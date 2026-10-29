"""腿 B 生成端：题面 -> LLM 写仿真工件 -> 落盘 -> 交给判分端。

纪律（都是今天夜里定死的，别绕过）：
1. **默认不花钱**。必须同时给 --spend 且环境变量 LEGB_SPEND=yes 才真发请求；
   否则只走 --mock：把 prompt 全部渲染落盘，用参照工件当"假答案"走通下游统计链路。
2. prompt 里索要的字段 = **该题参照件实际报出的键**（`field_contract.csv`，逐题），不是全局清单。
   理由：参照件报这些字段，若 LLM 工件只报 W/L，J2/J3 会在 LLM 侧白送通过率＝假公平；
   但反过来向 eoq/newsvendor 索要 W、p_wait 会把**正确**的工件判成缺字段（今天就是这么把 5 件
   库存题工件挡在"参照可比率"分母之外的），所以清单必须由参照件自己生成。
3. prompt 里**禁止**出现任何闭式真值数值（那等于把答案给它）。真值只进判分端。
4. 每次调用的 usage(prompt/completion tokens) 逐条落盘，花钱前先拿实测数报价。
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402
import legB_grade as LG  # noqa: E402

OUT_DIR = os.path.join(HERE, 'legB')
ENV_FILE = os.path.join(HERE, 'deepseek.env')

SYS_PROMPT = (
    '你是离散事件仿真工程师。只输出一段可运行的 Python，不解释、不写注释、不写思考过程。'
    '硬长度约束：全文不超过 120 行；不要定义类、不要分阶段重构，写成一个 main() 即可。'
    '要求：(1) 用标准库实现题面描述的随机模型（不要用第三方库）；'
    '(2) 服务时长必须在顾客到达时抽好并挂在该顾客身上，不得在开始服务那一刻才抽；'
    '(3) 统计量只在去掉前 25% 预热后的窗口内累计，面积型量必须在改变状态之前积分；'
    '(4) 程序接受命令行 --seeds N --horizon H --seed-start S --pert NAME，'
    'NAME 取 none/lam_up/mu_up/c_up，扰动只改参数不改结构；'
    '(5) stdout 恰好输出一行 JSON（用 print(json.dumps(...)) 一次性打印，不要缩进、不要多行），'
    '键必须包含题面"输出要求"列出的全部字段，其中 per_seed_* 数组的长度必须等于实际种子数。'
)

# 字段契约的**唯一来源**在 legB_grade（逐题：该题参照件报了哪些键 × 该题哪些观测量标了 τ 星）。
# 这里过去写死过一个全局 FIELDS 清单（time_unit/arr/dep/blk/... /p_loss/p_wait/busy_frac），
# 那对排队模板成立、对 eoq/newsvendor 不成立（参照件只报 7-8 个键），
# 于是正确只报 q/cost 的工件被判 FIELD_GAP、还被挡出"参照可比率"分母——见预注册 §17 的 AE。
# 全局清单已删；如需再引用，一律走 contract_fields()。


def contract_fields(task, why='prompt'):
    """转给 legB_grade：判"缺字段"和"能比哪些观测量"必须是同一个来源，不许两头各写一份。"""
    return LG.contract_fields(task, why)


def required_fields(task, why='prompt'):
    return LG.required_fields(task, why)



def load_key():
    env = {}
    if os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k] = v
    return env.get('DEEPSEEK_API_KEY', ''), env.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')


def build_prompt(task):
    req, opt = contract_fields(task, 'prompt')
    want = sorted(set(req) | set(opt))
    body = task.get('desc_zh') or task.get('desc_en') or ''
    # ⚠ 刻意**不**把 params 字典放进 prompt：题面里写的是"平均 6 分钟"这种自然语言，
    #    把 μ=10/小时 直接喂给模型就等于抹掉一整族错型（rate_units 的 service_per_minute、
    #    lam_mu_swap、time_base 的 scale60 全靠"单位换算这一步归模型"才存在）。
    #    真值 truth_print 更是绝不进 prompt（那是给它答案）。
    # ⚠ want 也刻意**不再**并全局 FIELDS：向库存题（eoq/newsvendor）索要 W/p_wait 会把正确的
    #    工件判成缺字段，并把它们挡在"参照可比率"分母之外（2026-10-17 实测栽过一次）。
    gloss = []
    if 'W' in want or 'L' in want:
        gloss.append(u'W 的单位是分钟，L 无量纲，概率量取 0-1；')
    # 忙度必须把**定义**写给模型：`busy_frac` 这一个名字在腿 A 里背过两种口径
    # （每台利用率 E[min(N,c)]/c 与 站不空比例 1−π₀，c>1 时相差 44–68%）。
    # 只写"车道忙度/lane utilisation"就等于让一个写对了每台利用率的正确模型，
    # 在 mmcK 上挨 9–68% 的 rel —— 那是我在造假阳（外部审计 P-05）。
    ct = task.get('output_contract') or {}
    if 'busy_frac' in want and ct.get('busy_frac'):
        gloss.append(u'busy_frac 的定义：题目契约已点名 = %s；'
                     u'请另报 busy_util=E[min(N,c)]/c 与 busy_occupied=1−π₀ 两个具名量，'
                     u'不要把二者混成一个数；' % ct['busy_frac'])
    if 'time_unit' in want:
        gloss.append(u'time_unit 填你程序内部时间轴的单位（hour/minute/second 之一）；')
    for f, g in (('arr', u'arr 是统计窗口内平均每种子的人数计数'),
                 ('dep', u'dep 是窗口内平均每种子的离开人数'),
                 ('blk', u'blk 是窗口内平均每种子被拒绝/丢失的人数'),
                 ('dep_rate', u'dep_rate 是"个/每小时"的有效离开率'),
                 ('win', u'win 是统计窗口长度（与 time_unit 同单位）')):
        if f in want:
            gloss.append(g + u'；')
    per_seed = sorted(f for f in want if f.startswith('per_seed_'))
    if per_seed:
        gloss.append(u'%s 是逐种子的单独估计值，长度必须等于 seeds_used；' % u'/'.join(per_seed))
    if 'seed_list' in want:
        gloss.append(u'seed_list 列出实际用过的种子号。')
    return (u'题面（任务号 %s）：\n%s\n\n'
            u'输出要求：stdout 恰好输出一行 JSON（用 print(json.dumps(...)) 一次打印，不要缩进多行），'
            u'键必须包含：%s。\n'
            u'另外建议一并报出：%s —— 这些用来核对流量/忙度恒等式，缺了对应判据只能记"不可比"，不算通过。\n'
            u'口径约定：%s\n'
            # ↓ 命令行接口与入口要求：这是**接口约定**，不含任何答案（不给参数值、不给真值），
            #   所以不会抹掉单位/率那几族错型；不写它的话，模型按 int() 解析 --horizon 就会被我判死，
            #   而"只定义函数、没有入口"也会被算成"模型写不出来"——两类都是测量假象。
            u'命令行接口（必须照此实现）：评测程序会调用 '
            u'`python 你的文件.py --seeds N --horizon H --seed-start S --pert none`；'
            u'H 是整数样式的仿真时域长度，单位与你自报的 time_unit 一致，'
            u'解析时请写成 `float(...)`（或两种都吃），不要假设它一定是整数；'
            u'不带任何参数时也必须能用默认值跑完并打印那一行 JSON；'
            u'程序必须有入口（例如 `if __name__ == "__main__": main()`），'
            u'不要只定义函数。'
            u'每个种子用独立的随机流，seeds_used 填实际跑完的种子数。\n'
            % (task['task_id'], body, ', '.join(req), ', '.join(opt) or '（无）', u' '.join(gloss)))


def call_api(model, prompt, max_tokens, key, base, timeout=300, thinking='disabled', chat_kwargs=None):
    """thinking 档位实测（2026-10-17，_ds_thinking.txt + 本地 llama.cpp 四开关对照）：
         DeepSeek：默认=开。`thinking:{'type':'disabled'}` 与 `reasoning_effort:'low'` 有效；
           `disable_thinking:true` 被**静默忽略**（正文空、HTTP 仍 200）。
         本地 llama.cpp + Qwen3-8B（llama-server -ngl 99）：只有
           `chat_template_kwargs:{'enable_thinking':false}` 有效（content=4604 字、reasoning=0、finish=stop、
           45 token/s）；`thinking:{type:disabled}` 与 `{thinking:false}` 都**静默失效**
           ——正文 0 字、reasoning_content 2651 字、finish=length，把 max_tokens 全烧在思考上。
       ⇒ 两条教训：① 开关要按后端传，不能假设某个通用字段名管用；
          ② usage 里**不一定有** reasoning_tokens（llama.cpp 就没有），
             所以"档位生效"的断言必须同时看 `content` 是否为空与 `reasoning_content` 长度，
             只看 reasoning_tokens 会静默放过整批空正文。"""
    payload = {'model': model,
               'messages': [{'role': 'system', 'content': SYS_PROMPT},
                            {'role': 'user', 'content': prompt}],
               'temperature': 0.0, 'max_tokens': max_tokens}
    if thinking == 'disabled':
        payload['thinking'] = {'type': 'disabled'}
    elif thinking == 'enabled':
        payload['thinking'] = {'type': 'enabled'}
    if chat_kwargs:
        payload['chat_template_kwargs'] = dict(chat_kwargs)
    r = urllib.request.Request(base.rstrip('/') + '/chat/completions',
                               data=json.dumps(payload).encode('utf-8'), method='POST')
    r.add_header('Authorization', 'Bearer ' + key)
    r.add_header('Content-Type', 'application/json')
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            j = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'err': 'HTTP %s %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]),
                'wall': time.time() - t0}
    except Exception as e:
        return {'err': '%s: %s' % (type(e).__name__, e), 'wall': time.time() - t0}
    ch = (j.get('choices') or [{}])[0]
    usage = j.get('usage') or {}
    rt = ((usage.get('completion_tokens_details') or {}).get('reasoning_tokens')) or 0
    out = {'text': (ch.get('message') or {}).get('content') or '',
           'reasoning_len': len((ch.get('message') or {}).get('reasoning_content') or ''),
           'reasoning_tokens': rt,
           'usage': j.get('usage'), 'wall': time.time() - t0, 'finish': ch.get('finish_reason')}
    want_off = (thinking == 'disabled')
    if want_off and (rt > 0 or out['reasoning_len'] > 0 or not out['text'].strip()):
        # 三种形态都要抓：报了 reasoning_tokens 的（DeepSeek）、只回 reasoning_content 的（llama.cpp）、
        # 以及正文干脆为空的（两边都会静默给 200）
        out['err'] = (out.get('err') or '') + (
            ' THINKING_NOT_OFF reasoning_tokens=%d reasoning_content=%dB content=%dB'
            % (rt, out['reasoning_len'], len(out['text'])))
    if out['finish'] == 'length':
        # 截断的工件会语法错->跑崩->被记成"检出"，这会系统性高估检出率，必须单独归档
        out['err'] = (out.get('err') or '') + ' TRUNCATED(finish=length)'
    return out


def extract_code(text):
    """取代码块，**必须处理被截断的回答**。

    上一版只在找到闭合围栏时才剥壳；max_tokens 用尽时根本没有闭合标记，
    于是带 ```python 的原文被当代码落盘 -> SyntaxError -> 记成"模型写错了"。
    那是我的解析 bug，不是模型能力。现在：无闭合就把围栏之后全取；
    调用方另按 finish_reason=='length' 单独归档，绝不混进能力统计。
    """
    i = text.find('```')
    if i < 0:
        return text.strip()
    j = text.find('\n', i)
    if j < 0:
        return ''
    body = text[j + 1:]
    k = body.find('```')
    return (body[:k] if k >= 0 else body).strip()


