# -*- coding: utf-8 -*-
"""从 full64 工件池里选 2→4 的 40 题 / 750 件。

排队模板：按 rho 排序取 ts[0], ts[1], ts[-2], ts[-1]（当前 2 是 ts[0], ts[-1]；加次低/次高）。
库存模板：eoq/newsvendor 全 6 题不变。
不生成新工件；只从 mutants_all64.jsonl 里筛行。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import simcore as SC  # noqa: E402

SRC = os.path.join(os.path.dirname(HERE), 'full64', 'mutants_all64.jsonl')
OUT = os.path.join(HERE, 'mutants_2to4.jsonl')
TASKS = {t['task_id']: t for t in SC.load_tasks()}
BY = {}
for t in TASKS.values():
    BY.setdefault(t['template'], []).append(t)
SEL = set()
for tpl in ('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'):
    ts = sorted(BY[tpl], key=SC.rho_of)
    pick = [ts[0], ts[1], ts[-2], ts[-1]]
    SEL.update(t['task_id'] for t in pick)
    print(tpl, 'pick', [t['task_id'] for t in pick], 'rho', ['%.3f' % SC.rho_of(t) for t in pick])
for tpl in ('eoq', 'newsvendor'):
    SEL.update(t['task_id'] for t in BY[tpl])
rows = [json.loads(l) for l in io.open(SRC, encoding='utf-8') if l.strip()]
sel = [m for m in rows if m['task_id'] in SEL]
with io.open(OUT, 'w', encoding='utf-8') as f:
    for m in sel:
        f.write(json.dumps(m, ensure_ascii=False) + '\n')
from collections import Counter
print('tasks=%d mutants=%d expected=%s' % (len(SEL), len(sel), dict(Counter(m['expected'] for m in sel))))
print('out ->', OUT)
assert len(SEL) == 40 and len(sel) == 750, (len(SEL), len(sel))
