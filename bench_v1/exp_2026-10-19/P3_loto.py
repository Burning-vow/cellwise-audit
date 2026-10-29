# -*- coding: utf-8 -*-
"""P3-B：leave-one-template-out 重标 τ*。

问题：τ* 是在 64 道参照题上按 (criterion, statistic, template) 标定的；
      如果把某个 template 的所有题拿掉，用其余 template 的 trials 重标，
      这个“外来的 τ*”在留出 template 上还能不能把 FP 的 Wilson 上界压在 5% 以内？

口径：
  - 只处理非确定式格（同一组 trials 的唯一值数 > 1）。
  - 每个 (crit, stat, T)：pool = 所有 template != T 的 trials；held = T 的 trials。
  - 用 pool 按 R1（最小 τ 使 Wilson 上界 ≤5%）选 τ；若无 R1，用 R3（最小 τ 使 pool 零报警）。
  - 在 held 上算 k=rel>τ、n、Wilson 上界；≤5% 记 PASS，否则 FAIL。
  - 原始 τ* 从 table_tau_v2.csv 读，用于比较 τ 是否换档。

产物：P3_loto.csv / P3_loto.md。只读，不写权威件。
"""
import csv
import io
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
sys.path.insert(0, BENCH)
import criteria as C  # noqa: E402

RAW = os.path.join(BENCH, 'RECAL64_raw.jsonl')
TAU = os.path.join(BENCH, 'table_tau_v2.csv')
OUT = HERE
GRID = C.TAU_GRID
TARGET = C.WILSON_TARGET_UPPER


def pick(trials):
    """返回 (tau, rule, k, n)；R1 优先，R3 兜底。"""
    n = len(trials)
    if not n:
        return (None, 'none', 0, 0)
    for tau in GRID:
        k = sum(1 for v in trials if v > tau)
        if C.wilson(k, n)[1] <= TARGET:
            return (tau, 'R1', k, n)
    for tau in GRID:
        k = sum(1 for v in trials if v > tau)
        if k == 0:
            return (tau, 'R3', k, n)
    return (None, 'none', 0, n)


