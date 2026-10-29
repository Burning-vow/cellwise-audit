"""外部题集补库存变异件之后的验收：三件事，顺序不能反。

  (1) **回归闸**：新的整表 EXTERNAL_MATRIX.csv 里，与旧 4 片重叠的那 77 行，
      verdict / fired_n / fired_obs / match 必须逐行相同。
      不过就直接判"这次跑废了"，不去读新数字。
      （同一台引擎的逐位确定性已在 c×K 那轮证过：102/102 行 rel 全等。）
  (2) **新 9 行**：ext-eoq-01 / ext-newsvendor-01 上每件的实际 verdict，
      与 simcore.CATALOG 声明的 expected 对账。**对不上就照实报，不改声明凑数。**
  (3) **给正文的数**：现算 86 件 / 12 题，以及表 V 每一行的新计数
      （含新增的那一行"库存类，不属于 P1–P4 任何命题"）。
"""
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'bench_v1')
WHOLE = os.path.join(HERE, 'EXTERNAL_MATRIX.csv')
SIM = os.path.join(B1, 'simcore.py')
OUT = os.path.join(HERE, 'EXTERNAL_INV_CHECK.md')


def load(p):
    return list(csv.DictReader(io.open(p, encoding='utf-8', newline='')))


def main():
    if not os.path.exists(WHOLE):
        print('整表还没生成'); return 1
    whole = load(WHOLE)
    if len(whole) < 86:
        print('整表只有 %d 行，跑分还没完成（目标 86）' % len(whole))
        return 1
    old = []
    for f in sorted(os.listdir(HERE)):
        if f.startswith('EXTERNAL_MATRIX.shard') and f.endswith('.csv') and '.triggers.' not in f:
            old += load(os.path.join(HERE, f))

    def key(r):
        return (r['task_id'], r['error_type'])

    o = {key(r): r for r in old}
    n = {key(r): r for r in whole}
    L = ['# 外部题集补库存变异件：验收（run_external.py + 本脚本）', '']
    L.append('- 旧分片 %d 行 / %d 题；新整表 %d 行 / %d 题。'
             % (len(old), len({r['task_id'] for r in old}), len(whole),
                len({r['task_id'] for r in whole})))
    L.append('')
    L.append('## (1) 回归闸：旧 %d 行在新整表里必须逐行同判' % len(o))
    missing = [k for k in o if k not in n]
    FIELDS = ('verdict', 'fired_n', 'fired_obs', 'match')
    diff = [(k, f, o[k][f], n[k][f]) for k in o if k in n for f in FIELDS
            if (o[k].get(f) or '') != (n[k].get(f) or '')]
    L.append('- 旧行在新表里找不到：%d %s' % (len(missing), missing[:3] or ''))
    L.append('- **判定字段有差异的格：%d**' % len(diff))
    for k, f, a, b in diff[:10]:
        L.append('  - %s/%s 的 %s: 旧=%r 新=%r' % (k[0], k[1], f, a, b))
    gate = (not missing) and (not diff)
    L.append('- **回归闸：%s**' % ('PASS' if gate else 'FAIL'))
    if not gate:
        L.append('')
        L.append('> 只加题就改变旧判定 ⇒ 新数字不可用。先查为什么。')
        io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('\n'.join(L[:12]))
        return 1

    # ---------- (2) 新 9 行 ----------
    added = [k for k in n if k not in o]
    src = io.open(SIM, encoding='utf-8').read()
    decl = {}
    for m in re.finditer(r"^\s*'(E\d{2})':\s*dict\((.*?)\),\s*$", src, re.M | re.S):
        mm = re.search(r"\bexpected\s*=\s*'([^']*)'", m.group(2))
        decl[m.group(1)] = mm.group(1) if mm else '?'
    if decl.get('E01') == decl.get('E03'):
        L.append(''); L.append('- **解析器坏了（E01/E03 同一个 expected），本节的对账不算**')
    L.append('')
    L.append('## (2) 新增 %d 件（两个库存题）' % len(added))
    L.append('')
    L.append('| 题 | 码 | CATALOG 声明 | 实测 verdict | fired | 一致? |')
    L.append('|----|----|-------------|-------------|-------|-------|')
    disagree = []
    for k in sorted(added):
        r = n[k]
        d = decl.get(k[1], '?')
        exp_word = {'detectable': 'DETECTED', 'weak': 'DETECTED', 'blind': 'NOT_DETECTED'}.get(d, '?')
        ok = r['verdict'] == exp_word
        if not ok:
            disagree.append((k, d, r['verdict']))
        L.append('| %s | %s | %s | %s | %s | %s |'
                 % (k[0], k[1], d, r['verdict'], r['fired_n'], 'yes' if ok else '**NO**'))
    L.append('')
    L.append('- 与声明不一致：**%d 件** %s' % (len(disagree), disagree or ''))
    L.append('- 注：外部矩阵的 verdict 只有 DETECTED / NOT_DETECTED 两档，'
             '所以 weak 与 detectable 在这里都算 DETECTED；真要分档得回主矩阵口径。')

    # ---------- (3) 给正文的数 ----------
    muts = [json.loads(l) for l in io.open(os.path.join(HERE, 'external_mutants.jsonl'),
                                           encoding='utf-8') if l.strip()]
    refs = [json.loads(l) for l in io.open(os.path.join(HERE, 'external_refs.jsonl'),
                                           encoding='utf-8') if l.strip()]
    by_tmpl = {}
    for r in muts:
        by_tmpl[r['template']] = by_tmpl.get(r['template'], 0) + 1
    L.append('')
    L.append('## (3) 正文要用的数（现算，不抄）')
    L.append('- 变异件 **%d 件**，覆盖 **%d / %d 题**（题数按 external_refs.jsonl 现数）。'
             % (len(muts), len({r['task_id'] for r in muts}), len({r['task_id'] for r in refs})))
    L.append('- 逐模板：%s' % json.dumps(by_tmpl, ensure_ascii=False, sort_keys=True))
    det = sum(1 for r in whole if r['verdict'] == 'DETECTED')
    nod = sum(1 for r in whole if r['verdict'] == 'NOT_DETECTED')
    mat = sum(1 for r in whole if r['match'] == 'MATCH')
    L.append('- 整表判定：DETECTED %d、NOT_DETECTED %d；与声明 MATCH %d / %d'
             % (det, nod, mat, len(whole)))
    inv = [k for k in added]
    L.append('- 库存那 %d 件：DETECTED %d、NOT_DETECTED %d'
             % (len(inv), sum(1 for k in inv if n[k]['verdict'] == 'DETECTED'),
                sum(1 for k in inv if n[k]['verdict'] == 'NOT_DETECTED')))
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:6] + L[-9:]))
    print('wrote %s ; gate=PASS ; 与声明不一致 %d 件' % (os.path.basename(OUT), len(disagree)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
