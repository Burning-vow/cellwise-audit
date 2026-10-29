# -*- coding: utf-8 -*-
"""P5 外部题：REF 对账 + 77 件代表错型矩阵。

用法：
  python run_external.py ref              # 12 道 REF × 20 种子 × 40000，对独立真值
  python run_external.py matrix [i/n]     # 77 件注入件 × 10 种子 × 40000

外部题不进主表、不参与 tau* 标定；这里只是用同一套判据与已标定 tau*
检查 P1–P4 的四条边界能否在教材参数上复现。
"""
import csv
import glob
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.abspath(os.path.join(HERE, '..', '..'))
ROOT = os.path.dirname(BENCH)
if BENCH not in sys.path:
    sys.path.insert(0, BENCH)
import criteria as C  # noqa: E402
from inv_obs import j1_inv  # noqa: E402

TASKS = os.path.join(HERE, 'external_tasks.jsonl')
REFS = os.path.join(HERE, 'external_refs.jsonl')
MUTS = os.path.join(HERE, 'external_mutants.jsonl')
REF_CSV = os.path.join(HERE, 'EXTERNAL_REF_CHECK.csv')
MAT_CSV = os.environ.get('EXT_MAT_CSV') or os.path.join(HERE, 'EXTERNAL_MATRIX.csv')
if not os.environ.get('EXT_MAT_CSV'):
    # 2026-10-21 踩过的坑：不设 EXT_MAT_CSV 直接跑 matrix，会另开一个 EXTERNAL_MATRIX.csv
    # 并把**全部**变异件重跑一遍（done 集合只来自这一个文件，看不见 shard1-4 的 77 行）。
    # 结果盘上同时存在"分片版"和"整表版"两份矩阵，任何 glob 写宽一点就双计。
    # 要故意重建整表，就显式设 EXT_ALLOW_WHOLE=1 —— 光靠"文件已存在"当条件是没用的，
    # 那样第一次跑完之后这道闸就永远不响了。
    _shards = [f for f in os.listdir(HERE)
               if f.startswith('EXTERNAL_MATRIX.shard') and f.endswith('.csv')
               and '.triggers.' not in f]
    if _shards and os.environ.get('EXT_ALLOW_WHOLE') != '1':
        raise SystemExit(
            '拒绝写整表 %s：盘上已有 %d 个分片（%s ...）。'
            '补跑请设 EXT_MAT_CSV 指向明确的新分片；确实要重建整表请设 EXT_ALLOW_WHOLE=1。'
            % (os.path.basename(MAT_CSV), len(_shards), ','.join(sorted(_shards)[:3])))
SUMMARY = os.path.join(HERE, 'EXTERNAL_SUMMARY.md')
ART = os.path.join(BENCH, 'artifacts_external')
TAU_PATH = os.path.join(BENCH, 'table_tau_v2.csv')

REF_N = 10
MUT_N = 10
HOR = 40000.0
REF_TOL = 0.03       # 排队量 20 种子的复算容差；库存量另用 1%
INV_TOL = 0.01


def load_tasks():
    return {json.loads(l)['task_id']: json.loads(l)
            for l in open(TASKS, encoding='utf-8') if l.strip()}


def load_tau():
    out = {}
    for r in csv.DictReader(open(TAU_PATH, encoding='utf-8')):
        if r.get('tau_star') not in ('', 'NONE', None):
            out[(r['criterion'], r['statistic'], r['template'])] = float(r['tau_star'])
    return out


def fmt_rel(x):
    if x is None:
        return ''
    return '%.6g' % x


