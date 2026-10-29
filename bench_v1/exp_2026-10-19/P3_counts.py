# -*- coding: utf-8 -*-
"""P3-A：R10b/R10c 预注册对照 + 题簇级良性上界 + 每格 n/Wilson。

只读 bench_v1 权威件；产物写 exp_2026-10-19/。
关键：良性 68 件来自 20 道题，工件级 0/68=5.3%，题簇级 0/20=16.1%。
"""
import csv, io, math, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
sys.path.insert(0, BENCH)
import criteria as C  # noqa: E402

TAGS_C = os.path.join(BENCH, 'MUTANT_TAGS_R10c.csv')
TAGS_B = os.path.join(BENCH, 'MUTANT_TAGS_R10b_regen.csv')
OUT = HERE
CATS = ('detectable', 'blind', 'weak', 'benign')
TAGS = ('TP', 'BLIND_CONFIRM', 'WEAK_FIRED', 'BENIGN_OK', 'INJECTION_IDLE', 'NA_NOINST')


def load(path):
    with io.open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.96):
    # 本地实现，避免 criteria.wilson 在极端 k/n 上的 domain error；先对 k>n 做硬断言
    if n <= 0:
        return (float('nan'), float('nan'))
    assert 0 <= k <= n, ('wilson 收到 k>n', k, n)
    p = k / float(n)
    den = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def ok_for(cat, tag):
    return ((cat == 'detectable' and tag == 'TP') or
            (cat == 'blind' and tag == 'BLIND_CONFIRM') or
            (cat == 'weak' and tag == 'WEAK_FIRED') or
            (cat == 'benign' and tag == 'BENIGN_OK'))


def cat_of(r):
    exp, tag = r['expected_declared'], r['tag_strict_A']
    if tag == 'INJECTION_IDLE' or tag == 'NA_NOINST':
        return None
    return exp if exp in CATS else None


