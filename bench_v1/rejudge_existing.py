"""把**盘上已有的工件**用修好后的判定出口重新判一遍，不再花一分 API 钱。

为什么要这个文件：腿 B 的三条门槛（可编译 / 契约字段齐全 / 参照可比率）此前只有本地 8B 探针有读数，
而 `legB/` 里躺着 20 个已经花过钱的 deepseek-flash 工件。它们当初是用
`gen_legB.run_local`（`--horizon 4000.0` 这种字符串写法）跑的，那正是今天把"我的传参 bug"
误记成"模型写错"的那条出口。现在一律走 `criteria.run_artifact`，与腿 A 判参照件**同一个函数**。

必须写清楚的不干净之处（免得这版数字被当成干净的模型 A/B）：
  1. `legB/` 那 20 件是**旧 prompt** 生成的（prompt 里没有 CLI/入口约定那一段）⇒ 两轴混在一起；
  2. 它们的题面覆盖与本地探针的 20 题**不一定同一批**，脚本会显式报交集；
  3. 重判用的预算是 R=10/40000（与 τ* 同口径），与当初生成时 run_local 的 3/4000 不同 ⇒
     这是对**同一份代码**换判定口径，不是重跑生成。

2026-10-18 加的两件事，都只改"能不能中断、能不能看进度"，不改判据：
  · **逐件落盘 sidecar**（`--jsonl`，每条 append+flush）。原先汇总报告是**最后一次性写**，
    长链一旦被打断、或把 stdout 接进缓冲管道，就完全没有进度可读——
    18:56 那一跑就是这么瞎跑了 52 分钟（我的错在末尾接了 `2>&1 | tail -30`，不在脚本）。
  · **分片并行**（`--shard i/N`，按 `files[i::N]` 交错切，把 mh2 那类慢件摊到各片）：
    实测单件 ~45 秒、192 件单线程要 90 分钟，而本机 16 核只用了 1 个核。
  · 分片只决定"谁判哪件"。`timeout=420`、R=10/40000、`required_fields(task,'rejudge')` 一字不动；
    汇总由 `rejudge_merge.py` 调本文件的 `summarize()` ⇒ 判分与汇总各只有一份实现。

用法：
  ~/miniconda3/python.exe rejudge_existing.py <目录>                        # 整跑（老行为）
  ~/miniconda3/python.exe rejudge_existing.py <目录> --shard 0/4 --jsonl s0.tsvl
  ~/miniconda3/python.exe rejudge_existing.py <目录> --shard 0/4 --jsonl s0.tsvl --resume
汇总：~/miniconda3/python.exe rejudge_merge.py legB/_flash20261018_shard*.tsvl
"""
import argparse
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C                                    # noqa: E402
import gen_legB as G                                    # noqa: E402
import legB_grade as LG                                 # noqa: E402

SEEDS, HOR = LG.SEEDS, LG.HOR
OUT_TMPL = os.path.join(HERE, '_rejudge_%s.txt')
KINDS = ('OK', 'SYNTAX', 'NO_ENTRY', 'NO_JSON', 'FIELD_GAP', 'CRASH', 'SKIP_NOTID')


def artifacts(d):
    return sorted(f for f in os.listdir(d) if f.endswith('.py') and '__REF' not in f)