def run_local(path, seeds=3, horizon=4000.0, timeout=300):
    """`timeout` 10-18 才加进来：批量生成器里这次运行只是**预览**（只为拿 obs 的键名/缺字段），
    权威读数由 `rejudge_existing.py` 走 `criteria.run_artifact(timeout=420)` 重跑给出。
    写死 300 s 的后果实测过：一个死循环工件能把整条批的墙钟拖 5 分钟/件，而显卡在那 5 分钟里是 0%。
    """
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        p = subprocess.run([sys.executable, path, '--seeds', str(seeds), '--horizon', str(horizon),
                            '--seed-start', '1', '--pert', 'none'],
                           capture_output=True, text=True, timeout=timeout,
                           encoding='utf-8', errors='replace', env=env)
    except Exception as e:
        return 'EXC %s' % e, None
    if p.returncode != 0:
        return 'rc=%s %s' % (p.returncode, (p.stderr or '')[-200:]), None
    obs, note = C.parse_artifact_line(p.stdout or '')
    return note, obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mock', action='store_true')
    ap.add_argument('--spend', action='store_true')
    ap.add_argument('--model', default='deepseek-flash')
    ap.add_argument('--limit', type=int, default=2)
    ap.add_argument('--max-tokens', type=int, default=4000)
    ap.add_argument('--thinking', default='disabled', choices=('disabled', 'enabled'))
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    tasks = C.load_tasks()[:a.limit]
    key, base = load_key()
    real = a.spend and os.environ.get('LEGB_SPEND') == 'yes' and bool(key)
    log = open(os.path.join(OUT_DIR, 'legB_%s.jsonl' % ('mock' if not real else a.model)),
               'a', encoding='utf-8')
    print('[legB] real_api=%s model=%s tasks=%d' % (real, a.model, len(tasks)), flush=True)
    for t in tasks:
        prompt = build_prompt(t)
        rec = {'task_id': t['task_id'], 'template': t['template'],
               'prompt_chars': len(prompt), 'mock': not real}
        if real:
            r = call_api(a.model, prompt, a.max_tokens, key, base, thinking=a.thinking)
            code = extract_code(r.get('text') or '')
            rec.update({'usage': r.get('usage'), 'wall': r.get('wall'),
                        'err': r.get('err'), 'finish': r.get('finish'),
                        'thinking': a.thinking,
                        'reasoning_tokens': r.get('reasoning_tokens'),
                        'truncated': (r.get('finish') == 'length'),
                        'raw_chars': len(r.get('text') or ''),
                        'code_chars': len(code)})
            code = extract_code(r.get('text') or '')
            try:
                compile(code, '<gen>', 'exec')
                rec['syntax'] = 'ok'
            except SyntaxError as e:
                rec['syntax'] = 'SyntaxError@%s' % e.lineno      # 截断的典型后果，单独归档
            cp = os.path.join(OUT_DIR, '%s__%s.py' % (t['task_id'], a.model.replace('.', '_')))
            with open(cp, 'w', encoding='utf-8', newline='') as f:
                f.write(code + '\n')
            note, obs = run_local(cp)
            rec['run_note'] = str(note)[:200]
            rec['obs_keys'] = sorted(obs.keys()) if obs else None
        else:
            # mock：拿参照件当"假答案"，只验下游链路（落盘->跑->解析字段）是否通
            ref = os.path.join(HERE, 'artifacts', '%s__REF.py' % t['task_id'])
            note, obs = run_local(ref) if os.path.exists(ref) else ('no_ref', None)
            rec['run_note'] = str(note)[:200]
            rec['obs_keys'] = sorted(obs.keys()) if obs else None
            rec['missing_fields'] = [f for f in required_fields(t, 'grade')
                                     if f not in (obs or {})]
        log.write(json.dumps(rec, ensure_ascii=False) + '\n')
        log.flush()
        print('[legB] %s prompt_chars=%s run_note=%s missing=%s'
              % (t['task_id'], rec['prompt_chars'], rec['run_note'],
                 rec.get('missing_fields')), flush=True)
    log.close()


if __name__ == '__main__':
    main()
