"""本地模型（llama.cpp OpenAI 兼容端点）跑腿 B 链路的探针：量三件事，判"8B 能不能独自撑起腿 B"。

复用而不重造：prompt 用 `gen_legB.build_prompt`（刻意**不含 params 字典**，否则抹掉整族单位/率错型），
代码提取用 `gen_legB.extract_code`（能处理被截断的回答），判据用 `legB_grade.cells`
（里面同时走 `criteria.j1_analytic` 排队侧和 `inv_obs.j1_inv` 库存侧），τ 星用 `table_tau_v2.csv` 的**逐格**值，
判定预算 R=10 = τ 星的标定预算。

失败必须**分型归档**，不许混成一个"不行"：
  EMPTY      正文为空（thinking 没关掉时就是这个样子）
  TRUNCATED  finish_reason=length ⇒ 被 max_tokens 砍断。**这条不能无条件当成我的预算问题**：
             2026-10-17 我先把它写成"算我的预算设置，不算模型能力"，抬到 6000 token 复查才实测到
             原文是同一批 `total_*=0` 初始化行反复抄（790 行里只有 58 个唯一行）⇒ 属模型侧退化。
             归因必须由 probe_trunc_check.py 的重复度读数给出，不许由解释给出。
  SYNTAX     有代码但编译不过
  NO_JSON    能跑但没吐出一行契约 JSON / 语法过但没 print
  FIELD_GAP  吐出 JSON 但缺契约字段
  OK         以上都过 ⇒ 才进"参照可比率"的分母
每个任务都写日志（上一版只在成功时写 ⇒ 失败样本凭空消失，正是"产物条数要跟上游对账"那条）。

门槛（跑之前定死）：可编译率 ≥80%、字段齐全率 ≥60%、参照可比率 ≥10%；
且必须报 Wilson 上界 —— 3 个样本判不了任何事，所以默认跑 20 道。
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C                                    # noqa: E402
import gen_legB as G                                    # noqa: E402
import legB_grade as LG                                 # noqa: E402

BASE = os.environ.get('LLM_BASE', 'http://127.0.0.1:18081/v1')
MODEL = os.environ.get('LLM_MODEL', 'qwen3-8b')
OUT_DIR = os.path.join(HERE, 'legB_local_probe')
LOG = os.path.join(OUT_DIR, 'probe_log.jsonl')
SEEDS, HOR = LG.SEEDS, LG.HOR        # 与 τ* 标定预算一致，来源唯一（legB_grade）
MAXTOK = int(os.environ.get('LLM_MAXTOK', 3000))


def log(rec):
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def main(n_task=20):
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(LOG):
        os.remove(LOG)                       # 每次重跑都是全新账本，避免条数对不上
    TAU, by_id = LG.tau_map(), {}
    tasks = LG.pick_tasks(n_task)
    kinds = {k: 0 for k in ('OK', 'EMPTY', 'TRUNCATED', 'SYNTAX', 'NO_ENTRY', 'NO_JSON',
                            'FIELD_GAP', 'CRASH')}
    n_agree = n_uncmp = 0
    lines = ['# 本地 %s 跑腿 B 链路探针（%s，%d 道题，R=%d/40000）\n' % (MODEL, time.strftime('%m-%d %H:%M'), len(tasks), SEEDS)]
    t0 = time.time()
    for j, task in enumerate(tasks, 1):
        tid = task['task_id']
        by_id[tid] = task
        r = G.call_api(MODEL, G.build_prompt(task), MAXTOK, 'local', BASE, timeout=1200,
                       thinking='none', chat_kwargs={'enable_thinking': False})
        text = r.get('text') or ''
        code = G.extract_code(text)
        rec = {'n': j, 'task_id': tid, 'template': task['template'],
               'wall': round(r.get('wall', 0), 1), 'finish': r.get('finish'),
               'completion_tokens': (r.get('usage') or {}).get('completion_tokens'),
               'prompt_tokens': (r.get('usage') or {}).get('prompt_tokens'),
               'api_err': (r.get('err') or '').strip(), 'code_lines': len(code.splitlines())}
        kind = None
        if not code.strip():
            kind = 'EMPTY'
        elif r.get('finish') == 'length':
            kind = 'TRUNCATED'                 # 我的 max_tokens 不够，不能算模型不会写
        else:
            path = os.path.join(OUT_DIR, '%s__%s.py' % (tid, MODEL))
            io.open(path, 'w', encoding='utf-8').write(code)
            rec['path'] = os.path.basename(path)
            try:
                compile(code, path, 'exec')
            except SyntaxError as e:
                kind = 'SYNTAX'
                rec['syntax_err'] = str(e)[:120]
            if kind is None:
                # 判定只走 criteria.run_artifact 这一条出口：与腿 A 判参照件用的是同一个函数。
                # 今天这个 bug 的根源就是探针自己另拼了一遍命令行，于是"模型的错"和"我的传参格式"分不开。
                obs, dt_run, note = C.run_artifact(path, SEEDS, HOR, 'none', 1, timeout=420)
                rec['run_wall'] = round(dt_run, 1)
                rec['run_note'] = (note or '')[-300:]
                rec['has_entry'] = ('__main__' in code)
                rec['has_dump'] = ('json.dumps' in code)
                if obs is None:
                    # 分两类：连入口都没有 = 没写完就停；有入口有 dump 却没数 = 运行期没出来
                    kind = 'NO_ENTRY' if not rec['has_entry'] else 'NO_JSON'
                else:
                    miss = [k for k in G.required_fields(task, 'probe-grade') if k not in obs]
                    rec['missing_fields'] = miss
                    if miss:
                        kind = 'FIELD_GAP'
                    else:
                        kind = 'OK'
                        cells, n_in, n_tot = LG.cells(obs, task, TAU)
                        rec['agree'] = '%d/%d' % (n_in, n_tot)
                        rec['cells'] = cells
                        if n_tot == 0:
                            rec['note'] = '仪器不可比：该题没有带 τ* 的观测量可比（缺器官，不算失败）'
                            n_uncmp += 1
                        elif n_in == n_tot:
                            n_agree += 1
        kinds[kind] += 1
        rec['kind'] = kind
        log(rec)
        print('[%d/%d] %-14s %-10s 行=%3d tok=%5s %.0fs %s' % (
            j, len(tasks), tid, kind, rec['code_lines'], rec.get('completion_tokens'),
            r.get('wall', 0), rec.get('api_err', '')[:60]), flush=True)

    n = len(tasks)
    wil = lambda k, nn: (1.96 ** 2 / nn) / (1 + 1.96 ** 2 / nn) if nn else 1.0   # 0/n 的 Wilson 上界
    usable = kinds['OK']
    lines += ['', '## 分型计数（**每类都单列，不合并成"模型不行"**）', '',
              '| 类型 | 件数 | 含义 |', '|---|---|---|',
              '| OK | %d | 能跑、契约字段齐全、可进可比率分母 |' % kinds['OK'],
              '| EMPTY | %d | 正文为空（多为思考没关） |' % kinds['EMPTY'],
              '| TRUNCATED | %d | 被 max_tokens=%d 砍断。**不得自动当作我的预算问题**：'
              '抬到 6000 token 复查，mm1-01 仍 finish=length，且原文 790 个非空行里只有 58 个唯一行、'
              '单行最多重复 47 次 ⇒ 是模型退化重复，属模型侧失败；'
              '逐件读数见 probe_trunc_check.py 产出的 TRUNC_CHECK.md |'
              % (kinds['TRUNCATED'], MAXTOK),
              '| SYNTAX | %d | 有代码但编译不过 |' % kinds['SYNTAX'],
              '| NO_ENTRY | %d | 能编译但**只定义函数没有入口**（没写完就停，`has_entry=False`）|' % kinds['NO_ENTRY'],
              '| NO_JSON | %d | 有入口却拿不到一行契约 JSON（多为运行期崩/超时）|' % kinds['NO_JSON'],
              '| FIELD_GAP | %d | 吐了 JSON 但缺字段 |' % kinds['FIELD_GAP'],
              '| CRASH | %d | 运行超时/崩 |' % kinds['CRASH'], '',
              '## 三条门槛（跑前定死）\n',
              '- 可编译（语法过的全部：OK+FIELD_GAP+NO_JSON+NO_ENTRY+SYNTAX 之外）：**%d/%d**' % (
                  kinds['OK'] + kinds['FIELD_GAP'] + kinds['NO_JSON'] + kinds['NO_ENTRY'], n),
              '- 契约字段齐全（OK）：**%d/%d = %.0f%%**；若为 0，则 0/%d 的 Wilson 95%% 上界 = **%.0f%%**' % (
                  usable, n, 100.0 * usable / n, n, 100 * wil(usable, n) if usable == 0 else 0.0),
              '- 参照可比率（全部观测量都在逐格 τ* 内与闭式一致）：**%d/%d = %.0f%%**（门槛 ≥10%%）' % (
                  n_agree, max(usable - n_uncmp, 0),
                  100.0 * n_agree / (usable - n_uncmp) if usable > n_uncmp else 0.0),
              '- 其中**仪器比不了**（字段齐全但没有一个带 τ\\* 的观测量）：%d 件 ⇒ 已从分子分母同时剔除，'
              '不计为模型失败；真出现就说明判分出口缺器官（见 legB_grade.py 的说明）' % n_uncmp,
              '- 用时：%.1f 分钟（平均每道 %.0f 秒，含生成 + 判定运行）' % (
                  (time.time() - t0) / 60.0, (time.time() - t0) / max(1, n)), '',
              '⇒ **注意分母**：门槛是按"全部 %d 道"算的；如果把 TRUNCATED 剔出分母，'
              '可比率的分母会变成 %d，两个数都要报，不许只报好看的那个。' % (n, n - kinds['TRUNCATED'] - kinds['EMPTY'])]
    txt = '\n'.join(lines)
    io.open(os.path.join(OUT_DIR, 'PROBE.md'), 'w', encoding='utf-8').write(txt + '\n')
    print('\n' + txt)


if __name__ == '__main__':
    # argv 在**入口**解析并且要显式回显：以前写在模块顶层，别的脚本一 import 我，
    # 就把它自己的 argv 当题数吃下去（rejudge_existing.py 传目录名 ⇒ ValueError）。
    argv = sys.argv[1:]
    assert len(argv) <= 1, '用法：probe_local8b.py [题数]，多出来的参数 %s 会被静默忽略 ⇒ 停下' % argv[1:]
    n_task = int(argv[0]) if argv else 20        # 非数字当场 ValueError，不静默取默认
    print('[probe] 题数=%d max_tokens=%d 模型=%s base=%s 预算=R%d/%g' % (
        n_task, MAXTOK, MODEL, BASE, SEEDS, HOR), flush=True)
    main(n_task)