def judge_one(f, d, by_id, TAU, probe_ids):
    """逐件的**唯一**判定出口。整跑与分片共用它，不许出现第二份实现。"""
    tid = f.split('__')[0]
    task = by_id.get(tid)
    if task is None:
        return {'file': f, 'task_id': tid, 'kind': 'SKIP_NOTID', 'has_obs': False}
    path = os.path.join(d, f)
    code = io.open(path, encoding='utf-8').read()
    rec = {'file': f, 'task_id': tid, 'template': task['template'],
           'in_probe_set': tid in probe_ids, 'code_lines': len(code.splitlines()),
           'has_obs': False, 'n_in': 0, 'n_tot': 0}
    kind = None
    obs = None
    try:
        compile(code, path, 'exec')
    except SyntaxError as e:
        kind, rec['syntax_err'] = 'SYNTAX', str(e)[:120]
    if kind is None:
        t0 = time.time()
        obs, dt, note = C.run_artifact(path, SEEDS, HOR, 'none', 1, timeout=420)
        rec['run_wall'] = round(dt, 1)
        rec['run_note'] = (note or '')[-260:]
        # 入口判据：'main()' 这种子串会被 `def main():` 命中（同名两义的老毛病），
        # 所以只认 `if __name__` 或**顶格**的 main() 调用。
        rec['has_entry'] = ('__main__' in code) or bool(re.search(r'^main\(\)', code, re.M))
        if obs is None:
            kind = 'NO_ENTRY' if not rec['has_entry'] else 'CRASH'
        else:
            miss = [k for k in G.required_fields(task, 'rejudge') if k not in obs]
            rec['missing_fields'] = miss
            kind = 'FIELD_GAP' if miss else 'OK'
    # 只要吐出了 JSON 就比：**逐观测量**计分，而不是把"缺任一字段"的工件整个丢掉。
    # 理由：FIELD_GAP 的工件往往 W/L 报得对、只是没报 busy_frac；整件丢弃会把可用的信号扔掉，
    # 而"件级全一致"这个统计量会因此虚低。腿 A 用 strict/measurable/NA 三分母，这里同口径：
    #   件级可比率（该件所有可比观测量都一致）＋ 格级一致率（可比观测量里一致的比例）。
    if obs is not None:
        rows_txt, n_in, n_tot = LG.cells(obs, task, TAU)
        rec['has_obs'] = True
        rec['agree'] = '%d/%d' % (n_in, n_tot)
        rec['n_in'], rec['n_tot'] = n_in, n_tot
        rec['cells'] = rows_txt
    rec['kind'] = kind
    return rec


def summarize(recs, title, note=''):
    """门槛与分母**全部从逐件记录现算**（分母不许挂常量）。"""
    n = len(recs)
    kinds = {k: 0 for k in KINDS}
    for r in recs:
        kinds[r['kind']] += 1
    skip = kinds['SKIP_NOTID']
    compiled = n - kinds['SYNTAX'] - skip
    n_ok = kinds['OK']
    withobs = [r for r in recs if r.get('has_obs')]
    unc = [r for r in withobs if r['n_tot'] == 0]
    cmpf = [r for r in withobs if r['n_tot'] > 0]
    agree = [r for r in cmpf if r['n_in'] == r['n_tot']]
    n_cells_tot = sum(r['n_tot'] for r in withobs)
    n_cells_in = sum(r['n_in'] for r in withobs)
    n_probe = sum(1 for r in recs if r.get('in_probe_set'))
    slow = sorted((r for r in recs if r.get('run_wall')), key=lambda r: -r['run_wall'])[:5]
    wil = lambda k, nn: (1.96 ** 2 / nn) / (1 + 1.96 ** 2 / nn) if nn else 1.0
    pc = lambda a, b: 100.0 * a / b if b else 0.0
    lines = ['# 盘上工件回判（%s，出口=criteria.run_artifact，R=%d/%g）' % (title, SEEDS, HOR), '']
    if note:
        lines += [note, '']
    lines += ['读入 **%d 件**（题号在题集里找不到而跳过 %d 件）' % (n, skip), '',
              '## 分型', '']
    for k, v in sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append('- %s: %d' % (k, v))
    lines += ['', '## 门槛与分母（一次报全，不许只报好看的那个）', '',
              '- 可编译：%d/%d = %.1f%%（门槛 ≥80%%）' % (compiled, n, pc(compiled, n)),
              '- 契约字段齐全（required 全中）：%d/%d = %.1f%%（门槛 ≥60%%）' % (n_ok, n, pc(n_ok, n)),
              '- 吐出了 JSON（能进比对）：%d/%d' % (len(withobs), n),
              '- 其中**仪器比不了**（一个带 τ 星的观测量都没有）：%d 件 ⇒ 从分子分母同时剔除，不计为失败'
              % len(unc),
              '- 件级可比率（该件可比观测量**全部**一致 / 可比件数）：%d/%d = %.1f%%；若为 0 则 Wilson 上界 %.1f%%'
              % (len(agree), len(cmpf), pc(len(agree), len(cmpf)),
                 100 * wil(0, max(len(cmpf), 1))),
              '- **格级一致率**（可比观测量里一致的比例，主统计量）：%d/%d = %.1f%%（门槛 ≥10%%）' % (
                  n_cells_in, n_cells_tot, pc(n_cells_in, n_cells_tot)),
              '- 与本地探针 20 题的交集：%d/%d' % (n_probe, n),
              '', '## 最慢 5 件（超时件要单列，不能混进"模型写错"）', '']
    for r in slow:
        lines.append('- %s run_wall=%ss kind=%s' % (r['file'], r.get('run_wall'), r['kind']))
    lines += ['', '## 逐件（cells 全表只在 sidecar，正文不落）', '']
    for r in recs:
        lines.append(json.dumps({k: v for k, v in r.items() if k != 'cells'},
                                ensure_ascii=False))
    return lines