def check_ref():
    tasks = load_tasks()
    refs = [json.loads(l) for l in open(REFS, encoding='utf-8') if l.strip()]
    rows = []
    bad = []
    t0 = time.time()
    print('[ext-ref] %d tasks, R=%d H=%g' % (len(refs), REF_N, HOR), flush=True)
    for i, r in enumerate(refs, 1):
        tid = r['task_id']
        task = tasks[tid]
        path = os.path.join(ROOT, r['artifact_path'].replace('/', os.sep))
        obs, dt, note = C.run_artifact(path, REF_N, HOR, 'none', 1, timeout=1200)
        if obs is None:
            rows.append([tid, task['template'], 'CRASH', '', '', '', note])
            bad.append((tid, 'CRASH', note))
            print('[ext-ref] ! %s CRASH %s' % (tid, note[-120:]), flush=True)
            continue
        rels = {}
        if task['kind'] == 'queue':
            for o, d in C.j1_analytic(obs, task, tau=None)['per_obs'].items():
                if d.get('truth') is None:
                    continue          # 本题没有该观测量真值，不是 REF 失败
                rels[o] = d.get('rel')
        else:
            for o, d in j1_inv(obs, task).items():
                rels[o] = d.get('rel')
        mx = None
        fails = []
        for o, rel in rels.items():
            if rel is None:
                fails.append('%s:MISS' % o)
                continue
            mx = rel if mx is None else max(mx, rel)
            tol = INV_TOL if task['kind'] == 'inventory' else REF_TOL
            if rel > tol:
                fails.append('%s:%.5f>%.3f' % (o, rel, tol))
        verdict = 'PASS' if not fails else 'FAIL'
        if fails:
            bad.append((tid, verdict, '; '.join(fails)))
        rows.append([tid, task['template'], verdict, fmt_rel(mx), len(rels),
                     '; '.join(fails), '%.1fs' % dt])
        print('[ext-ref] %d/%d %s %s max=%s %s'
              % (i, len(refs), tid, verdict, fmt_rel(mx), '; '.join(fails)[:100]), flush=True)
    with open(REF_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['task_id', 'template', 'verdict', 'max_rel', 'n_obs', 'failures', 'wall'])
        w.writerows(rows)
    print('[ext-ref] done %.1fs bad=%d -> %s' % (time.time() - t0, len(bad), REF_CSV), flush=True)
    return bad


def _counter_text(obs):
    ks = ('trig_nonhead', 'trig_preempt', 'trig_class0', 'trig_transfer',
          'trig_swap_noop', 'trig_leak', 'trig_fieldconst', 'trig_backsolve')
    return ','.join('%s=%s' % (k.replace('trig_', ''), obs.get(k)) for k in ks)


def judge(obs, task, tau):
    cells = []

    def add(cn, stat, d):
        rel = d.get('rel')
        if rel is None:
            cells.append(dict(cn=cn, stat=stat, rel=None, status=d.get('status', 'missing'),
                              tau=None, fired=None))
            return
        key = (cn, stat, task['template'])
        t = tau.get(key)
        if t is None:
            cells.append(dict(cn=cn, stat=stat, rel=rel, status='NO_TAU', tau=None, fired=None))
            return
        cells.append(dict(cn=cn, stat=stat, rel=rel, status='ok', tau=t,
                          fired=bool(rel > t)))

    for o, d in C.j1_analytic(obs, task, tau=None)['per_obs'].items():
        add('J1', o, d)
    for o, d in j1_inv(obs, task).items():
        add('J1', o, d)
    for cn, fn in (('J2', C.j2_conservation), ('J3', C.j3_pairing)):
        for k, d in (fn(obs, task, tau=None).get('per_stat') or {}).items():
            add(cn, k, d)
    judged = [c for c in cells if c['status'] == 'ok']
    fired = [c for c in judged if c['fired']]
    no_tau = [c for c in cells if c['status'] == 'NO_TAU']
    if not judged:
        verdict = 'NO_JUDGED'
    elif fired:
        verdict = 'DETECTED'
    else:
        verdict = 'NOT_DETECTED'
    return dict(verdict=verdict, judged=len(judged), fired_n=len(fired),
                fired_cells='; '.join('%s/%s rel=%.4g>tau=%.3g' % (c['cn'], c['stat'], c['rel'], c['tau'])
                                      for c in fired)[:300],
                no_tau='; '.join('%s/%s' % (c['cn'], c['stat']) for c in no_tau)[:200],
                fired_obs=','.join(sorted({c['stat'] for c in fired if c['cn'] == 'J1'})),
                counters=_counter_text(obs), cells=cells)


def evaluate(m, task, tau):
    path = os.path.join(ROOT, m['artifact_path'].replace('/', os.sep))
    if not os.path.exists(path):
        return dict(verdict='MISSING', judged=0, fired_n=0, fired_cells='',
                    no_tau='', fired_obs='', counters='', cells=[])
    obs, dt, note = C.run_artifact(path, MUT_N, HOR, 'none', 1, timeout=1200)
    if obs is None:
        return dict(verdict='CRASH', judged=0, fired_n=0, fired_cells='',
                    no_tau='', fired_obs='', counters='', cells=[], note=str(note)[-200:])
    d = judge(obs, task, tau)
    d['note'] = ''
    return d


