"""两张 τ\\* 表的逐格对照：`旧表 新表` —— 回答"主矩阵要不要因为重标而重跑"。

为什么这是一道闸而不是"看一眼"：主表每一格的 `fired_*` 是用 τ\\* 算的，
所以只要 τ\\* 换档（0.010 → 0.020 之类），已跑完的 346 件就得重跑。
反过来，若 `τ*` 与选档规则 `rule` **逐格不变**、只有 `mean_stat/max_stat/fp/wilson` 这些
描述量随新引擎换值，那么已存的 `rel` 与 `fired_*` 仍然成立，不必重跑（省 4 小时）。

退出码：0 = τ\\* 与 rule 全同（矩阵可续用）；1 = 有任何一格换档（矩阵必须重跑）。
"""
import csv
import io
import os
import sys

KEY = ('criterion', 'statistic', 'template')


def load(p):
    rows = list(csv.DictReader(io.open(p, encoding='utf-8')))
    if not rows or set(KEY) - set(rows[0].keys()):
        raise SystemExit('%s 不像 τ* 表（缺 %s）' % (p, KEY))
    out = {}
    for r in rows:
        k = tuple(r[x] for x in KEY)
        if k in out:
            raise SystemExit('%s 里重复键 %s ⇒ 两张表并成一张了？' % (p, k))
        out[k] = r
    return out


def main():
    if len(sys.argv) != 3:
        raise SystemExit('用法：diff_tau_tables.py 旧表.csv 新表.csv')
    a, b = load(sys.argv[1]), load(sys.argv[2])
    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    tau_chg, rule_chg, desc_chg, basis_chg = [], [], [], []
    for k in sorted(set(a) & set(b)):
        if a[k]['tau_star'] != b[k]['tau_star']:
            tau_chg.append((k, a[k]['tau_star'], b[k]['tau_star']))
        if a[k].get('rule') != b[k].get('rule'):
            rule_chg.append((k, a[k].get('rule'), b[k].get('rule')))
        if a[k].get('tau_basis_seeds') != b[k].get('tau_basis_seeds'):
            basis_chg.append((k, a[k].get('tau_basis_seeds'), b[k].get('tau_basis_seeds')))
        if any(a[k].get(c) != b[k].get(c) for c in
               ('mean_stat', 'max_stat', 'fp_task', 'wilson_hi_task', 'n_trials_task', 'note')):
            desc_chg.append(k)
    print('旧 %d 行 / 新 %d 行；共同 %d；只旧 %d；只新 %d' % (
        len(a), len(b), len(set(a) & set(b)), len(only_a), len(only_b)))
    print('τ* 换档：%d 格 ｜ 选档规则变：%d 格 ｜ tau_basis_seeds 变：%d 格 ｜ 描述量变：%d 格' % (
        len(tau_chg), len(rule_chg), len(basis_chg), len(desc_chg)))
    for k, x, y in tau_chg[:12]:
        print('   τ* 变 %s：%s → %s' % (k, x, y))
    for k, x, y in rule_chg[:12]:
        print('   rule 变 %s：%s → %s' % (k, x, y))
    for k, x, y in basis_chg[:12]:
        print('   预算变 %s：%s → %s' % (k, x, y))
    if only_a:
        print('   只旧：', only_a[:8])
    if only_b:
        print('   只新：', only_b[:8])
    # ⚠ 只新（键变多）**不**要求重跑：加一条判据（如 J0）会让表多出行，而已跑完的矩阵
    #    每格的 rel/fired 不受影响。把它和"τ* 换档"混成一个 FAIL，就会把 4 小时机时
    #    花在一个根本不存在的矛盾上 —— 与 check_recal_currency 里"新增键当 DRIFT"同族。
    ok = not tau_chg and not basis_chg and not only_a
    print('%s ⇒ %s' % ('PASS' if ok else 'FAIL',
                       '主矩阵的 rel 与 fired_* 可续用，不必重跑（只描述量/选档标签换值）'
                       if ok else '有格 τ* 换档、预算变了、或**旧格被删** ⇒ 主矩阵必须重跑，否则判定与阈值不同源'))
    if only_b and ok:
        print('   [WARN] 表新增了 %d 行（新判据/新模板，例 %s）⇒ 不影响既有格，但矩阵里没有它们的列，'
              '要用就得单独跑那一判据，别顺手说成"主表已含 J0"' % (len(only_b), only_b[:3]))
    if rule_chg and ok:
        # ⚠ `rule` 变但 `tau_star` 不变，**不**要求重跑：矩阵里的 `fired_*` 是按 τ* 数值算的，
        #    与选档标签无关。今晚这一条会真的出现——P-11 把 3 个零方差格从 R1/R3 改标 R0_DETERMINISTIC，
        #    若把 rule 变化也当阻断，就会误判成"主矩阵要重跑 4 小时"。
        print('   [WARN] 选档标签变了 %d 格（τ* 没变 ⇒ 不影响 fired_*，只影响"这格为什么选这档"那句话）：%s'
              % (len(rule_chg), rule_chg[:4]))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