def load_sidecar(p):
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def load_sidecars(paths):
    """并片。重复键直接炸——分片切重或 sidecar 被写两遍时，宁可停下也不能出双计的分母。"""
    recs, seen = [], {}
    for p in paths:
        for r in load_sidecar(p):
            k = r['file']
            if k in seen:
                raise AssertionError('重复键 %s（%s 与 %s）⇒ 分片切重了或 sidecar 被写过两遍'
                                     % (k, seen[k], p))
            seen[k] = p
            recs.append(r)
    recs.sort(key=lambda r: r['file'])
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir', nargs='?', default=os.path.join(HERE, 'legB'))
    ap.add_argument('suffix', nargs='?', default=None)   # 兼容老 CLI，本脚本不用它
    ap.add_argument('--shard', default=None, help='i/N，按 files[i::N] 交错切')
    ap.add_argument('--jsonl', default=None, help='逐件 sidecar（append+flush）')
    ap.add_argument('--resume', action='store_true', help='sidecar 里已有的 file 直接跳过')
    ap.add_argument('--report', default=None, help='汇总落盘路径；分片且未给则不写汇总')
    a = ap.parse_args()

    d = a.dir if os.path.isabs(a.dir) else os.path.join(HERE, a.dir)
    files = artifacts(d)
    if a.shard:
        i, N = (int(x) for x in a.shard.split('/'))
        assert 0 <= i < N, 'bad --shard %s' % a.shard
        files = files[i::N]
        print('[rejudge] shard=%s 本片 %d 件' % (a.shard, len(files)), flush=True)
    by_id = {t['task_id']: t for t in C.load_tasks()}
    TAU = LG.tau_map()
    probe_ids = {t['task_id'] for t in LG.pick_tasks(20)}

    done = set()
    if a.jsonl and a.resume:
        done = {r['file'] for r in load_sidecar(a.jsonl)}
        print('[rejudge] resume：sidecar 已有 %d 件，跳过' % len(done), flush=True)
    if a.jsonl:
        jd = os.path.dirname(os.path.abspath(a.jsonl))
        if not os.path.isdir(jd):
            os.makedirs(jd, exist_ok=True)
    side = io.open(a.jsonl, 'a', encoding='utf-8') if a.jsonl else None

    recs = []
    try:
        for idx, f in enumerate(files, 1):
            if f in done:
                continue
            rec = judge_one(f, d, by_id, TAU, probe_ids)
            recs.append(rec)
            if side:
                side.write(json.dumps(rec, ensure_ascii=False) + '\n')
                side.flush()          # 逐件 flush：杀进程/断链也不丢已判的
            print('[%d/%d] %-26s %-9s %s' % (idx, len(files), f, rec['kind'],
                                             rec.get('agree', '')), flush=True)
    finally:
        if side:
            side.close()

    if a.shard and not a.report:
        print('[rejudge] 分片不写汇总（交给 rejudge_merge.py）', flush=True)
        return
    out = a.report or OUT_TMPL % re.sub(r'\W+', '_', os.path.basename(d.rstrip('\\/')))
    io.open(out, 'w', encoding='utf-8').write(
        '\n'.join(summarize(recs, os.path.basename(d.rstrip('\\/')))) + '\n')
    print('\n写在 %s' % out, flush=True)


if __name__ == '__main__':
    main()
