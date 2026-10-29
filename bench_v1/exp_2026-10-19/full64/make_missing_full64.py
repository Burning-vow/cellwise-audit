# -*- coding: utf-8 -*-
"""找出 full64 现有分片矩阵漏跑的工件，写成独立清单。

根因：run_mutant_matrix 在每个分片进程里先按**该分片自己的** OUT 做 done_keys 过滤，
再按 i/n 切片。各分片 skip 集不同 ⇒ 过滤后的序列错位 ⇒ 有人重复、有人从未被切到。
本脚本只读现有矩阵，按 (task_id,error_type) 做全局差集；不修改原分片。
"""
import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MUT = os.path.join(HERE, 'mutants_all64.jsonl')
OUT = os.path.join(HERE, 'mutants_missing_full64.jsonl')
PAT = os.path.join(HERE, 'MUTANT_MATRIX_full64.shard[0-9].csv')


def main():
    have = set()
    for p in glob.glob(PAT):
        with open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r.get('task_id') and r.get('error_type'):
                    have.add((r['task_id'], r['error_type']))
    ms = [json.loads(l) for l in open(MUT, encoding='utf-8') if l.strip()]
    missing = [m for m in ms if (m['task_id'], m['error_type']) not in have]
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        for m in missing:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
    print('mutants=%d have=%d missing=%d -> %s' % (len(ms), len(have), len(missing), OUT))
    by = {}
    for m in missing:
        by[m['template']] = by.get(m['template'], 0) + 1
    print('missing per template: %s' % json.dumps(by, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    main()
