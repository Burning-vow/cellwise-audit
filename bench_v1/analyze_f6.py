"""F6 分析：把 `F6_BLOCKS.csv` 的独立块读数汇成**检出率 vs 样本预算**的曲线。

只读产物，不改任何判定、不改 τ*。分母全部现算（规矩：条数要带载体）。

四层输出，按"能不能被写进论文"排：
 1. **F6 题面判决**：R=20 检出率<50% 成不成立、R=100>80% 成不成立。
    两把尺子都要报：`按选带`（R=10 那次读数落在 [3%,6%] ⇒ 有回归均值污染）与
    `按 δ̂`（用最大臂的合并读数重新判带 ⇒ 题面真正说的东西）。
 2. **√R 律实测**：同一格在 R=20 与 R=100 上的**块间标准差**之比应≈√5。
    这是 P3 的机制内容，与"检出率"是两条独立的证据；它只要一条就够写
    （"噪声按 1/√R 收缩，实测比值 X"），不需要 δ 落在哪个带。
 3. **δ_min(R) 经验表**：每个臂上"检出率首次 ≥50%" 的最小 δ̂ ⇒ 直接对着
    `预注册 §4` 那句"样本预算是可检性的第三个自变量"给数。
 4. **近阈值层的逐格曲线**：`near` 层（δ̂ 在自己 τ* 的 0.5–1.5 倍内）才是真会随 R 翻脸的那几格。

防三种自欺（都是这个项目付过学费的）：
 a. `DETERMINISTIC` 哨：同一格所有块 rel **逐位相同** ⇒ 这件工件是闭式解不是随机仿真
    （eoq/newsvendor 实测如此），预算轴对它**不适用** ⇒ 从检出率分母里剔除并单独报数，
    否则"100% 检出"里掺着"N 次抄同一个数"。
 b. NA 哨：`fired` 为空 = 该格在这一臂上没判定（缺真值/缺字段/没标定 τ*），不许当 0 计入漏检。
 c. 缺臂哨：某臂一行都没有 ⇒ 明说"还没跑到"，不许用另一臂外推。
"""
import csv
import io
import math
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('F6_SRC') or os.path.join(HERE, 'F6_BLOCKS.csv')
OUT = os.environ.get('F6_MD') or os.path.join(HERE, 'F6_BUDGET.md')
BAND = (0.03, 0.06)
NEAR = (0.5, 1.5)          # 近阈值：δ 在自己 τ* 的 0.5–1.5 倍
NEAR_MIN_REL = 0.005
SHARDS = [os.path.join(HERE, 'MUTANT_MATRIX_R10b.shard%d.csv' % i) for i in (1, 2, 3, 4)]
L = []


def emit(s=''):
    L.append(str(s))
    sys.stdout.buffer.write((str(s) + chr(10)).encode('utf-8', 'replace'))


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / float(n)
    den = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4.0 * n * n)) ** 0.5) / den
    return max(0.0, c - h), min(1.0, c + h)


def sd(vals):
    n = len(vals)
    if n < 2:
        return None
    m = sum(vals) / n
    return (sum((v - m) ** 2 for v in vals) / (n - 1)) ** 0.5


def rel10_table():
    """主矩阵（R=10）的逐格权威读数：`{(key, criterion, statistic): (rel, tau)}`。

    CSV 里那列 `stratum` 是**按件**union 出来的（`run_f6_budget.py` 里 strat 取的是整件的层），
    拿它当"这个格在带内"会把同件里 rel≈1e-5 的守恒格一起算进检出率分母——
    10-18 第一次跑分析器就被这条骗过一次（"按 R=10 选带"报出 50%，而真带内格是 100%）。
    所以选带一律回主矩阵重查，`stratum` 列只当注释看。
    """
    import csv as _csv
    from summarize_matrix_v2 import load_tau, STAGE2CRIT
    TAU, _ = load_tau()
    t = {}
    for p in SHARDS:
        with io.open(p, encoding='utf-8') as f:
            for r in _csv.DictReader(f):
                crit = STAGE2CRIT.get(r['stage'])
                if crit is None or r['rel'] in ('', None):
                    continue
                k = (r['template'], crit, r['instance'])
                if k not in TAU:
                    continue
                t[(r['key'], crit, r['instance'])] = (float(r['rel']), TAU[k])
    return t


