# -*- coding: utf-8 -*-
"""从 full64 工件池选 4→6：排队模板 6 题 + eoq/newsvendor 各 6 题 = 54 题 / 1092 件。

排队：按 rho 排序取 ts[0],ts[1],ts[2],ts[-3],ts[-2],ts[-1]（当前 2→4 的 4 题 + 次两端各 1）。
库存：全 6 题不变。不生成新工件，只筛 mutants_all64.jsonl。
"""
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import simcore as SC  # noqa: E402

SRC = os.path.join(os.path.dirname(HERE), 'full64', 'mutants_all64.jsonl')
OUT = os.path.join(HERE, 'mutants_2to6.jsonl')
TASKS = {t['task_id']: t for t in SC.load_tasks()}
BY = {}
for t in TASKS.values():
    BY.setdefault(t['template'], []).append(t)
SEL = set()
for tpl in ('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'):
    ts = sorted(BY[tpl], key=SC.rho_of)
    pick = [ts[0], ts[1], ts[2], ts[-3], ts[-2], ts[-1]]
    SEL.update(t['task_id'] for t in pick)
    print(tpl, 'pick', [t['task_id'] for t in pick], 'rho', ['%.3f' % SC.rho_of(t) for t in pick])
for tpl in ('eoq', 'newsvendor'):
    SEL.update(t['task_id'] for t in BY[tpl])
rows = [json.loads(l) for l in io.open(SRC, encoding='utf-8') if l.strip()]
sel = [m for m in rows if m['task_id'] in SEL]
with io.open(OUT, 'w', encoding='utf-8') as f:
    for m in sel:
        f.write(json.dumps(m, ensure_ascii=False) + '\n')
print('tasks=%d mutants=%d expected=%s' % (len(SEL), len(sel), dict(Counter(m['expected'] for m in sel))))
print('out ->', OUT)
assert len(SEL) == 54 and len(sel) == 1092, (len(SEL), len(sel))
