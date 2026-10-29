# -*- coding: utf-8 -*-
"""把 2→4 的四片矩阵合成一个 skip 清单，供 2→6 只补新 342 件。"""
import csv, glob, io, os
HERE = os.path.dirname(os.path.abspath(__file__))
SIX = HERE
TWO4 = os.path.join(os.path.dirname(HERE), 'two_to_four')
files = sorted(glob.glob(os.path.join(TWO4, 'MUTANT_MATRIX_2to4.shard[0-9].csv')))
files = [f for f in files if '.triggers.' not in os.path.basename(f)]
assert len(files) == 4, files
out = os.path.join(TWO4, 'MUTANT_MATRIX_2to4_all.csv')
hdr = None
n = 0
with io.open(out, 'w', encoding='utf-8', newline='') as fh:
    wr = None
    for f in files:
        rd = csv.DictReader(io.open(f, encoding='utf-8'))
        if hdr is None:
            hdr = rd.fieldnames
            wr = csv.DictWriter(fh, fieldnames=hdr)
            wr.writeheader()
        for r in rd:
            wr.writerow(r); n += 1
print('wrote', out, 'rows', n)
assert n == 750, n
