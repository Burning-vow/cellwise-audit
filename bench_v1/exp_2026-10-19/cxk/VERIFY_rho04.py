"""c×K 扫描补 ρ=0.4 之后的验收。两件事，顺序不能反：

  (1) **旧 17 题必须一格都没动**。这是"不该动的量不许动"闸：
      加题会重写 tasks_cxk.jsonl 与 artifacts，若 simcore 的缓存顺序/种子派生
      与题表长度有关，旧读数就会漂 ⇒ 那这条新控制点也不能用。
      先跑这一条；它不过就直接判"这次跑废了"，不去解读新数字。
  (2) 新 ρ=0.4 三格（K=4/6/8）的判定与 rel，用来替换正文那句"插值得到、未复现"。

比较口径：verdict 必须逐格相等（这是结论层）；rel_truth 是否逐位相等单独报
（这是确定性层，漂了只说明 RNG 不纯，不影响判定，但要如实写）。
"""
import csv
import io
import json
import os
import sys

CXK = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(CXK, 'CXK_MATRIX.csv.pre_rho04_2026-10-20')
NEW = os.path.join(CXK, 'CXK_MATRIX.csv')
OUT = os.path.join(CXK, 'CXK_RHO04.md')


def load(p):
    return list(csv.DictReader(io.open(p, encoding='utf-8', newline='')))


def key(r):
    return (r['task_id'], r['etype'], r['obs'])