def _match(boundary, d):
    if boundary == 'static':
        if d['verdict'] == 'NOT_DETECTED':
            return 'MATCH'
        if d['verdict'] == 'NO_JUDGED':
            return 'NA'
        if d['verdict'] in ('CRASH', 'MISSING'):
            return d['verdict']
        return 'MISMATCH'
    if boundary == 'point':
        if d['verdict'] == 'DETECTED':
            return 'MATCH'
        if d['verdict'] in ('CRASH', 'MISSING'):
            return d['verdict']
        return 'MISMATCH'
    if boundary == 'weak':
        # P3：均值量应基本不动，p_loss（计数一阶）应动。
        obs = set(x for x in (d.get('fired_obs') or '').split(',') if x)
        if 'p_loss' in obs and not ({'W', 'L'} & obs):
            return 'MATCH_WEAK'
        if {'W', 'L'} & obs:
            return 'OVER_DETECTED'
        return 'NOT_DETECTED'
    return 'OPEN'


def matrix(shard=1, nshard=1):
    tasks = load_tasks()
    tau = load_tau()
    muts = [json.loads(l) for l in open(MUTS, encoding='utf-8') if l.strip()]
    muts = muts[(shard - 1)::nshard]
    done = set()
    if os.path.exists(MAT_CSV):
        for r in csv.DictReader(open(MAT_CSV, encoding='utf-8')):
            done.add((r['task_id'], r['error_type'], r['seeds'], r['horizon']))
    new = not os.path.exists(MAT_CSV)
    fh = open(MAT_CSV, 'a', newline='', encoding='utf-8')
    w = csv.writer(fh)
    if new:
        w.writerow(['task_id', 'template', 'error_type', 'expected', 'p5_boundary',
                    'verdict', 'judged', 'fired_n', 'fired_obs', 'fired_cells',
                    'no_tau', 'counters', 'seeds', 'horizon', 'match', 'note'])
        fh.flush()
    todo = [m for m in muts if (m['task_id'], m['error_type'], str(MUT_N), str(HOR)) not in done]
    t0 = time.time()
    print('[ext-mat] shard %d/%d todo=%d' % (shard, nshard, len(todo)), flush=True)
    for i, m in enumerate(todo, 1):
        tid, et = m['task_id'], m['error_type']
        d = evaluate(m, tasks[tid], tau)
        mt = _match(m.get('p5_boundary', 'open'), d)
        w.writerow([tid, m['template'], et, m['expected'], m.get('p5_boundary', ''),
                    d['verdict'], d['judged'], d['fired_n'], d['fired_obs'],
                    d['fired_cells'], d['no_tau'], d['counters'],
                    MUT_N, HOR, mt, d.get('note', '')])
        fh.flush()
        if i % 5 == 0 or i == 1:
            print('[ext-mat] %d/%d %s__%s %s %s fired=%d %.0fs'
                  % (i, len(todo), tid, et, d['verdict'], mt, d['fired_n'],
                     time.time() - t0), flush=True)
    fh.close()
    print('[ext-mat] shard %d/%d done -> %s' % (shard, nshard, MAT_CSV), flush=True)