def main():
    R10 = rel10_table()
    if not os.path.exists(SRC):
        emit('# F6 预算曲线 —— 还没有产物：%s 不存在' % SRC)
        io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        return 1
    rows = [r for r in csv.DictReader(io.open(SRC, encoding='utf-8'))]
    # `.triggers.csv` 这类旁文件不吃（显式只读 F6_BLOCKS.csv）；重复键要报出来而不是默默合并
    seen, dup = set(), 0
    for r in rows:
        k = (r['key'], r['R'], r['block'], r['criterion'], r['statistic'])
        if k in seen:
            dup += 1
        seen.add(k)
    cells = defaultdict(list)
    for r in rows:
        if r['fired'] in ('', None):
            continue                       # NA：这一格这一臂没判定，不进分母
        cells[(r['key'], r['criterion'], r['statistic'])].append(
            (int(r['R']), int(r['block']), float(r['rel']), float(r['tau_star']),
             int(r['fired']), r['stratum']))
    arms = sorted({int(r['R']) for r in rows})
    emit('# F6 检出率 vs 样本预算（%s）' % time.strftime('%Y-%m-%d %H:%M'))
    emit('')
    emit('读入 `%s`：**%d 行**（重复键 %d）｜有判定的格 **%d** ｜臂 = %s ｜块数每臂 = %s' % (
        os.path.basename(SRC), len(rows), dup, len(cells), arms,
        ', '.join('R=%d:%d' % (a, len({r['block'] for r in rows if int(r['R']) == a}))
                  for a in arms)))
    emit('')
    if not cells:
        emit('⚠ 一条判定都没有 ⇒ 链还没跑出可用读数，先看 `_f6_run.log`。')
        io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        return 1

    # ---- (0) δ̂ 与确定性哨 ----
    big = max(arms)
    delta = {}
    for ck, vs in cells.items():
        vb = sorted(v[2] for v in vs if v[0] == big) or sorted(v[2] for v in vs)
        # 中位数而不是均值：`rel` 存的是**绝对**偏差，噪声比 δ 大时均值会被正向抬起来
        # （近阈值层首当其冲）。中位同样有正向偏差，但小得多，且这里只需要"落在哪个档"。
        delta[ck] = vb[len(vb) // 2]
    det = {ck for ck, vs in cells.items() if len({('%.12g' % v[2]) for v in vs}) == 1}

    # ---- (1) 题面判决 ----
    emit('## (1) F6 题面：`|δ|∈[3%,6%] ⇒ R=20 检出率<50%，R=100 检出率>80%`')
    emit('')
    emit('两把尺子的差别是**选带用了哪一次读数**：`按 R=10` 有回归均值污染（选中它就是因为它这次读得高），'
         '`按 δ̂(R=%d)` 才是题面说的 δ。' % big)
    emit('')
    emit('| 尺子 | 臂 | 格数 | 判定次数 | 点火 | 检出率 | Wilson 95% | 题面阈值 | 判 |')
    emit('|---|---|---|---|---|---|---|---|---|')
    for nm, by_delta in (('按 R=10 选带', False), ('按 δ̂ 重新判带', True)):
        for a in arms:
            ks = [ck for ck, vs in cells.items()
                  if ck not in det and any(v[0] == a for v in vs)
                  and (BAND[0] <= delta[ck] <= BAND[1] if by_delta
                       else (ck in R10 and BAND[0] <= R10[ck][0] <= BAND[1]))]
            draws = [(ck, a) for ck in ks]
            if not draws:
                emit('| %s | R=%d | 0 | — | — | — | — | — | 无合格格 |' % (nm, a))
                continue
            n = k = 0
            for ck in ks:
                for v in cells[ck]:
                    if v[0] == a:
                        n += 1
                        k += v[4]
            rate = k / float(n)
            lo, hi = wilson(k, n)
            thr = '<50%' if a <= 20 else '>80%'
            ok = ('成立' if (rate < 0.5 if a <= 20 else rate > 0.8) else '**不成立**')
            emit('| %s | R=%d | %d | %d | %d | %.1f%% | [%.1f%%, %.1f%%] | %s | %s |'
                 % (nm, a, len(ks), n, k, 100 * rate, 100 * lo, 100 * hi, thr, ok))
    emit('')
    emit('- 被"确定性哨"剔出的格 = **%d**（同一格所有块逐位相同 ⇒ 闭式解/恒 0，预算轴不适用）%s'
         % (len(det), '：' + ', '.join('%s·%s·%s' % c for c in sorted(det)[:6]) if det else ''))
    # 陷阱显形：CSV 的 `stratum` 列是**按件**打的。谁将来拿它选带，就会把同件的守恒格/恒 0 格
    # 一起算进分母（本轮实测被它骗过一次：带内 2 格报成 4 格、检出率从 100% 掉成 50%）。
    polluted = [ck for ck, vs in cells.items()
                if any(v[5] and 'band' in v[5] for v in vs)
                and not (ck in R10 and BAND[0] <= R10[ck][0] <= BAND[1])]
    emit('- 陷阱自检：`stratum` 列写着 band 但 R=10 权威表说它不在带内的格 = **%d** ⇒ 该列只当注释，'
         '本报告选带一律回 `%s`（%d 格）重查' % (len(polluted), 'MUTANT_MATRIX_R10b.shard*.csv', len(R10)))
    emit('')

    # ---- (2) √R 律实测 ----
    emit('## (2) √R 律实测（P3 的机制内容，与检出率是两条独立证据）')
    emit('')
    emit('同一格在两条臂上的**块间标准差**之比，理论值 = √(R_hi/R_lo)；'
         '`归一化` 列 = 实测比 / 理论比，**1.00 = 恰好按 1/√R 收缩**。')
    emit('这条量的是 rel 的散布，与"点估计准不准"无关 ⇒ 不依赖 δ 落在哪个带。')
    emit('')
    emit('| 比较 | 可比格数 | 中位 σ(低臂) | 中位 σ(高臂) | 实测比 | 理论比 | 归一化 |')
    emit('|---|---|---|---|---|---|---|')
    if len(arms) < 2:
        emit('  ⚠ 现在只有 **1 条臂**（R=%s）⇒ 这一节按定义还测不了，等 R=100 那一相跑完再看。'
             % arms[0])
    for i in range(len(arms) - 1):
        a, b = arms[i], arms[i + 1]
        th = math.sqrt(b / float(a))
        pairs = []
        for ck, vs in cells.items():
            sa, sb = sd([v[2] for v in vs if v[0] == a]), sd([v[2] for v in vs if v[0] == b])
            if sa and sb and sa > 0 and sb > 0:
                pairs.append((sa, sb))
        if pairs:
            pairs.sort(key=lambda x: x[0] / x[1])
            rmed = pairs[len(pairs) // 2][0] / pairs[len(pairs) // 2][1]
            smed = sorted(p[0] for p in pairs)[len(pairs) // 2]
            tmed = sorted(p[1] for p in pairs)[len(pairs) // 2]
            emit('| σ(%d)/σ(%d) | %d | %.3g | %.3g | %.2f | %.2f | **%.2f** |'
                 % (a, b, len(pairs), smed, tmed, rmed, th, rmed / th))
        else:
            emit('| σ(%d)/σ(%d) | 0 | — | — | — | %.2f | — |' % (a, b, th))
            emit('')
            emit('  ⚠ 这一对臂**一条可比格都没有**（某臂还没跑到，或每臂不足 2 块）⇒ 不许拿单边外推。')
    emit('')

    # ---- (3) δ_min(R) 经验表 ----
    emit('## (3) δ_min(R)：每个臂上"检出率首次 ≥50%" 的最小 δ̂')
    emit('')
    emit('| δ̂ 档 | 格数 | ' + ' | '.join('R=%d' % a for a in arms) + ' |')
    emit('|---|---|' + '---|' * len(arms))
    bins = [(0.0, 0.005), (0.005, 0.01), (0.01, 0.02), (0.02, 0.03), (0.03, 0.06),
            (0.06, 0.15), (0.15, 1.0), (1.0, float('inf'))]
    for lo, hi in bins:
        ks = [ck for ck in cells if lo <= delta[ck] < hi and ck not in det]
        line = []
        for a in arms:
            n = k = 0
            for ck in ks:
                for v in cells[ck]:
                    if v[0] == a:
                        n += 1
                        k += v[4]
            line.append('%.0f%%(%d)' % (100.0 * k / n, n) if n else '—')
        emit('| %s–%s | %d | %s |' % ('%.1f%%' % (lo * 100),
                                      ('∞' if hi == float('inf') else '%.1f%%' % (hi * 100)),
                                      len(ks), ' | '.join(line)))
    emit('')

    # ---- (4) 近阈值层逐格 ----
    emit('## (4) 近阈值层逐格（δ̂ 在自己 τ* 的 0.5–1.5 倍内：真会随 R 翻脸的格）')
    emit('')
    emit('| 格 | τ* | δ̂ | δ̂/τ* | ' + ' | '.join('R=%d 检出' % a for a in arms) + ' |')
    emit('|---|---|---|---|' + '---|' * len(arms))
    near = [(ck, cells[ck]) for ck in cells
            if ck in R10 and R10[ck][0] >= NEAR_MIN_REL
            and NEAR[0] * R10[ck][1] <= R10[ck][0] <= NEAR[1] * R10[ck][1]
            and ck not in det]
    for ck, vs in sorted(near, key=lambda x: -delta[x[0]]):
        tau = vs[0][3]
        cols = []
        for a in arms:
            n = len([v for v in vs if v[0] == a])
            k = sum(v[4] for v in vs if v[0] == a)
            cols.append('%d/%d' % (k, n) if n else '—')
        emit('| %s·%s·%s | %.3f | %.3f%% | %.2fx | ' % (ck[0], ck[1], ck[2], tau,
                                                         delta[ck] * 100, delta[ck] / tau)
             + ' | '.join(cols) + ' |')
    emit('')
    emit('⚠ 这一层若出现"同一格 R=%d 全不点火、R=%d 全点火"，那才是 P3 要的证据；'
         '如果整层在两条臂上都同向，说明本文语料的近阈值格仍然不够近。' % (arms[0], big))

    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    sys.stderr.write('wrote %s (%d lines)\n' % (OUT, len(L)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
