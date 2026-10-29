# -*- coding: utf-8 -*-
"""补跑 full64 缺失件：输出 shard5..8，避免覆盖 1..4。

用法：python run_missing_full64.py i/4   (i=1..4 -> shard 5..8)
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import run_mutant_matrix as R  # noqa: E402
import criteria as C  # noqa: E402

# 补跑里混入了个别病态工件（实测一件 >14 min 仍在算）。主表正常件 <2 min；
# 给补跑单件 300 s 硬超时，超时写成 CRASH 行，别让它拖住整晚。
_orig_run_artifact = C.run_artifact


def _run_artifact(path, seeds, horizon, pert='none', seed_start=1, timeout=300):
    return _orig_run_artifact(path, seeds, horizon, pert, seed_start, timeout=timeout)


C.run_artifact = _run_artifact

if len(sys.argv) != 2 or '/' not in sys.argv[1]:
    raise SystemExit('用法：run_missing_full64.py i/4')
i, n = [int(x) for x in sys.argv[1].split('/')]
if not (1 <= i <= n):
    raise SystemExit('分片号越界')
R.MUT = os.path.join(HERE, 'mutants_missing_full64.part%d.jsonl' % i)
R.SEEDS = 10
R.HOR = 40000.0
out = os.path.join(HERE, 'MUTANT_MATRIX_full64.shard%d.csv' % (4 + i))
log = io.open(os.path.join(HERE, 'log_shard%d.txt' % (4 + i)),
              'w', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log
sys.argv = ['run_mutant_matrix.py', '--out=' + out, '--shard=1/1']
R.main()
