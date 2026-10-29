"""核"标签两义"这条：我生成的 codes_used.tex 用了 CATALOG 的**默认** expected，
完全没看 `expected_by_tpl`。这里把 13 个码的默认值、模板覆盖值、以及正文 §3.2 的
五套先验标签词表一次摊出来，看有几处对不上。
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(HERE, 'simcore.py')
MT = os.path.join(os.path.dirname(HERE), 'paper_cscwd2027', 'main.tex')
USED = ['E01', 'E02', 'E03', 'E04', 'E07', 'E12', 'E14', 'E15', 'E16', 'E21', 'E24', 'E25', 'E43']

src = io.open(SIM, encoding='utf-8').read()
entries = {}
for m in re.finditer(r"^\s*'(E\d{2})':\s*dict\((.*?)\),\s*$", src, re.M | re.S):
    entries[m.group(1)] = m.group(2)
# 解析器自检：一条都没解析出来就往下印，等于把"我没读到"印成"它没有"。
assert len(entries) >= 30, 'PARSE FAILED: only %d CATALOG entries' % len(entries)

out = ['# 标签两义核对（codes_used.tex vs 正文 §3.2 vs simcore.CATALOG）', '']
out.append('- CATALOG 解析出 %d 个条目（正则 `^ \'EXX\': dict(` 到本行缩进的 `),`）。' % len(entries))
missing = [c for c in USED if c not in entries]
out.append('- 13 个码里没解析到的：%s' % (missing or '无'))
out.append('')
out.append('| 码 | 默认 expected | expected_by_tpl | 表里印的 | mmcK 上应为 |')
out.append('|----|--------------|-----------------|---------|------------|')

tab = io.open(os.path.join(os.path.dirname(HERE), 'paper_cscwd2027', 'codes_used.tex'),
              encoding='utf-8').read()
DECLMAP = {'blind': 'blind', 'detectable': 'detect.', 'weak': 'weak'}
nbad = 0
for c in USED:
    body = entries.get(c, '')
    d = re.search(r"\bexpected\s*=\s*'([^']*)'", body)
    d = d.group(1) if d else '?'
    bt = re.search(r"expected_by_tpl\s*=\s*\{([^}]*)\}", body, re.S)
    tpl = {}
    if bt:
        tpl = dict(re.findall(r"'(\w+)'\s*:\s*'([^']*)'", bt.group(1)))
    pr = re.search(r'%s & .* & (\S+) \\\\' % c, tab)
    printed = pr.group(1) if pr else '?'
    mmc = tpl.get('mmcK', d)
    bad = bool(tpl) and mmc != d
    if bad:
        nbad += 1
    out.append('| %s | %s | %s | %s | %s%s |'
               % (c, d, (json_s := (', '.join('%s:%s' % kv for kv in sorted(tpl.items())) or '—')),
                  printed, mmc, ' ⚠' if bad else ''))
out.append('')
out.append('- **默认值与 mmcK 上应有值不一致的码：%d 个**（上表带 ⚠ 的行）。' % nbad)
out.append('')
out.append('## CATALOG 里 expected 的全部取值')
vals = sorted({m.group(1) for b in entries.values() for m in
               [re.search(r"\bexpected\s*=\s*'([^']*)'", b)] if m})
out.append('- %s' % vals)
out.append('')
out.append('## 正文 §3.2 声明的先验标签词表（原文）')
mt = io.open(MT, encoding='utf-8').read()
seg = re.search(r'The theorem layer assigns one of five prior labels:(.{0,420})', mt, re.S)
out.append('- %s' % (seg.group(1).strip().replace('\n', ' ') if seg else 'NOT FOUND'))
out.append('')
out.append('## 表里 Decl. 列实际用到的词')
out.append('- %s' % sorted({m.group(1) for m in re.finditer(r'& (blind|detect\.|weak|collapse|no-inf\.) \\\\', tab)}))
io.open(os.path.join(HERE, 'LABELS_check.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('\n'.join(out[:8]))
print('...')
print('codes whose default != mmcK-specific: %d ; CATALOG expected values: %s' % (nbad, vals))
