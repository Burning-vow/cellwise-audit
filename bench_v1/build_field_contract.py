"""生成**逐题的字段契约**：`field_contract.csv`，每行 = task_id + 参照件实际报出的键。

为什么要有这个文件（这是今天腿 B 探针里最贵的一处错的根源）：
`gen_legB.build_prompt` 过去把**全局** FIELDS（arr/blk/p_loss/p_wait/busy_frac/per_seed_W…）
并到每道题的索要清单上。库存类题（eoq / newsvendor）根本没有排队观测量——
`eoq-01__REF.py` 自己只报 7 个键（q / cost / per_seed_q / 口径字段），
可 prompt 却向模型索要 W、L、p_wait、busy_frac，判分再用同一张全局清单去查缺字段。
后果有两层，第二层比第一层更糟：
  1. 正确只报 q/cost 的工件被判 FIELD_GAP ⇒ **字段齐全率被系统性压低**；
  2. 这些工件**根本没进"参照可比率"的分母** ⇒ 我到现在**没有**"8B 会不会算 EOQ/报童"的任何读数，
     却在报告里写了"参照可比率 0/20"，好像那是完整测量。

所以契约的正确来源不是我手写的清单，而是**参照件自己的输出键**——腿 A 判参照件用的就是这些键，
两个腿从此共用一个定义，不会再出现"同名两义"。

用法：~/miniconda3/python.exe build_field_contract.py
"""
import csv
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C                                    # noqa: E402

SEEDS, HOR = 10, 40000.0            # 与 τ* 标定预算一致（口径漂移一次就白跑）
ART = os.path.join(HERE, 'artifacts')
OUT = os.path.join(HERE, 'field_contract.csv')


def main():
    tasks = C.load_tasks()
    rows, t0 = [], time.time()
    for i, t in enumerate(tasks, 1):
        tid = t['task_id']
        path = os.path.join(ART, '%s__REF.py' % tid)
        if not os.path.exists(path):
            print('[%d/%d] %-14s NO_REF' % (i, len(tasks), tid), flush=True)
            continue
        obs, dt, note = C.run_artifact(path, SEEDS, HOR, 'none', 1, timeout=600)
        if obs is None:
            print('[%d/%d] %-14s RUN_FAIL %s' % (i, len(tasks), tid, str(note)[-80:]), flush=True)
            continue
        keys = sorted(obs.keys())
        # `truth_keys`（原名 judgeables，2026-10-17 改名）：真值里点了名的键。
        # ⚠ 它**不是**"可比率的分母"——里面含参照件不报的 `rho`/`eff_arrival`，而 τ* 表里也没有它们的行；
        # 谁把它当分母，就凭空多出一批"永远不可比"的格（外部审计 F-6 + 新规矩 20）。
        # 可比格的分母只有一个：`keys ∩ 标了 τ* 的统计量`（在 `legB_grade.contract_fields` 里算）。
        rows.append({'task_id': tid, 'template': t['template'], 'n_keys': len(keys),
                     'keys': ' '.join(keys),
                     'truth_keys': ' '.join(sorted((t.get('truth_print') or {}).keys())),
                     'basis_seeds': int(SEEDS), 'basis_horizon': HOR})
        print('[%d/%d] %-14s n_keys=%d %.0fs' % (i, len(tasks), tid, len(keys), dt), flush=True)

    # 旧契约留一份带时间戳的副本（规矩 15：复查写新文件，别把上一轮的证据覆盖掉）
    if os.path.exists(OUT):
        import shutil
        bak = OUT.replace('.csv', '.pre_%s.csv' % time.strftime('%m%d_%H%M'))
        if not os.path.exists(bak):
            shutil.copy2(OUT, bak)
            print('[备份] 旧契约 → %s' % os.path.basename(bak))
    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['task_id', 'template', 'n_keys', 'keys',
                                         'truth_keys', 'basis_seeds', 'basis_horizon'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    by_tpl = {}
    for r in rows:
        by_tpl.setdefault(r['template'], set()).add(r['n_keys'])
    print('\n%d/%d 题写入 %s，用时 %.1f min' % (len(rows), len(tasks), OUT, (time.time() - t0) / 60))
    print('每模板键数：' + json.dumps({k: sorted(v) for k, v in sorted(by_tpl.items())},
                                      ensure_ascii=False))
    missing = [t['task_id'] for t in tasks
               if t['task_id'] not in {r['task_id'] for r in rows}]
    assert not missing, '有题没生成契约（%d 题缺）：%s ⇒ 不许带缺口去跑腿 B' % (
        len(missing), ','.join(missing))

    # 出生活闸：新契约必须与 τ* 表自洽（就是 `legB_grade.contract_fields` 里那条 G1）。
    # 放在这里而不是只放判分那头：标定表多写一行不可比的统计量，**产契约时**就该炸，
    # 而不是等腿 B 跑到某一格才发现"这格永远不可比"。
    import legB_grade as LG
    LG._CONTRACT.clear()
    LG.TAU_CSV = TAU_FOR_CHECK = os.environ.get('SC_TAU_CSV') or os.path.join(HERE, 'table_tau_v2.csv')
    for t in tasks:
        LG.contract_fields(t, 'build-time 自洽检查')
    print('契约自洽检查通过：%d 题的 τ* 统计量全部落在参照件实际报出的键里（τ* 表=%s）'
          % (len(tasks), os.path.basename(TAU_FOR_CHECK)))


if __name__ == '__main__':
    main()
