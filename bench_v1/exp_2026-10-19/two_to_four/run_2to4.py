# -*- coding: utf-8 -*-
"""全 64 注入的矩阵分片包装：不改 run_mutant_matrix.py，只换 MUT/OUT/预算。

用法：python run_full64.py 1/4
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import run_mutant_matrix as R  # noqa: E402

if len(sys.argv) != 2 or '/' not in sys.argv[1]:
    raise SystemExit('用法：run_full64.py i/n')
shard = sys.argv[1]
i = int(shard.split('/')[0])
R.MUT = os.path.join(HERE, 'mutants_2to4.jsonl')
R.SEEDS = 10
R.HOR = 40000.0
out = os.path.join(HERE, 'MUTANT_MATRIX_2to4.shard%d.csv' % i)
log = io.open(os.path.join(HERE, 'log_2to4_shard%d.txt' % i), 'w', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log
sys.argv = ['run_mutant_matrix.py', '--out=' + out, '--shard=' + shard]
R.main()
