# -*- coding: utf-8 -*-
"""补跑剩余缺失件：8 份互斥 rem 文件 -> shard5..12。

用法：python run_missing_more.py i/8
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import run_mutant_matrix as R  # noqa: E402
import criteria as C  # noqa: E402

_orig_run_artifact = C.run_artifact


def _run_artifact(path, seeds, horizon, pert='none', seed_start=1, timeout=300):
    return _orig_run_artifact(path, seeds, horizon, pert, seed_start, timeout=timeout)


C.run_artifact = _run_artifact

if len(sys.argv) != 2 or '/' not in sys.argv[1]:
    raise SystemExit('用法：run_missing_more.py i/8')
i, n = [int(x) for x in sys.argv[1].split('/')]
if not (1 <= i <= n):
    raise SystemExit('分片号越界')
R.MUT = os.path.join(HERE, 'mutants_missing_full64.rem%d.jsonl' % i)
R.SEEDS = 10
R.HOR = 40000.0
out = os.path.join(HERE, 'MUTANT_MATRIX_full64.shard%d.csv' % (4 + i))
log = io.open(os.path.join(HERE, 'log_shard%d.txt' % (4 + i)),
              'w', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log
sys.argv = ['run_mutant_matrix.py', '--out=' + out, '--shard=1/1']
R.main()
