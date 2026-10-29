# -*- coding: utf-8 -*-
"""P1-A：15 个 n10 近阈值格的逐种子噪声。

目的：回答“rel 1.1–2.0% 是真错还是抽样噪声”。
  对每个被标记的 (文件, 观测量) 重跑 R=10 / horizon=40000，取工件自报的 per_seed_* 列表，
  算 mean / sd / se / z=(mean-truth)/se。
  |z|<2 ⇒ 与该格 10 种子的抽样波动同量级，不能仅凭 rel 判真错；
  |z|>=2 ⇒ 统计上显著，再回代码找机制。
注意：这是**仪器侧**的重跑，不是人工基线；人工计时仍要用户盲读。
"""
import csv
import io
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
sys.path.insert(0, BENCH)
import criteria as C  # noqa: E402

ART = os.path.join(BENCH, 'legB', 'flash20261018')
OUT = HERE
CELLS = [
    ('mm1K-05__d1.py', 'mm1K-05', 'busy_frac'),
    ('mm1K-08__d3.py', 'mm1K-08', 'L'),
    ('mmc-01__d1.py', 'mmc-01', 'W'),
    ('mmc-02__d2.py', 'mmc-02', 'W'),
    ('mmc-02__d2.py', 'mmc-02', 'p_wait'),
    ('jackson2-06__d2.py', 'jackson2-06', 'L'),
    ('mmc-03__d1.py', 'mmc-03', 'p_wait'),
    ('mmc-03__d1.py', 'mmc-03', 'L'),
    ('mmc-03__d1.py', 'mmc-03', 'busy_frac'),
    ('mmc-01__d3.py', 'mmc-01', 'L'),
    ('mmcK-01__d1.py', 'mmcK-01', 'L'),
    ('mmc-02__d3.py', 'mmc-02', 'L'),
    ('mmc-08__d3.py', 'mmc-08', 'p_wait'),
    ('mm1-08__d1.py', 'mm1-08', 'L'),
    ('mmc-06__d1.py', 'mmc-06', 'W'),
]
SEEDS = 10
HOR = 40000.0


def truth_of(task, obs):
    tp = task.get('truth_print') or {}
    tr = task.get('truth_raw') or {}
    if tp.get(obs) is not None:
        return float(tp[obs])
    if tr.get(obs) is not None:
        return float(tr[obs])
    # busy_frac 在 truth_print 里是 0-1；p_wait 有时只在 truth_raw
    raise KeyError('%s 的 %s 没有真值' % (task.get('task_id'), obs))


def main():
    tasks = {t['task_id']: t for t in C.load_tasks()}
    # 同一个文件只跑一次
    files = []
    for f, tid, obs in CELLS:
        if f not in [x[0] for x in files]:
            files.append((f, tid))
    obs_by_file = {}
    t0 = time.time()
    for f, tid in files:
        path = os.path.join(ART, f)
        st = time.time()
        obs, wall, note = C.run_artifact(path, SEEDS, HOR, 'none', 1, timeout=420)
        obs_by_file[f] = (obs, note, time.time() - st)
        print('[p1] %-22s %-6s %.1fs note=%s' % (f, 'OK' if obs is not None else 'FAIL', time.time() - st, str(note)[:80]), flush=True)
    rows = []
    for f, tid, ob in CELLS:
        obs, note, wall = obs_by_file[f]
        task = tasks[tid]
        truth = truth_of(task, ob)
        if obs is None:
            rows.append(dict(file=f, task=tid, obs=ob, truth=truth, mean='', sd='', se='', z='',
                             rel='', n=0, wall=round(wall, 1), verdict='RUN_FAIL', note=str(note)[:120]))
            continue
        vals = obs.get('per_seed_%s' % ob)
        if not vals:
            # busy_frac 的键是 per_seed_busy_frac；p_wait 是 per_seed_p_wait；其余同名
            rows.append(dict(file=f, task=tid, obs=ob, truth=truth, mean='', sd='', se='', z='',
                             rel='', n=0, wall=round(wall, 1), verdict='NO_PERSESEED', note=str(note)[:120]))
            continue
        vals = [float(v) for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
        n = len(vals)
        mean = sum(vals) / n if n else float('nan')
        if n >= 2:
            sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1))
            se = sd / math.sqrt(n)
        else:
            sd = se = float('nan')
        z = ((mean - truth) / se) if (se and not math.isnan(se) and se > 0) else float('nan')
        rel = abs(mean - truth) / abs(truth) if truth else float('nan')
        if n < 2 or math.isnan(z):
            verdict = 'UNCERTAIN'
        elif abs(z) < 2:
            verdict = 'WITHIN_NOISE'
        else:
            verdict = 'SIGNIFICANT'
        rows.append(dict(file=f, task=tid, obs=ob, truth=truth, mean=mean, sd=sd, se=se, z=z,
                         rel=rel, n=n, wall=round(wall, 1), verdict=verdict, note=str(note)[:120]))
    with io.open(os.path.join(OUT, 'P1_perseed_noise.csv'), 'w', encoding='utf-8', newline='') as fh:
        wr = csv.DictWriter(fh, fieldnames=['file','task','obs','truth','mean','sd','se','z','rel','n','wall','verdict','note'])
        wr.writeheader()
        for r in rows:
            rr = dict(r)
            for k in ('truth','mean','sd','se','z','rel'):
                if isinstance(rr[k], float):
                    rr[k] = '%.8g' % rr[k]
            wr.writerow(rr)
    lines = []
    lines.append('# P1-A：15 个 n10 格的逐种子噪声（R=10 / horizon=40000）\n')
    lines.append('- 口径：对每个 (文件, 观测量) 重跑一次，取工件自报 `per_seed_*`；')
    lines.append('  `z=(mean−truth)/se`；`|z|<2` 记 `WITHIN_NOISE`，`|z|>=2` 记 `SIGNIFICANT`。')
    lines.append('- 这不是人工基线；人工盲读计时仍待做。\n')
    lines.append('| 文件 | 观测量 | truth | mean | rel | sd | se | z | 判 |')
    lines.append('|---|---|---:|---:|---:|---:|---:|---:|---|')
    for r in rows:
        def g(x, fmt='%.6g'):
            return fmt % x if isinstance(x, float) and not math.isnan(x) else '—'
        lines.append('| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r['file'], r['obs'], g(r['truth']), g(r['mean']),
            ('%.3f%%' % (100 * r['rel'])) if isinstance(r['rel'], float) and not math.isnan(r['rel']) else '—',
            g(r['sd']), g(r['se']), g(r['z'], '%.2f'), r['verdict']))
    lines.append('')
    lines.append('## 读法')
    lines.append('- `WITHIN_NOISE`：该格的 rel 与 10 个种子的抽样波动同量级，不能仅凭 rel>τ* 判真错。')
    lines.append('- `SIGNIFICANT`：统计上显著；回代码找机制（窗口错配 / 自证式估计 / 口径错）。')
    lines.append('- 本表只回答“是否超出噪声”，不回答“是不是语义错”；代码行级判决见 `P1_15格人读_2026-10-19.md`。')
    with io.open(os.path.join(OUT, 'P1_perseed_noise.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('OK rows=%d total=%.1fs -> P1_perseed_noise.{csv,md}' % (len(rows), time.time() - t0))


if __name__ == '__main__':
    main()
