# -*- coding: utf-8 -*-
"""全 64 注入的汇总包装：不覆盖 R10c 的 MUTANT_SUMMARY_R10c.md。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import summarize_matrix_v2 as S  # noqa: E402

S.MUT = os.path.join(HERE, 'mutants_all64.jsonl')
S.BEN = os.path.join(HERE, 'BENIGN_PROOF_full64.csv')
os.environ['MM_TAGS_OUT'] = os.path.join(HERE, 'MUTANT_TAGS_full64.csv')
os.environ['MM_OUT'] = os.path.join(HERE, 'MUTANT_SUMMARY_full64.md')
sys.argv = ['summarize_matrix_v2.py',
            os.path.join(HERE, 'MUTANT_MATRIX_full64.shard*.csv')]
S.main()
