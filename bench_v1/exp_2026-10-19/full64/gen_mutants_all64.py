# -*- coding: utf-8 -*-
"""全 64 题注入：复用 make_mutants 的模板，只把 plan_rows 的采样换成“所有题 × 所有适用错型”。

- 不修改 make_mutants.py / simcore.py / artifacts 现有文件。
- 已存在的 REF/变异件跳过；只补缺失件。
- 元数据写 exp_2026-10-19/full64/mutants_all64.jsonl（不覆盖 mutants.jsonl）。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))  # bench_v1
sys.path.insert(0, BENCH)
import simcore as SC  # noqa: E402
import make_mutants as MM  # noqa: E402

OUTDIR = HERE
OUT_MUT = os.path.join(OUTDIR, 'mutants_all64.jsonl')
ART = MM.ART
UNITS = {'newsvendor': '天，需求按天', 'eoq': '年'}


def plan_all():
    refs = [(t['task_id'], t['template'], 'REF') for t in MM.tasks()]
    rows = []
    for t in MM.tasks():
        tpl = t['template']
        for et in sorted(SC.CATALOG):
            if tpl not in SC.CATALOG[et]['applies']:
                continue
            rows.append((t['task_id'], tpl, et))
    return refs, rows


def main():
    refs, rows = plan_all()
    n_new = 0
    for tid, tpl, et in refs + rows:
        fn = os.path.join(ART, MM.artifact_name(tid, et))
        if os.path.exists(fn):
            continue
        if et == 'REF':
            body = MM.REF_TMPL.format(tid=tid, tpl=tpl, units=UNITS.get(tpl, '小时'),
                                      name=os.path.basename(fn))
        else:
            c = SC.CATALOG[et]
            hook, hval = list(SC.ERRORS[et].items())[0]
            body = MM.MUT_TMPL.format(tid=tid, et=et, short=c['short'], fam=c['family'],
                                      exp=MM.expected_for(et, tpl), theory=c['theory_ref'],
                                      hook=hook, hval=hval, name=os.path.basename(fn))
        with io.open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write(body)
        n_new += 1
    with io.open(OUT_MUT, 'w', encoding='utf-8') as f:
        for tid, tpl, et in rows:
            c = SC.CATALOG[et]
            hook, hval = list(SC.ERRORS[et].items())[0]
            f.write(json.dumps(dict(
                task_id=tid, template=tpl, error_type=et, family=c['family'],
                artifact_path='bench_v1/artifacts/' + MM.artifact_name(tid, et),
                change='%s | 单点注入 hook %s=%s | 与 %s__REF.py 的唯一代码差' % (
                    c['short'], hook, hval, tid),
                expected=MM.expected_for(et, tpl), theory_ref=c['theory_ref']),
                ensure_ascii=False) + '\n')
    per = {}
    for tid, tpl, et in rows:
        per[tpl] = per.get(tpl, 0) + 1
    print('refs=%d mutants=%d total=%d new_files=%d' % (len(refs), len(rows), len(refs) + len(rows), n_new))
    print('per-template=%s' % json.dumps(per, sort_keys=True, ensure_ascii=False))
    print('mutants_all64 ->', OUT_MUT)


if __name__ == '__main__':
    main()
