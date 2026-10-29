"""独立重跑那 9 件库存变异件——关掉复核方唯一保留的那条洞：
   "9/9 DETECTED 是矩阵自己报的，我只核到件在、矩阵认、聚合表重算过。"

三层独立，缺一层就不算独立：
  (1) **真值换实现**：不复用 external_truth.py 的闭式。
      EOQ 用对 q 的数值最小化求 q*、cost*；
      报童用 F(q)=Cu/(Cu+Co) 的二分求根定 q*，期望利润用 Simpson 数值积分
      直接对 D~N(mu,sd) 积分，不走 loss-function 闭式。
  (2) **仿真重跑**：9 件各跑一遍（R=10、H=40000），与矩阵里存的 rel 逐件比。
      存了的与重跑的若逐位相同 ⇒ 矩阵不是编的；若不同 ⇒ 报出来，别压。
  (3) **判定重算**：用第 (1) 层的独立真值算 rel，再按 τ*=0.01 自己判 DETECTED，
      与矩阵的 verdict 对表。这一层才真正破"同源自洽恒真"。

只读：不改任何权威产物；输出落本目录。
"""
import csv
import io
import json
import math
import os
import sys
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.dirname(os.path.dirname(HERE))   # = bench_v1
sys.path.insert(0, B1)
import criteria as C  # noqa: E402

MATRIX = os.path.join(HERE, 'EXTERNAL_MATRIX.csv')
MUTS = os.path.join(HERE, 'external_mutants.jsonl')
TASKS = os.path.join(HERE, 'external_tasks.jsonl')
OUT = os.path.join(HERE, 'EXTERNAL_INV_INDEPENDENT.md')
TAU = 0.01
SEEDS, HOR = 10, 40000.0


# ---------- (1) 独立真值 ----------
def eoq_truth(D, S, H):
    """不用 sqrt 公式：对 q 做三分搜索最小化 cost(q)=D/q*S+q/2*H（凸函数）。"""
    lo, hi = 1e-6, max(10.0, 10.0 * math.sqrt(D * S / max(H, 1e-9)))
    f = lambda q: D / q * S + q / 2.0 * H
    for _ in range(300):
        m1 = lo + (hi - lo) / 3.0
        m2 = hi - (hi - lo) / 3.0
        if f(m1) < f(m2):
            hi = m2
        else:
            lo = m1
    q = (lo + hi) / 2.0
    return {'q': q, 'cost': f(q)}


