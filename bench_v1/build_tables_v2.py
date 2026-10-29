"""把 RECAL64_raw.jsonl 收成 table_tau_v2.csv / table_FP_v2.csv。

与 Step 2 的 build_tables.py 同一套选档规则（R1/R2/R3、同一 GRID、同一 Wilson 目标上界），
差别只有两点：出口换成 artifacts/*__REF.py、题数从 38 扩到 64。
这样 v1 与 v2 的差异就只反映"出口不同 + 题变多"，不掺方法差异。
"""
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402

RAW = os.path.join(HERE, 'RECAL64_raw.jsonl')
GRID = C.TAU_GRID
TARGET = C.WILSON_TARGET_UPPER
TAU_COLS = ['criterion', 'statistic', 'template', 'tau_star', 'rule', 'tau_basis_seeds',
            'n_tasks', 'n_trials_task', 'k_alarms_task', 'fp_task', 'wilson_hi_task',
            'n_batch_trials', 'k_batch', 'wilson_hi_batch',
            'n_uniq_trials', 'mean_stat', 'max_stat', 'budget_seeds', 'note']
FP_COLS = ['criterion', 'statistic', 'template', 'scope', 'tau', 'k_fp', 'n',
           'fp_hat', 'wilson_lo', 'wilson_hi', 'note']


def pick_tau(acc_task, acc_batch):
    for tau in GRID:
        k, n = acc_task[tau]
        if n and C.wilson(k, n)[1] <= TARGET:
            return tau, 'R1'
    if acc_batch:
        for tau in GRID:
            k0, n0 = acc_task[tau]
            k, n = acc_batch[tau]
            if n and k0 == 0 and C.wilson(k, n)[1] <= TARGET:
                return tau, 'R2'
    for tau in GRID:
        k0, n0 = acc_task[tau]
        if n0 and k0 == 0:
            return tau, 'R3'
    return None, 'none'


def counts(vals):
    return {t: (sum(1 for v in vals if v > t), len(vals)) for t in GRID}