def main():
    rc, rb = load(TAGS_C), load(TAGS_B)
    assert len(rc) == 408 and len(rb) == 408, (len(rc), len(rb))
    b_by = {(r['task_id'], r['error_type']): r for r in rb}
    c_by = {(r['task_id'], r['error_type']): r for r in rc}
    assert set(b_by) == set(c_by), '两代键不一致'
    na_b = {k for k, r in b_by.items() if r['tag_strict_A'] == 'NA_NOINST'}
    e3943 = {k for k in c_by if k[1] in ('E39', 'E40', 'E41', 'E42', 'E43')}
    assert na_b == e3943, ('R10b NA 不等于 E39–E43', len(na_b), len(e3943))

    lines = []
    def w(s=''):
        lines.append(s)

    w('# P3-A：预注册对照 + 题簇上界 + 每格 n（现算）\n')
    w('- 输入：`MUTANT_TAGS_R10b_regen.csv`、`MUTANT_TAGS_R10c.csv`（各 408 行）；')
    w('  R10b 的 62 行 `NA_NOINST` 恰好是 E39–E43（脚本断言过）。')
    w('- `INJECTION_IDLE` 不进任何分子分母。\n')

    # 1. pre/post
    w('## 1. R10b（预注册）→ R10c（含 E39–E43）\n')
    w('| 判定档 | R10b 346 件（已判） | R10c 408 件 | 差值 | E39–E43 贡献 |')
    w('|---|---:|---:|---:|---:|')
    for tag in TAGS:
        nb = sum(1 for r in rb if r['tag_strict_A'] == tag)
        nc = sum(1 for r in rc if r['tag_strict_A'] == tag)
        ne = sum(1 for r in rc if r['tag_strict_A'] == tag and r['error_type'] in ('E39','E40','E41','E42','E43'))
        w('| %s | %d | %d | %+d | %d |' % (tag, nb, nc, nc - nb, ne))
    w('')
    w('读法：新增 5 类带来 36 TP + 20 BLIND + 2 WEAK + 4 IDLE = 62 件；')
    w('**预注册子集本身已是 186/186、37/37**，所以 R10c 的 222/222、57/57 不是“加类加出来的”。')
    w('论文把 R10b 当确证、R10c 当含事后新增的扩展；E43 的 14 件标“仪器级构造”。\n')

    # 2. by task / cluster
    by_task = defaultdict(lambda: {c: [0, 0] for c in CATS})
    for r in rc:
        c = cat_of(r)
        if c is None:
            continue
        by_task[r['task_id']][c][1] += 1
        if ok_for(c, r['tag_strict_A']):
            by_task[r['task_id']][c][0] += 1
    w('## 2. 题簇：100% 不是 222 个独立试验；良性 5.3% 不是 68 个独立试验\n')
    w('| 类别 | 工件级 | 有该类的题簇 | 题簇级正确/可判 | 题簇级界 | 每题都 100%？ |')
    w('|---|---:|---:|---:|---|---|')
    for c in CATS:
        n_art = sum(v[c][1] for v in by_task.values())
        k_art = sum(v[c][0] for v in by_task.values())
        cl = [v[c] for v in by_task.values() if v[c][1] > 0]
        nc = len(cl)
        if c == 'benign':
            # 题簇级事件 = 该题是否有任何良性件被误杀
            bad = sum(1 for x in cl if x[0] != x[1])
            lo, hi = wilson(bad, nc)
            cluster_cell = '%d/%d 题有误杀' % (bad, nc)
            bound = '上界 %.1f%%' % (100 * hi)
            uniform = '是（每题 0 误杀）' if bad == 0 else '否'
        else:
            # 题簇级事件 = 该题是否全部按声明行为
            okc = sum(1 for x in cl if x[0] == x[1])
            lo, hi = wilson(okc, nc)
            cluster_cell = '%d/%d 题全对' % (okc, nc)
            bound = '下界 %.1f%%' % (100 * lo) if okc == nc else '—'
            uniform = '是（每题 100%）' if okc == nc else '否'
        w('| %s | %d/%d | %d | %s | %s | %s |' % (c, k_art, n_art, nc, cluster_cell, bound, uniform))
    n_ben_task = sum(1 for v in by_task.values() if v['benign'][1] > 0)
    w('')
    w('**结论**：')
    w('- 可检/不可检/弱档在每道观测到的题上都是 100%；按题 bootstrap 恒等于 100%，不是 95% 区间。')
    w('- 良性 0/68 的工件级 Wilson 上界 5.3%%；但良性件只来自 **%d 道题**，题簇级 0/%d 的上界 **%.1f%%**。'
      % (n_ben_task, n_ben_task, 100 * wilson(0, n_ben_task)[1]))
    w('  论文两个都要报，后者才是“换一道新题还不会误杀”的可辩护上界。\n')

    # 3. per cell
    cells = defaultdict(lambda: {c: [0, 0] for c in CATS})
    for r in rc:
        c = cat_of(r)
        if c is None:
            continue
        key = (r['template'], r['family'])
        cells[key][c][1] += 1
        if ok_for(c, r['tag_strict_A']):
            cells[key][c][0] += 1
    w('## 3. 每格（template×family）的 n 与 Wilson\n')
    w('只列 n≤6 的格；完整表见 `P3_cell_n.csv`。\n')
    w('| 模板 | family | 类别 | 正确/可判 | Wilson 95% |')
    w('|---|---|---|---:|---|')
    small = 0
    for (tpl, fam), d in sorted(cells.items()):
        for c in CATS:
            k, n = d[c]
            if 0 < n <= 6:
                small += 1
                lo, hi = wilson(k, n)
                w('| %s | %s | %s | %d/%d | %.1f–%.1f%% |' % (tpl, fam, c, k, n, 100*lo, 100*hi))
    w('')
    w('读法：`n=2` 的 2/2 只能写“2 件都点火”，不能写“该格 100% 可检”；')
    w('`n=6` 的 6/6 下界约 61%。图 2 已把 n 印在格子里，正文不要再用“100%”概括整张图。\n')

    # CSV
    with io.open(os.path.join(OUT, 'P3_prepost.csv'), 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['tag', 'r10b', 'r10c', 'diff', 'e3943'])
        for tag in TAGS:
            nb = sum(1 for r in rb if r['tag_strict_A'] == tag)
            nc = sum(1 for r in rc if r['tag_strict_A'] == tag)
            ne = sum(1 for r in rc if r['tag_strict_A'] == tag and r['error_type'] in ('E39','E40','E41','E42','E43'))
            wr.writerow([tag, nb, nc, nc - nb, ne])
    with io.open(os.path.join(OUT, 'P3_by_task.csv'), 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['task_id'] + ['%s_ok' % c for c in CATS] + ['%s_n' % c for c in CATS])
        for tid in sorted(by_task):
            v = by_task[tid]
            wr.writerow([tid] + [v[c][0] for c in CATS] + [v[c][1] for c in CATS])
    with io.open(os.path.join(OUT, 'P3_cell_n.csv'), 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['template','family','category','ok','n','wilson_lo','wilson_hi'])
        for (tpl, fam), d in sorted(cells.items()):
            for c in CATS:
                k, n = d[c]
                if n:
                    lo, hi = wilson(k, n)
                    wr.writerow([tpl, fam, c, k, n, '%.6f' % lo, '%.6f' % hi])
    with io.open(os.path.join(OUT, 'P3_counts.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('OK cells=%d small=%d benign_tasks=%d' % (len(cells), small, n_ben_task))


if __name__ == '__main__':
    main()
