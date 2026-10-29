"""核 FAIL-3：fig_cxk() 里写死的 4×(c,K) 数值，每一点到底是哪个 ρ？

做法：把 CXK_MATRIX.csv 里每个 (c,K,ρ) 的四格 |rel| 全列出来，
再拿图里那四个数去对，看唯一命中的是哪个 ρ。
对不上的点也照实印——那说明图里有点连 CSV 里都没有（手抄自更早一代）。
"""
import csv
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = {
    2: {2: (0.00009, 0.00067, 0.00009, 0.00067), 3: (0.00046, 0.00023, 0.00046, 0.00023),
        4: (0.00811, 0.01504, 0.00572, 0.01025), 6: (0.02392, 0.05144, 0.01557, 0.03360),
        8: (0.06712, 0.09313, 0.03963, 0.05742)},
    3: {3: (0.00056, 0.00051, 0.00056, 0.00051), 4: (0.00060, 0.00044, 0.00060, 0.00044),
        6: (0.00249, 0.01967, 0.00202, 0.01258), 8: (0.02184, 0.04507, 0.01357, 0.02845)},
    4: {4: (0.00005, 0.00092, 0.00005, 0.00092), 6: (0.00218, 0.00421, 0.00123, 0.00231),
        8: (0.00209, 0.01945, 0.00179, 0.01215)},
}
ORDER = ('E03/L', 'E03/W', 'E24/L', 'E24/W')

rows = list(csv.DictReader(io.open(os.path.join(HERE, 'CXK_MATRIX.csv'), encoding='utf-8', newline='')))
cells = {}
for r in rows:
    if r['etype'] == 'REF' or r['obs'] not in ('L', 'W'):
        continue
    cells.setdefault((int(r['c']), int(r['K']), round(float(r['rho']), 2)), {})[
        '%s/%s' % (r['etype'], r['obs'])] = abs(float(r['rel_truth']))

out = ['# FAIL-3 核对：图里每点实际对应哪个 ρ（`CXK_MATRIX.csv` 现算）', '']
out.append('图标题写的是 "The c×K boundary at ρ=0.8"。下表逐点回认。')
out.append('')
out.append('| c | K | 图里四点 | 唯一匹配的 ρ | 判 |')
out.append('|---|---|---------|-------------|---|')
nbad = 0
for c in sorted(FIG):
    for K in sorted(FIG[c]):
        want = FIG[c][K]
        hits = []
        for (cc, kk, rho), d in cells.items():
            if (cc, kk) != (c, K):
                continue
            got = tuple(round(d.get(k, -1), 5) for k in ORDER)
            if all(abs(g - w) < 1.5e-5 for g, w in zip(got, want)):
                hits.append(rho)
        tag = ('ρ=%s' % ('/'.join('%g' % h for h in sorted(hits)))) if hits else 'CSV 里找不到'
        ok = bool(hits) and all(abs(h - 0.8) < 1e-9 for h in hits)
        if not ok:
            nbad += 1
        out.append('| %d | %d | %s | %s | %s |'
                   % (c, K, ' '.join('%.5f' % v for v in want), tag,
                      '与标题一致' if ok else '**与标题 ρ=0.8 不符**'))
out.append('')
out.append('- 不符的点数：**%d / %d**' % (nbad, sum(len(v) for v in FIG.values())))
out.append('')
out.append('## 图里根本没有 ρ=0.4')
out.append('- `fig_cxk()` 的数据是写死的字典，不读 CSV ⇒ 重跑 `make_figs.py` 也补不出 ρ=0.4 那 12 格。')
avail = sorted({rho for (cc, kk, rho) in cells})
out.append('- CSV 现有负载：%s；图能表达的：只有一条未知混合。' % avail)
io.open(os.path.join(HERE, 'FAIL3_fig_provenance.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out[:6]))
print('...')
print('mismatched points = %d / %d' % (nbad, sum(len(v) for v in FIG.values())))
