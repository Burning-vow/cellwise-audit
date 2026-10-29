# -*- coding: utf-8 -*-
"""全 64 注入的定理对账包装：用 full64 矩阵，不覆盖 R10c 的 UNDETECTABILITY_MATRIX.md。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import build_undetectability_matrix as B  # noqa: E402

B.MUT = os.path.join(HERE, 'mutants_all64.jsonl')
B.OUT = os.path.join(HERE, 'UNDETECTABILITY_MATRIX_full64.md')
PAT = os.path.join('exp_2026-10-19', 'full64', 'MUTANT_MATRIX_full64.shard*.csv')


def pick_full64():
    files, rows = B.matrix_rows(PAT)
    arts = {(r['task_id'], r['error_type']) for r in rows}
    n_mut = len({a for a in arts if a[1] != 'REF'})
    return PAT, 'full64', files, rows, n_mut, n_mut


B.pick_matrix = pick_full64
B.main()