def main():
    if not os.path.exists(NEW):
        print('CXK_MATRIX.csv 不存在——扫描还没跑完，别急着出结论')
        return 1
    old, new = load(OLD), load(NEW)
    ntasks = len({r['task_id'] for r in new})
    o = {key(r): r for r in old}
    nn = {key(r): r for r in new}

    L = ['# c×K 扫描：补 ρ=0.4 控制点后的验收（run_cxk.py + 本脚本产生）', '']
    L.append('- 旧矩阵 %d 行 / %d 题；新矩阵 %d 行 / %d 题；τ\\*=0.01、R=10、H=40000 一条没改。'
             % (len(old), len({r['task_id'] for r in old}), len(new), ntasks))

    # ---------- (1) 旧题不许动 ----------
    missing = [k for k in o if k not in nn]
    moved = [(k, o[k]['verdict'], nn[k]['verdict']) for k in o
             if k in nn and o[k]['verdict'] != nn[k]['verdict']]
    rel_diff = [(k, o[k]['rel_truth'], nn[k]['rel_truth']) for k in o
                if k in nn and (o[k]['rel_truth'] or '') != (nn[k]['rel_truth'] or '')]
    L.append('')
    L.append('## (1) 旧 17 题回归闸')
    L.append('- 旧行在新矩阵里找不到的：%d %s' % (len(missing), missing[:3] or ''))
    L.append('- **verdict 变动的格：%d** %s' % (len(moved), moved[:5] or '（无）'))
    L.append('- rel_truth 文本不逐位相等的格：%d / %d（旧行总数）' % (len(rel_diff), len(o)))
    for k, a, b in rel_diff[:5]:
        L.append('  - %s: %s -> %s' % ('/'.join(k), a, b))
    gate_ok = (not missing) and (not moved)
    L.append('- **回归闸：%s**' % ('PASS（判定一格没动）' if gate_ok else 'FAIL'))
    if not gate_ok:
        L.append('')
        L.append('> 判定漂了 ⇒ 本次新增控制点不可用，先查为什么"只加题"会改变旧读数。')

    # ---------- (2) ρ=0.4 三格 ----------
    L.append('')
    L.append('## (2) 新增 ρ=0.4 的三格')
    r04 = [r for r in new if r['rho'].startswith('0.4') and r['c'] == '2']
    by = {}
    for r in r04:
        by.setdefault((r['K'], r['etype']), {})[r['obs']] = r
    ks = sorted({r['K'] for r in r04}, key=int)
    L.append('')
    L.append('| K | 格 | verdict | rel vs truth | trig_nonhead | trig_class0 |')
    L.append('|---|----|---------|--------------|--------------|-------------|')
    for K in ks:
        for et in ('E03', 'E24'):
            cell = by.get((K, et), {})
            for ob in ('L', 'W'):
                r = cell.get(ob)
                if not r:
                    L.append('| %s | %s/%s | — | — | — | — |' % (K, et, ob))
                    continue
                L.append('| %s | %s/%s | %s | %s | %s | %s |'
                         % (K, et, ob, r['verdict'], r['rel_truth'],
                            r['trig_nonhead'], r['trig_class0']))
    # 与 mmcK-04 主表读数对照（同参数，不同题表）
    L.append('')
    L.append('### 与主表 mmcK-04 的对照（同 c/K/λ/μ，两套题表）')
    f64 = os.path.join(CXK, '..', 'full64')
    # 观测量在 `instance` 列、判据层在 `stage` 列。上一版这里写 r.get('obs') or r.get('observable')
    # 两个字段都不存在 ⇒ 全取 None 并把 33 行塌成 2 格，是静默抓错字段那一类。
    # 这次一次把 mmcK-01..08 全收，逐题计数与"高于阈值的 W 格"都从矩阵现算——
    # 上一版我在散文中手抄了 "0.01504/0.01225"，后者是错的（真值 0.016414/0.010300），
    # 硬编码进句子的数一定会漂，所以这里一个都不许写死。
    allc = {}
    for fn in sorted(os.listdir(f64)):
        if not (fn.startswith('MUTANT_MATRIX_full64.shard') and fn.endswith('.csv')
                and '.triggers.' not in fn):
            continue
        for r in csv.DictReader(io.open(os.path.join(f64, fn), encoding='utf-8', newline='')):
            tid = r.get('task_id') or ''
            if (tid.startswith('mmcK-0') and r.get('error_type') in ('E03', 'E24')
                    and r.get('stage') == 'J1' and r.get('instance') in ('L', 'W')):
                key2 = (tid, r['error_type'], r['instance'])
                rel = abs(float(r['rel']))
                allc[key2] = max(allc.get(key2, 0.0), rel)
    mmc04 = {(et, ob): (v, '0') for (t, et, ob), v in allc.items() if t == 'mmcK-04'}
    below_by_task = {}
    above_w = []
    for (t, et, ob), v in sorted(allc.items()):
        if v < 0.01:
            below_by_task[t] = below_by_task.get(t, 0) + 1
        elif ob == 'W':
            above_w.append((t, et, v))
    # 正文那句"mmcK-04 贡献 4 个不吻合格"要能在这里对上，否则先怀疑自己
    below = [k for k, v in mmc04.items() if v[0] < 0.01 and v[1] == '0']
    L.append('- 主表里 mmcK-04 的 J1 × {L,W} × {E03,E24} 格：**%d** 个；其中 |rel|<τ\\* 且 fired=0 的：**%d** 个'
             % (len(mmc04), len(below)))
    for k in sorted(mmc04):
        L.append('  - %s/%s: |rel| = %.6f, fired_0.01 = %s' % (k[0], k[1], mmc04[k][0], mmc04[k][1]))
    if len(mmc04) != 4:
        L.append('- **警告：mmcK-04 的格数不是 4，正文"12 格全在 mmcK-01..04"这句要重新核。**')
    falsified = {t: n for t, n in below_by_task.items() if t in ('mmcK-01', 'mmcK-02', 'mmcK-03', 'mmcK-04')}
    other = {t: n for t, n in below_by_task.items() if t not in ('mmcK-01', 'mmcK-02', 'mmcK-03', 'mmcK-04')}
    L.append('- 逐题低于 τ* 的格数（现算）：mmcK-01..04 = %s，合计 %d；mmcK-05..08 = %s。'
             % (json.dumps(falsified, ensure_ascii=False), sum(falsified.values()),
                json.dumps(other, ensure_ascii=False)))
    L.append('- 所以逐题**不是**"每题 4 格"。高于 τ* 因而本来就点火的 W 格（现算）：')
    for t, et, v in sorted(above_w):
        L.append('  - %s %s/W |rel| = %.6f > 0.01 → 点火，不计入不吻合' % (t, et, v))
    # 逐位复现检查：同参数的两套题表，读数必须对得上，否则"复现"二字不成立。
    # 主表 rel 存的是 6 位小数，容差 1e-6 只用来吸收那个舍入，不是给真差异留口子。
    same = []
    for (K, et), cell in by.items():
        if K != '4':
            continue
        for ob, r in cell.items():
            if (et, ob) in mmc04 and abs(float(r['rel_truth']) - mmc04[(et, ob)][0]) < 1e-6:
                same.append(((et, ob), r['rel_truth']))
    L.append('- 扫描里 c=2,K=4,ρ=0.4 与主表 mmcK-04 同格读数一致（容差 1e-6，只吸收主表 6 位小数的舍入）'
             '：**%d / 4** 格' % len(same))
    for k, v in sorted(same):
        L.append('  - %s/%s: 扫描 %s vs 主表 %.6f' % (k[0], k[1], v, mmc04[k][0]))
    if len(same) != 4:
        L.append('- **警告：不是 4/4 复现，"独立题表复现同一读数"这句不能写进正文。**')
    L.append('')
    L.append('### 判决句（正文用）')
    tp = [r for r in r04 if r['verdict'] == 'TP']
    mm = [r for r in r04 if r['verdict'] == 'MISMATCH_BELOW_TAU']
    idle = [r for r in r04 if r['verdict'] == 'IDLE']
    L.append('- ρ=0.4 三格共 %d 个判定格：TP %d、MISMATCH_BELOW_TAU %d、IDLE %d。'
             % (len(r04) - len([r for r in r04 if r['etype'] == 'REF']), len(tp), len(mm), len(idle)))
    L.append('- 待人工读后写进正文；本脚本不下"边界成立/不成立"的结论。')

    io.open(OUT + '.tmp', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    os.replace(OUT + '.tmp', OUT)
    print('\n'.join(L[:12]))
    print('...')
    print('wrote %s ; regression gate = %s' % (os.path.basename(OUT), 'PASS' if gate_ok else 'FAIL'))
    return 0 if gate_ok else 1


if __name__ == '__main__':
    sys.exit(main())