def main():
    # 1. 原始 τ 表
    orig = {}
    with io.open(TAU, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['tau_star'] in ('', 'NONE'):
                continue
            orig[(r['criterion'], r['statistic'], r['template'])] = (float(r['tau_star']), r['rule'])

    # 2. raw trials
    groups = defaultdict(lambda: defaultdict(list))  # (crit,stat,tpl) -> task -> [rel]
    for line in io.open(RAW, encoding='utf-8'):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get('purpose') != 'task' or d.get('error'):
            continue
        tpl = d.get('template')
        for kk, v in (d.get('rel') or {}).items():
            parts = kk.split('|')
            if len(parts) != 2:
                continue
            groups[(parts[0], parts[1], tpl)][d['task_id']].append(float(v))

    rows = []
    for (crit, stat, tpl), by_task in sorted(groups.items()):
        # 只处理非确定式格：整组 trials 的唯一值数 > 1
        all_trials = [v for vs in by_task.values() for v in vs]
        if len({round(v, 12) for v in all_trials}) <= 1:
            continue
        # 其他 template 的 trials
        pool = []
        for (c2, s2, t2), bt2 in groups.items():
            if c2 == crit and s2 == stat and t2 != tpl:
                pool.extend(v for vs in bt2.values() for v in vs)
        if len(pool) < 10:
            continue
        tau, rule, kp, npool = pick(pool)
        if tau is None:
            continue
        held = all_trials
        kh = sum(1 for v in held if v > tau)
        nh = len(held)
        hi = C.wilson(kh, nh)[1] if nh else float('nan')
        if nh == 0:
            status = 'NO_TRIALS'
        elif hi <= TARGET:
            status = 'PASS'
        elif kh > 0:
            status = 'REAL_FAIL'
        else:
            # 0/n 且上界 >5%：不是校准失败，是留出样本不够（0/60 的上界就是 6.02%）
            status = 'UNDERPOWERED'
        passed = (status == 'PASS')
        ot, orule = orig.get((crit, stat, tpl), (None, ''))
        rows.append(dict(criterion=crit, statistic=stat, template=tpl,
                         orig_tau=ot, orig_rule=orule,
                         loto_tau=tau, loto_rule=rule,
                         pool_k=kp, pool_n=npool,
                         held_k=kh, held_n=nh,
                         held_fp=(kh / nh if nh else float('nan')),
                         held_hi=hi, passed=passed, status=status,
                         delta=(tau - ot if ot is not None else float('nan'))))

    # 3. 输出
    with io.open(os.path.join(OUT, 'P3_loto.csv'), 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['criterion','statistic','template','orig_tau','orig_rule','loto_tau','loto_rule',
                     'pool_k','pool_n','held_k','held_n','held_fp','held_hi','passed','status','delta'])
        for r in rows:
            wr.writerow([r['criterion'], r['statistic'], r['template'],
                         '' if r['orig_tau'] is None else '%.3f' % r['orig_tau'], r['orig_rule'],
                         '%.3f' % r['loto_tau'], r['loto_rule'], r['pool_k'], r['pool_n'],
                         r['held_k'], r['held_n'], '%.6f' % r['held_fp'], '%.6f' % r['held_hi'],
                         int(r['passed']), r['status'],
                         '' if math.isnan(r['delta']) else '%.3f' % r['delta']])
    lines = []
    def w(s=''):
        lines.append(s)
    cnt = Counter(r['status'] for r in rows)
    npass, nreal, nunder = cnt['PASS'], cnt['REAL_FAIL'], cnt['UNDERPOWERED']
    powered = npass + nreal
    w('# P3-B：leave-one-template-out 重标 τ*（现算）\n')
    w('- 输入：`RECAL64_raw.jsonl`（64 题 × 10 trials）、`table_tau_v2.csv`（83 行）。')
    w('- 只处理非确定式格；pool = 其他 template 的 trials；held = 留出 template 的 trials。')
    w('- 选 τ：R1（最小 τ 使 pool Wilson 上界 ≤5%）；无 R1 用 R3（pool 零报警）。')
    w('- PASS = held 的 Wilson 上界 ≤5%，即“外来的 τ 在留出 template 上仍守住假阳门”。\n')
    w('## 汇总\n')
    w('- 可测格 **%d**：PASS **%d**，REAL_FAIL **%d**，UNDERPOWERED **%d**，NO_TRIALS **%d**。'
      % (len(rows), npass, nreal, nunder, cnt['NO_TRIALS']))
    w('- **有功效的格 = PASS + REAL_FAIL = %d；真失败 %d/%d = %.1f%%**。' % (
        powered, nreal, powered, 100.0 * nreal / max(1, powered)))
    w('- UNDERPOWERED 是“held 0 报警但 n 太小”：0/60 的 Wilson 上界本来就是 6.02%，')
    w('  不是校准失败；这些格要补样本或标“不可判”，不能算进 FAIL。')
    w('- τ 换档（loto_tau != orig_tau）**%d** 格；其中变高 %d、变低 %d。' % (
        sum(1 for r in rows if r['orig_tau'] is not None and abs(r['loto_tau'] - r['orig_tau']) > 1e-9),
        sum(1 for r in rows if r['orig_tau'] is not None and r['loto_tau'] > r['orig_tau'] + 1e-9),
        sum(1 for r in rows if r['orig_tau'] is not None and r['loto_tau'] < r['orig_tau'] - 1e-9)))
    w('')
    w('## 真失败（held 有报警且 Wilson 上界 >5%）\n')
    w('| 判据 | 统计量 | 留出 template | 原 τ | LOTO τ | held k/n | held FP | Wilson 上界 |')
    w('|---|---|---|---:|---:|---:|---:|---:|')
    for r in rows:
        if r['status'] == 'REAL_FAIL':
            w('| %s | %s | %s | %s | %.3f | %d/%d | %.2f%% | %.2f%% |' % (
                r['criterion'], r['statistic'], r['template'],
                '—' if r['orig_tau'] is None else '%.3f' % r['orig_tau'],
                r['loto_tau'], r['held_k'], r['held_n'], 100 * r['held_fp'], 100 * r['held_hi']))
    w('')
    w('## 功效不足（held 0 报警，但 0/n 的 Wilson 上界 >5%）\n')
    w('| 判据 | 统计量 | 留出 template | 原 τ | LOTO τ | held k/n | 上界 |')
    w('|---|---|---|---:|---:|---:|---:|')
    for r in rows:
        if r['status'] == 'UNDERPOWERED':
            w('| %s | %s | %s | %s | %.3f | %d/%d | %.2f%% |' % (
                r['criterion'], r['statistic'], r['template'],
                '—' if r['orig_tau'] is None else '%.3f' % r['orig_tau'],
                r['loto_tau'], r['held_k'], r['held_n'], 100 * r['held_hi']))
    w('')
    w('## PASS 但 τ 换档的格（说明“换模板后阈值会变”，但不破 5% 门）\n')
    w('| 判据 | 统计量 | template | 原 τ | LOTO τ | Δ | held k/n |')
    w('|---|---|---|---:|---:|---:|---:|')
    for r in sorted(rows, key=lambda z: (-abs(z['delta']) if not math.isnan(z['delta']) else 0)):
        if r['passed'] and r['orig_tau'] is not None and abs(r['loto_tau'] - r['orig_tau']) > 1e-9:
            w('| %s | %s | %s | %.3f | %.3f | %+.3f | %d/%d |' % (
                r['criterion'], r['statistic'], r['template'], r['orig_tau'], r['loto_tau'],
                r['delta'], r['held_k'], r['held_n']))
    w('')
    w('## 读法')
    w('- REAL_FAIL **3** 格（`mh2` 的 L/W、`mm1K` 的 p_loss）⇒ “每个 template 必须自己标 τ*”有数据支撑；')
    w('  尤其 `mh2`：外来 τ=0.01 vs 自己的 0.03/0.02，held FP **18.33%**、上界 **29.92%**。')
    w('- PASS **46** 格 ⇒ 其余模板的外来 τ 能守住 5% 门；per-template 标定的价值是**局部防泄漏**，不是全局更好。')
    w('- UNDERPOWERED **16** 格 ⇒ 0/60 的上界 6.02%，样本不够；论文不能把它们算进 FAIL，要补样本或标“不可判”。')
    w('- 本表只查假阳门；不查 held 上的检出率（那需要把注入件按 template 再切一次）。')
    with io.open(os.path.join(OUT, 'P3_loto.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('OK cells=%d pass=%d real_fail=%d underpowered=%d' % (len(rows), npass, nreal, nunder))


if __name__ == '__main__':
    main()
