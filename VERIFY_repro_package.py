# -*- coding: utf-8 -*-
"""复现包完整性核对（独立于 BUILD 脚本的第二条出口）。

1) 逐条按 MANIFEST.csv 重算 sha256 与字节，对不上就报；
2) 列出"包里有但 MANIFEST 没记"的文件（跑过测试就会长出来：aux/log/bbl、artifacts/_selfcheck/ 等）；
3) 再扫一遍密钥字面量；
4) 断言不该进来的目录确实没进来。
退出码非 0 = 不干净。只读，不改包。
"""
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 脚本放在包外（项目根）时核对兄弟目录；被复制进包后就地核对自身所在目录
DST = HERE if os.path.isfile(os.path.join(HERE, 'MANIFEST.csv')) else os.path.join(HERE, 'repro_package_cscwd2027')
LIT_KEY = re.compile(r'sk-[A-Za-z0-9]{16,}')
BAD_DIR = ('__pycache__', 'calib_ref', '_archive_superseded')


def main():
    man_path = os.path.join(DST, 'MANIFEST.csv')
    rows = list(csv_rows(man_path))
    bad_hash, missing = [], []
    declared = set()
    for r in rows:
        declared.add(r['target_path'])
        p = os.path.join(DST, *r['target_path'].split('/'))
        if not os.path.isfile(p):
            missing.append(r['target_path'])
            continue
        data = io.open(p, 'rb').read()
        if len(data) != int(r['bytes']):
            bad_hash.append('%s 字节 %d≠%d' % (r['target_path'], len(data), int(r['bytes'])))
        elif hashlib.sha256(data).hexdigest()[:16] != r['sha256_16']:
            bad_hash.append(r['target_path'] + ' sha256 不符')
    extra = []
    for dirpath, dirnames, filenames in os.walk(DST):
        dirnames[:] = [d for d in dirnames if d != '.git']
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), DST).replace('\\', '/')
            if rel == 'MANIFEST.csv':       # 清单自身写在收集完之后，不算残留
                continue
            if rel not in declared:
                extra.append(rel)
    leaked = [p for p in sorted(declared) + extra
              if p.lower().endswith(('.py', '.md', '.txt', '.csv', '.jsonl', '.sh', '.tex', '.bib', '.json'))
              and os.path.isfile(os.path.join(DST, *p.split('/')))
              and LIT_KEY.search(io.open(os.path.join(DST, *p.split('/')), 'rb').read().decode('utf-8', 'ignore'))]
    baddir = [d for dirpath, dirnames, _ in os.walk(DST) for d in dirnames
              if d in BAD_DIR or d.startswith('_selfcheck')]
    out = io.open(os.path.join(os.path.dirname(DST), 'VERIFY_repro_package.md'), 'w',
                  encoding='utf-8', newline='\n')
    out.write('# 复现包完整性核对\n\n')
    out.write('- MANIFEST 条数 **%d**；缺失 %d；哈希/字节不符 %d\n'
              '- 包内多出的文件（测试残留）**%d** 个\n'
              '- 密钥字面量命中 **%d**；不该进来的目录 **%d** 个\n\n'
              % (len(rows), len(missing), len(bad_hash), len(extra), len(leaked), len(baddir)))
    for name, lst in (('缺失', missing), ('哈希不符', bad_hash), ('密钥', leaked), ('坏目录', baddir)):
        for x in lst[:20]:
            out.write('- [%s] %s\n' % (name, x))
    out.write('\n## 包内多出的文件（前 40）\n\n')
    for x in sorted(extra)[:40]:
        out.write('- %s\n' % x)
    ok = not (missing or bad_hash or leaked or baddir)
    out.write('\n**判决：%s**\n' % ('核心项全干净' if ok else '不干净，先处理上面列的'))
    out.close()
    print('VERIFY files=%d missing=%d badhash=%d extra=%d leaked=%d baddir=%d ok=%s'
          % (len(rows), len(missing), len(bad_hash), len(extra), len(leaked), len(baddir), ok))
    return 0 if ok else 1


def csv_rows(path):
    import csv
    with io.open(path, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            yield r


if __name__ == '__main__':
    sys.exit(main())
