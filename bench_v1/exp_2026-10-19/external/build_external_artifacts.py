# -*- coding: utf-8 -*-
"""生成 P5 外部题的 REF 与代表错型工件。

- 工件落在 bench_v1/artifacts_external/，不碰主 artifacts。
- 每个工件只是 simcore_ext.main(tid, et) 的一行入口；错型由 simcore.ERRORS 单点注入。
- 外部题不参与主表与 tau* 标定。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.abspath(os.path.join(HERE, '..', '..'))
if BENCH not in sys.path:
    sys.path.insert(0, BENCH)
import simcore as SC  # noqa: E402
import make_mutants as MM  # noqa: E402

TASKS = os.path.join(HERE, 'external_tasks.jsonl')
ART = os.path.join(BENCH, 'artifacts_external')
REFS_OUT = os.path.join(HERE, 'external_refs.jsonl')
MUT_OUT = os.path.join(HERE, 'external_mutants.jsonl')

REP_TYPES = ('E01', 'E02', 'E03', 'E24', 'E04', 'E25', 'E14', 'E21', 'E43')
# 库存侧代表码：2026-10-21 补，之前外部集 12 题里 eoq/newsvendor 两题只有参照件。
INV_TYPES = ('E31', 'E32', 'E33', 'E34', 'E35', 'E36', 'E37', 'E38', 'E42')

REF_TMPL = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 {tid}：参照件（{tpl}）。

真值来自 exp_2026-10-19/external/external_truth.py（独立闭式），
本文件只调用 simcore_ext 做仿真；不把 simcore 当外部真值。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('{tid}', 'REF')
'''

MUT_TMPL = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 {tid} / 错型 {et}：{short}

family={fam}  expected={exp}（跑实验之前声明）
theory_ref={theory}
注入点：simcore 的单个 hook —— {hook}={hval}（其余与 REF 完全一致）
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('{tid}', '{et}')
'''


def p5_boundary(tpl, et):
    if et in ('E01', 'E02', 'E43'):
        return 'static'
    if et == 'E25':
        return 'point'
    if et in ('E03', 'E24'):
        if tpl == 'mmcK':
            return 'open'
        return 'point'
    if et == 'E04':
        if tpl in ('mm1', 'mmc', 'jackson2'):
            return 'static'
        if tpl in ('md1', 'mh2'):
            return 'point'
        return 'open'
    if et in ('E14', 'E21'):
        return 'weak'
    return 'open'


def artifact_name(tid, et):
    return '%s__%s.py' % (tid, 'REF' if et == 'REF' else et)


def main():
    if not os.path.isdir(ART):
        os.makedirs(ART)
    tasks = [json.loads(l) for l in open(TASKS, encoding='utf-8') if l.strip()]
    refs, muts = [], []
    n_new = 0
    for t in tasks:
        tid, tpl = t['task_id'], t['template']
        fn = os.path.join(ART, artifact_name(tid, 'REF'))
        if not os.path.exists(fn):
            with io.open(fn, 'w', encoding='utf-8', newline='\n') as f:
                f.write(REF_TMPL.format(tid=tid, tpl=tpl))
            n_new += 1
        refs.append(dict(task_id=tid, template=tpl, error_type='REF',
                         artifact_path='bench_v1/artifacts_external/' + artifact_name(tid, 'REF')))
        for et in REP_TYPES + INV_TYPES:
            if tpl not in SC.CATALOG[et]['applies']:
                continue
            c = SC.CATALOG[et]
            hook, hval = list(SC.ERRORS[et].items())[0]
            exp = MM.expected_for(et, tpl)
            fn = os.path.join(ART, artifact_name(tid, et))
            if not os.path.exists(fn):
                with io.open(fn, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(MUT_TMPL.format(tid=tid, et=et, short=c['short'],
                                            fam=c['family'], exp=exp,
                                            theory=c['theory_ref'], hook=hook,
                                            hval=hval))
                n_new += 1
            muts.append(dict(task_id=tid, template=tpl, error_type=et,
                             family=c['family'], artifact_path='bench_v1/artifacts_external/' + artifact_name(tid, et),
                             change='%s | 单点注入 hook %s=%s | 与 %s__REF.py 的唯一代码差'
                                    % (c['short'], hook, hval, tid),
                             expected=exp, theory_ref=c['theory_ref'],
                             p5_boundary=p5_boundary(tpl, et)))
    with io.open(REFS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        for r in refs:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with io.open(MUT_OUT, 'w', encoding='utf-8', newline='\n') as f:
        for r in muts:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print('tasks=%d refs=%d mutants=%d new_files=%d' % (len(tasks), len(refs), len(muts), n_new))
    per = {}
    for m in muts:
        per[m['template']] = per.get(m['template'], 0) + 1
    print('per-template=%s' % json.dumps(per, sort_keys=True, ensure_ascii=False))


if __name__ == '__main__':
    main()