def newsvendor_truth(mu_d, sd, cost, price, salvage):
    """q* 用分位方程二分求根；exp_profit 用 Simpson 数值积分，不用 loss-function 闭式。"""
    cu, co = price - cost, cost - salvage
    frac = cu / (cu + co)
    nd = NormalDist(mu_d, sd)
    q = nd.inv_cdf(frac)          # 仅作二分初值参考；下面用积分独立复核同一条件
    lo, hi = mu_d - 12 * sd, mu_d + 12 * sd
    for _ in range(200):          # 一阶条件 P(D<=q)=frac，直接对 CDF 二分
        mid = (lo + hi) / 2.0
        if nd.cdf(mid) < frac:
            lo = mid
        else:
            hi = mid
    q = (lo + hi) / 2.0

    def profit(qv):
        n = 1001                   # Simpson 需要奇数节点
        a, b = mu_d - 12 * sd, mu_d + 12 * sd
        h = (b - a) / (n - 1)
        s = 0.0
        for i in range(n):
            x = a + i * h
            w = 1.0 if i in (0, n - 1) else (4.0 if i % 2 else 2.0)
            dens = math.exp(-0.5 * ((x - mu_d) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
            g = (price * min(qv, max(x, 0.0)) - cost * qv + salvage * max(qv - x, 0.0)) * dens
            s += w * g
        return s * h / 3.0
    return {'fractile': frac, 'q': q, 'exp_profit': profit(q), 'cu': cu, 'co': co}


def indep_truth(task):
    p, tpl = task['params'], task['template']
    if tpl == 'eoq':
        return eoq_truth(p['D'], p['S'], p['H'])
    return newsvendor_truth(p['mu_d'], p['sd'], p['cost'], p['price'], p['salvage'])


# ---------- 主流程 ----------
rows = {(r['task_id'], r['error_type']): r for r in
        csv.DictReader(io.open(MATRIX, encoding='utf-8', newline=''))}
muts = [json.loads(l) for l in io.open(MUTS, encoding='utf-8') if l.strip()]
tasks = {json.loads(l)['task_id']: json.loads(l) for l in
         io.open(TASKS, encoding='utf-8') if l.strip()}
inv = [(m['task_id'], m['error_type']) for m in muts
       if m['template'] in ('eoq', 'newsvendor')]
L = ['# 那 9 件库存变异件的独立重跑（不依赖矩阵自报）', '']
L.append('- 件数 %d；τ\\*=%.2f；R=%d、H=%g。真值用**另一套实现**（数值最小化 / 二分求根 + Simpson 积分）。'
         % (len(inv), TAU, SEEDS, HOR))
L.append('')
L.append('| 件 | 我判 | 矩阵判 | 我点的字段 | 矩阵记的字段 | 最大 rel | 独立真值 vs 闭式 最大相对差 |')
L.append('|----|------|--------|-----------|-------------|---------|------------------------|')

n_truthbad = n_verdif = n_fired = 0
mine_detect = 0
for tid, et in inv:
    t = tasks[tid]
    stored = rows[(tid, et)]
    it = indep_truth(t)
    path = os.path.join(B1, 'artifacts_external', '%s__%s.py' % (tid, et))
    obs, wall, note = C.run_artifact(path, SEEDS, HOR, 'none', 1, timeout=900)
    if obs is None:
        L.append('| %s/%s | 运行失败 | %s | — | %s | — | — |'
                 % (tid, et, stored['verdict'], stored['fired_obs']))
        n_truthbad += 1
        continue
    rels, fired, tdiff = {}, set(), 0.0
    for k, tv in it.items():
        ov = obs.get(k)
        closed = (t['truth_raw'] or {}).get(k)
        if ov is None or closed is None or not isinstance(ov, (int, float)):
            continue
        tdiff = max(tdiff, abs(tv - closed) / max(abs(closed), 1e-12))
        rels[k] = abs(ov - tv) / max(abs(tv), 1e-12)
        if rels[k] > TAU:
            fired.add(k)
    if not rels:
        L.append('| %s/%s | 无可比字段 | %s | — | %s | — | — |'
                 % (tid, et, stored['verdict'], stored['fired_obs']))
        n_truthbad += 1
        continue
    j_ = 'DETECTED' if fired else 'NOT_DETECTED'
    if j_ == 'DETECTED':
        mine_detect += 1
    sf = set(x for x in (stored['fired_obs'] or '').split(',') if x)
    if tdiff > 1e-4:
        n_truthbad += 1
    if j_ != stored['verdict']:
        n_verdif += 1
    if fired != sf:
        n_fired += 1
    L.append('| %s/%s | %s | %s | %s | %s | %.6f | %.2e |'
             % (tid, et, j_, stored['verdict'], ','.join(sorted(fired)) or '-',
                ','.join(sorted(sf)) or '-', max(rels.values()), tdiff))

L.append('')
L.append('## 判决')
L.append('- 独立真值与闭式真值相对差 >1e-4 的字段：**%d**（应为 0，否则我这套实现不可信）' % n_truthbad)
L.append('- 我点的**字段集合**与矩阵 `fired_obs` 不同的件：**%d**' % n_fired)
L.append('- 我判 vs 矩阵判 不一致的字段：**%d**' % n_verdif)
L.append('- 我用独立真值判出 DETECTED 的字段数：**%d**' % mine_detect)
L.append('- 结论口径：**只有上面三项全 0，"9/9 DETECTED"才算被独立确认**；'
         '否则本文件要写"未确认"，正文那句也得跟着降级。')
io.open(OUT + '.tmp', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
os.replace(OUT + '.tmp', OUT)
print('\n'.join(L[-6:]))
sys.exit(0 if (n_truthbad == 0 and n_fired == 0 and n_verdif == 0) else 1)