def main():
    groups = defaultdict(list)
    bgroups = defaultdict(list)
    tpl_of = {}
    err = []
    seeds_of_purpose = defaultdict(set)     # {'task': {10}, 'batch': {100}}，从 raw 里读出来
    for line in open(RAW, encoding='utf-8'):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        key = (d['task_id'], d.get('template'))
        tpl_of[d['task_id']] = d['template']
        if d.get('error'):
            err.append((d['task_id'], d['purpose'], d['error'][-90:]))
            continue
        seeds_of_purpose[d['purpose']].add(int(d['seeds']))   # 标定口径从数据里取，不写死
        if d['purpose'] == 'task':
            for kk, v in (d.get('rel') or {}).items():
                groups[(kk.split('|')[0], kk.split('|')[1], d['template'])].append((d['task_id'], v))
        else:
            for kk, vs in (d.get('batches') or {}).items():
                bgroups[(kk.split('|')[0], kk.split('|')[1], d['template'])].append((d['task_id'], vs))

    # 同一题多个试验会重复计入 n；task 级按"试验"计数是对的（Step 2 也这么算）
    # 标定口径（τ* 是在"每次判定用多少种子"下标出来的）**从 raw 里推**，不写死。
    #   v1（Step 2）的 task 级试验是 100 种子；v2（本轮）是 10 种子 —— 照搬 v1 的标签会把
    #   "给别人抄的那一页"上的预算写错 10 倍，所以这里禁止常量。
    def one_seed(purpose):
        s = seeds_of_purpose.get(purpose) or set()
        assert len(s) == 1, 'raw 里 %s 级的 seeds 不唯一/缺失：%s —— 口径没法确定，停下' % (purpose, sorted(s))
        return s.pop()
    BASIS = {'task': one_seed('task'), 'batch': one_seed('batch')}
    RULE_LEVEL = {'R1': 'task', 'R3': 'task', 'R2': 'batch'}
    tau_rows, fp_rows = [], []
    for (crit, stat, tpl), pairs in sorted(groups.items()):
        by_task = defaultdict(list)
        for tid, v in pairs:
            by_task[tid].append(v)
        task_alarm = {t: (sum(1 for tid, vs in by_task.items() if vs and min(vs) > t),
                          sum(1 for vs in by_task.values() if vs)) for t in GRID}
        trials = [v for _, v in pairs]
        # **假精度闸（外部审计 P-11）**：确定式解（EOQ 的 q=√(2DS/H)、报童的分位数 q）在 10 个种子上
        # 给出**同一个数**，所以 `n_trials_task = 题数 × 10` 是"同一个数抄 10 遍"，
        # 按 60 次独立试验算 Wilson 上界会把"0/60 ⇒ 上界 6.0%"写成一句没有载体的一句话；
        # 真正独立的估计只有 6 个（题数），上界是 39%。
        uniq = {round(v, 12) for v in trials}
        determ = len(uniq) == 1
        det_c = next(iter(uniq)) if determ else None
        vacuous_placeholder = (crit != 'J1')      # J2/J3 的恒零都是单侧/范围检查，不是测量结果
        if determ:
            # 独立单元 = **题**（确定式解在同一题的 10 个种子上给出同一个数）
            acc_task = dict(task_alarm)
            if det_c != 0.0:
                tau, rule = None, 'R0_DET_NONZERO'
            elif vacuous_placeholder:
                # 恒零但理由是"定义"而不是"测量" ⇒ 单独一档，能被 `rule` 列过滤
                # （只写在 note 里等于没分档：note 是给人读的，下游按 rule 筛）
                tau, rule = GRID[0], 'R0_VACUOUS_INTERNAL'
            else:
                tau, rule = GRID[0], 'R0_DETERMINISTIC'
            # ⚠ 同样是"恒为 0"，**理由有两种**，note 必须分开写（2026-10-17 重标时才发现）：
            #   ① J1 的 eoq q/cost、newsvendor q —— 确定式闭式解，与随机流无关；
            #   ② J2 的 `J2c_busy` = `max(0, busy_frac − 1)` —— **单侧范围检查**，
            #      而 `min(N,c)/c ≤ 1`、`1−π₀ ≤ 1` 由**定义**成立 ⇒ 我们自己产的工件**永远不会**点火。
            #      这条只对**外部工件**（模型可能把忙度算成 >1，例如忘了除 c）有价值，
            #      所以它**不许**被算进"守恒律全部通过"那一栏，写论文时要单列为"越界检查"。
            vacuous = (crit != 'J1')
        else:
            acc_task = counts(trials)
            tau, rule = None, None
        bpairs = [v for tid, vs in bgroups.get((crit, stat, tpl), []) for v in vs]
        acc_batch = counts(bpairs) if bpairs else None
        if not determ:
            tau, rule = pick_tau(acc_task, acc_batch)
        k0, n0 = acc_task[GRID[0]]
        # 这条断言就是本该拦住"11 个报警 / 6 题"那种读法的：报警数不可能超过试验数
        assert k0 <= n0, (crit, stat, tpl, k0, n0)
        kb, nb = (acc_batch[GRID[0]] if acc_batch else ('', ''))
        if not determ:
            note = ''
        elif vacuous:
            # note 里的理由必须**按这格的实现写**，不能整族套一句"忙度由定义 ≤1"。
            # 上一版就是这么错的：`J0e`（窗口对调用参数的区间检查）也落进这一档，
            # 却被注明成"单侧范围检查 max(0,busy_frac−1)" ⇒ 那句话对它根本不成立。
            if stat == 'J2c_busy':
                why = ('忙度由定义 ≤1（`J2c=max(0,busy_frac−1)`），'
                       '只能抓外部工件把忙度算超 1（如忘除服务台数 c）')
            elif stat == 'J0e_win_invocation':
                why = ('区间检查：`win×h(runtime_units)` 落在调用参数允许的区间内 ⇒ 我方工件恒为 0，'
                       '只有"自报窗口跑出可行域"才点火')
            else:
                why = '恒为 0 的理由来自该判据的定义（**未逐条登记**，要去 criteria 实现里核）'
            note = ('R0_VACUOUS_INTERNAL：这格恒不点火，理由：%s。'
                    '参照件 %d 个读数全为 %.5g ⇒ **不得计入"守恒律全部通过"这类独立证据计数**，'
                    '论文里要单列为越界/区间检查' % (why, n0, det_c))
        else:
            note = ('DETERMINISTIC：确定式解，%d 个读数是同一个数(%.5g)抄 %d 遍；'
                    '独立估计=题数 %d ⇒ Wilson 上界按 %d 算，**不许写成"0/60、上界 6%%"**；'
                    '样本预算轴对这一格不适用' % (n0, det_c, BASIS['task'], len(by_task), len(by_task)))
        tau_rows.append(dict(criterion=crit, statistic=stat, template=tpl,
                             tau_star=('%.3f' % tau if tau else 'NONE'), rule=rule,
                             tau_basis_seeds=BASIS[RULE_LEVEL.get(rule, 'task')],
                             n_tasks=len(by_task), n_trials_task=n0, k_alarms_task=k0,
                             fp_task=('%.4f' % (k0 / n0) if n0 else ''),
                             wilson_hi_task=('%.4f' % C.wilson(k0, n0)[1] if n0 else ''),
                             n_batch_trials=nb if bpairs else '',
                             k_batch=kb if bpairs else '',
                             wilson_hi_batch=('%.4f' % C.wilson(kb, nb)[1] if bpairs else ''),
                             # ⚠ `max_stat` 原来写 %.5f：`md1/J3a` 的真读数在 2.5e-7~4.25e-6 之间
                             #    （60 个**互不相同**的值），五位小数全打印成 0.00000 ⇒
                             #    自检第 12 项把这条合法格当成"假精度"报了 FAIL。
                             #    改：① 数值用 %.6g 不塌缩；② 另存 `n_uniq_trials`，
                             #    判"恒为同一个数"要看唯一值数，不能看打印出来的小数。
                             n_uniq_trials=len(uniq),
                             mean_stat=('%.6g' % (sum(trials) / len(trials))),
                             max_stat=('%.6g' % max(trials)),
                             budget_seeds=BASIS['task'], note=note))
        for t in GRID:
            k, n = acc_task[t]
            lo, hi = C.wilson(k, n) if n else (float('nan'), float('nan'))
            fp_rows.append(dict(criterion=crit, statistic=stat, template=tpl,
                                scope=('task_deterministic' if determ else 'task'),
                                tau=('%g' % t), k_fp=k, n=n, fp_hat=('%.6f' % (k / n) if n else ''),
                                wilson_lo=('%.6f' % lo), wilson_hi=('%.6f' % hi),
                                note=('EXCLUDED_FROM_FP:' + note if determ else '')))
    with open(os.path.join(HERE, 'table_tau_v2.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=TAU_COLS)
        w.writeheader()
        w.writerows(tau_rows)
    with open(os.path.join(HERE, 'table_FP_v2.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FP_COLS)
        w.writeheader()
        w.writerows(fp_rows)
    with open(os.path.join(HERE, 'RECAL64_ERRORS.md'), 'w', encoding='utf-8') as f:
        f.write('# 重标过程中的失败观测（%d 条）\n\n' % len(err))
        for e in err[:60]:
            f.write('- %s %s %s\n' % e)
    print('tau 行=%d  fp 行=%d  错误行=%d  覆盖题数=%d'
          % (len(tau_rows), len(fp_rows), len(err), len(tpl_of)))


# （已删）SEEDS_LABEL 是写死的常量映射，且是从 v1 照搬的 —— v1 的 task 级试验=100 种子、
# v2 的 task 级试验=10 种子，照搬会把 55 行的预算标错 10 倍。现在由 BASIS 从 raw 推导。

if __name__ == '__main__':
    main()