def summarize():
    files = sorted(glob.glob(os.path.join(HERE, 'EXTERNAL_MATRIX*.csv')))
    if not files:
        raise SystemExit('没有 EXTERNAL_MATRIX*.csv')
    rows = []
    seen = set()
    for p in files:
        for r in csv.DictReader(open(p, encoding='utf-8')):
            k = (r.get('task_id'), r.get('error_type'))
            if k in seen:
                continue
            seen.add(k)
            # P2 的 deterministic-service E24 是定理明说的定义塌缩，不是可检点。
            if r.get('template') == 'md1' and r.get('error_type') == 'E24':
                r['p5_boundary'] = 'collapse'
                if r.get('verdict') == 'NOT_DETECTED':
                    r['match'] = 'MATCH_COLLAPSE'
            rows.append(r)
    lines = ['# P5 外部教材题：验证报告', '',
             '> 外部题参数与题面见 `external_tasks.jsonl`；真值由 `external_truth.py` 独立复算；',
             '> 判据与 tau* 沿用主表，但这些题不进入主表、不参与 tau* 标定。', '']
    if os.path.exists(REF_CSV):
        rr = list(csv.DictReader(open(REF_CSV, encoding='utf-8')))
        ok = sum(1 for r in rr if r['verdict'] == 'PASS')
        lines += ['## 1. REF 与独立真值对账', '',
                  '`%d/%d` 道 REF 在 R=%d/H=%g 下通过（排队容差 %.0f%%，库存 %.0f%%）。'
                  % (ok, len(rr), REF_N, HOR, REF_TOL * 100, INV_TOL * 100), '',
                  '| task | template | verdict | max_rel | failures |', '|---|---|---|---:|---|']
        for r in rr:
            lines.append('| %s | %s | %s | %s | %s |'
                         % (r['task_id'], r['template'], r['verdict'], r['max_rel'],
                            r['failures'] or ''))
        lines.append('')
    # boundary groups
    groups = {}
    for r in rows:
        key = (r['p5_boundary'], r['match'], r['verdict'])
        groups[key] = groups.get(key, 0) + 1
    lines += ['## 2. 边界复现总表', '', '| P5 预期 | 实测匹配 | 判定 | 件数 |', '|---|---|---|---:|']
    for (b, mt, v), n in sorted(groups.items()):
        lines.append('| %s | %s | %s | %d |' % (b, mt, v, n))
    lines.append('')
    # P1/P2/P3/P4 sections
    def rowset(pred):
        return [r for r in rows if pred(r)]
    p1 = rowset(lambda r: r['error_type'] in ('E01', 'E02', 'E04', 'E25'))
    p2 = rowset(lambda r: r['error_type'] in ('E03', 'E24'))
    p3 = rowset(lambda r: r['error_type'] in ('E14', 'E21'))
    p4 = rowset(lambda r: r['error_type'] == 'E43')
    for title, rs in (('3. P1（次序/均值恒等）', p1),
                      ('4. P2（点判据/结构空转）', p2),
                      ('5. P3（稀有状态：均值 vs p_loss）', p3),
                      ('6. P4（同根估计量）', p4)):
        lines += [title, '', '| task | type | P5 | verdict | match | fired J1 obs | counters |',
                  '|---|---|---|---|---|---|---|']
        for r in rs:
            lines.append('| %s | %s | %s | %s | %s | %s | %s |'
                         % (r['task_id'], r['error_type'], r['p5_boundary'],
                            r['verdict'], r['match'], r['fired_obs'] or '',
                            r['counters'] or ''))
        lines.append('')
    # full detail
    lines += ['## 7. 逐件明细', '',
              '| task | type | expected | P5 | verdict | fired | match | counters | note |',
              '|---|---|---|---|---|---:|---|---|---|']
    for r in rows:
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |'
                     % (r['task_id'], r['error_type'], r['expected'], r['p5_boundary'],
                        r['verdict'], r['fired_n'], r['match'], r['counters'] or '',
                        (r['fired_cells'] or '')[:160]))
    with open(SUMMARY, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote %s' % SUMMARY)
    # console headline
    for b in ('static', 'point', 'weak', 'open'):
        sub = [r for r in rows if r['p5_boundary'] == b]
        if not sub:
            continue
        cnt = {}
        for r in sub:
            cnt[r['match']] = cnt.get(r['match'], 0) + 1
        print('%s n=%d %s' % (b, len(sub), json.dumps(cnt, sort_keys=True)))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'ref'
    if mode == 'ref':
        bad = check_ref()
        if bad:
            print('[ext-ref] FAILURES: %s' % json.dumps(bad, ensure_ascii=False)[:800])
            raise SystemExit(1)
    elif mode == 'matrix':
        shard, nshard = 1, 1
        if len(sys.argv) > 2 and '/' in sys.argv[2]:
            shard, nshard = [int(x) for x in sys.argv[2].split('/')]
        matrix(shard, nshard)
    elif mode == 'summary':
        summarize()
    else:
        raise SystemExit('用法：run_external.py ref|matrix [i/n]|summary')


if __name__ == '__main__':
    main()
