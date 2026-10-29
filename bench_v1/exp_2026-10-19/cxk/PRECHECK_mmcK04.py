"""单点预验：正文说"12 个不吻合全在 mmcK-01..04，每题 4 格"。
这不必等 ρ=0.4 扫描，直接从 full64 矩阵现算：每题 × {E03,E24} × {L,W} 的 J1 格里，
|rel|<τ* 且 fired=0 的有几个。对不上就先怀疑正文那句，不是先怀疑数据。
"""
import csv
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
F64 = os.path.normpath(os.path.join(HERE, '..', 'full64'))
TAU = 0.01

agg = {}
for fn in sorted(os.listdir(F64)):
    if not (fn.startswith('MUTANT_MATRIX_full64.shard') and fn.endswith('.csv')
            and '.triggers.' not in fn):
        continue
    for r in csv.DictReader(io.open(os.path.join(F64, fn), encoding='utf-8', newline='')):
        tid, et, st, ob = r.get('task_id'), r.get('error_type'), r.get('stage'), r.get('instance')
        if not (tid and tid.startswith('mmcK-0') and et in ('E03', 'E24')
                and st == 'J1' and ob in ('L', 'W')):
            continue
        rel = abs(float(r['rel'])) if r.get('rel') not in (None, '') else None
        fired = r.get('fired_0.01')
        if rel is None:
            continue
        cell = (tid, et, ob)
        prev = agg.get(cell)
        # 同一格可能有多件 instance（多种子/多次注入），取最大 |rel|（最有利于"点火"的那件）
        agg[cell] = rel if prev is None else max(prev, rel)
        agg.setdefault(cell + ('fired',), fired)

rows = sorted(k for k in agg if len(k) == 3)
below = [k for k in rows if agg[k] < TAU]
per_task = {}
for k in below:
    per_task[k[0]] = per_task.get(k[0], 0) + 1

# 28 个低于阈值 ≠ 12 个不吻合。差额必须是"机制没跑"的 IDLE 格，
# 而且只能按**对账表自己的判定**来分，不许我拿 rel 猜（拿读数像不像去推断有没有跑，
# 是这条仪器 10-17 明确犯过的错）。所以直接解析权威对账表的 verdict 列。
RECON = os.path.join(F64, 'UNDETECTABILITY_MATRIX_full64.md')
verdict = {}
for line in io.open(RECON, encoding='utf-8'):
    mm = re.match(r'^\| `(E03|E24)/(L|W)@mmcK\((mmcK-0\d)\)` \| \S+ \| (\S+)', line)
    if mm:
        verdict[(mm.group(3), mm.group(1), mm.group(2))] = mm.group(4)
idle_below = [k for k in below if str(verdict.get(k, '')).startswith('IDLE')]
judged_below = [k for k in below if k not in idle_below and k in verdict]
unexplained = [k for k in below if k not in verdict]

out = ['mmcK-0x 的 J1×{L,W}×{E03,E24} 格：共 %d 个；|rel| < τ*=%.3f 的 %d 个' % (len(rows), TAU, len(below)), '',
       '低于阈值的 %d 个按**权威对账表的 verdict 列**拆开（不是按 rel 猜有没有跑）：' % len(below),
       '  - 已判且低于阈值（=不吻合）：%d' % len(judged_below),
       '  - 对账表判 IDLE（机制没跑，不进分母）：%d' % len(idle_below),
       '  - 对账表里找不到、无法归类：%d %s' % (len(unexplained), unexplained[:3] or ''),
       '  - 合计 %d，与"低于阈值 %d"%s' % (len(judged_below) + len(idle_below) + len(unexplained),
                                        len(below),
                                        '一致' if len(judged_below) + len(idle_below) + len(unexplained) == len(below) else '**不一致，有格没交代**'), '',
       '正文那句"12 个不吻合全在 mmcK-01..04"逐题核对：', '']
for t in sorted(per_task):
    out.append('  %s: %d 格低于阈值' % (t, per_task[t]))
out.append('')
out.append('逐格 max|rel|：')
for k in rows:
    out.append('  %-12s %-4s %-2s  |rel|=%.6f  %s' % (k[0], k[1], k[2], agg[k],
                                                       'BELOW' if agg[k] < TAU else 'above'))
io.open(os.path.join(HERE, 'PRECHECK_mmcK04.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out[:14]))
print('...  写了 %d 行 -> PRECHECK_mmcK04.md' % len(out))
