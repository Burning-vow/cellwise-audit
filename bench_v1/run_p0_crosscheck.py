"""P0 补字段之后的验收：在**所有有参照工件的题**（当前 64 题，题数现算别抄这里）上
   复现闭式真值、守恒式、配对式与自报口径自洽。

门禁（跑之前就钉死，不许事后放宽）：
  G1 J2a Little   相对偏差 < 0.01（=当前最小 τ 档）
  G2 J2b 流量守恒 相对偏差 < 0.01
  G3 J2c 忙度     不 > 1
  G4 J1 各观测量  相对偏差 ≤ 该模板在 table_tau_v2.csv（artifacts 出口、10 种子口径）里的 τ*
  G5 J4 方向      每个可用扰动都不许"方向违反且超噪声"
  J0 自报口径自洽 三条腿（原 `G6` 只是它的 `J0c` 一条腿，10-18 起折进 J0、阈值一起进 τ* 表；
                  缺 τ* 行的腿记 `no_tau` 而**不给默认阈值**）
输出逐条 flush，可续跑；--shard i/N 分片。
"""
import os
import sys
import csv
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402
from inv_obs import j1_inv  # noqa: E402

ART = os.path.join(HERE, 'artifacts')
def _flat(x):
    s = str(x).replace(chr(10), ' | ').replace(chr(13), ' ')
    return s if len(s) <= 200 else s[:60] + ' ... ' + s[-140:]

class _SanitizedWriter(object):
    """出口统一加两列口径（P-16：这张表过去不携带自己的 seeds/horizon，
    与归档里的 R=20 旧表列结构完全一样、行数也一样，只能靠 mtime 分——那是会认错的东西）。

    表头行不加：用第一格是不是 'task_id' 来区分，数据行的第一格永远是题号。
    """

    def __init__(self, w):
        self._w = w

    def writerow(self, vals):
        vals = list(vals)
        if vals and str(vals[0]) != 'task_id':
            vals += [SEEDS, HOR]
        self._w.writerow([('' if v is None else str(v).replace(chr(10), ' | ').replace(chr(13), ' '))
                          for v in vals])


# 默认写权威文件；改口径/动内核之后要先看新表与旧表差在哪，就用 P0_OUT 指到临时文件，
# 不许在 A/B 还没做完时覆盖交付物（受控 A/B 的规矩：被验对象与验证工具分开坏）。
OUT = os.environ.get('P0_OUT') or os.path.join(HERE, 'P0_CROSSCHECK.csv')
# 口径必须和 τ* 的标定口径一致（本文的主张就是"τ 是预算的函数"）：
#   τ* 来自 table_tau_v2.csv 的 task 级试验 = 每次判定 10 种子 / horizon 40000（artifacts 出口）
#   原来这里写 SEEDS=20 并读 v1 的 table_tau.csv（calib_ref 出口、task 级 100 种子）⇒ 三头不对
SEEDS = 10
HOR = 40000.0

TAU_STAR = {}
TAU_J0 = {}                 # 单位锚的阈值单独一张表：与 J1 分开，免得 (模板,统计量) 撞名后互相顶包
tp = os.path.join(HERE, 'table_tau_v2.csv')     # artifacts 出口、64 题这一版
if not os.path.exists(tp):
    raise SystemExit('缺 %s —— 腿 B 用的就是这套阈值，没有它不许跑门禁' % tp)
BASIS = set()
with open(tp, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['criterion'] in ('J1', 'J0') and r['tau_star'] not in ('', 'NONE'):
            (TAU_STAR if r['criterion'] == 'J1' else TAU_J0)[
                (r['template'], r['statistic'])] = float(r['tau_star'])
            # 口径断言也覆盖 J0：新判据若在别的预算上标定，这里就该炸，而不是悄悄混用
            BASIS.add(int(r['tau_basis_seeds']))
assert BASIS == {SEEDS}, 'τ* 的标定口径 %s 与本脚本的 SEEDS=%d 不一致 ⇒ 跨预算比阈值等同口径错' % (
    sorted(BASIS), SEEDS)
print('[xcheck] 口径对齐 τ*=%s seeds / horizon=%g，τ* 覆盖 (模板,观测量) %d 项' % (
    sorted(BASIS), HOR, len(TAU_STAR)), flush=True)


def tau_of(tpl, obs, default=0.01):
    return TAU_STAR.get((tpl, obs), default)


def main():
    shard, nshard, limit = 1, 1, 0
    for a in sys.argv[1:]:
        if a.startswith('--shard='):
            shard, nshard = [int(x) for x in a.split('=')[1].split('/')]
        elif a.startswith('--limit='):
            limit = int(a.split('=')[1])
    tasks = C.load_tasks()
    ids = [t['task_id'] for t in tasks
           if os.path.exists(os.path.join(ART, '%s__REF.py' % t['task_id']))]
    if limit:
        ids = ids[:limit]
    ids = ids[(shard - 1)::nshard]
    new = not os.path.exists(OUT)
    fh = open(OUT, 'a', newline='', encoding='utf-8')
    w = _SanitizedWriter(csv.writer(fh))
    if new:
        w.writerow(['task_id', 'template', 'stage', 'pert', 'obs', 'est', 'truth',
                    'rel', 'tau', 'gate', 'note', 'seeds', 'horizon'])
        fh.flush()
    by_id = {t['task_id']: t for t in tasks}
    print('[xcheck %d/%d] %d tasks' % (shard, nshard, len(ids)), flush=True)
    for tid in ids:
        task = by_id[tid]
        tpl = task['template']
        path = os.path.join(ART, '%s__REF.py' % tid)
        base, dt, note = C.run_artifact(path, SEEDS, HOR, 'none', 1)
        if base is None:
            w.writerow([tid, tpl, 'run', 'none', '', '', '', '', '', 'FAIL', note])
            fh.flush()
            continue
        truth = task.get('truth_print') or {}
        # ---- J1 ----
        j1 = C.j1_analytic(base, task, tau=None)
        j1['per_obs'].update(j1_inv(base, task))      # 报童/EOQ 的 q/exp_profit/cost
        for o, d in j1['per_obs'].items():
            if d.get('rel') is None:
                w.writerow([tid, tpl, 'J1', 'none', o, d.get('est'), d.get('truth'),
                            '', '', 'NA', d.get('status', '')[:120]])
                continue
            t = tau_of(tpl, o)
            cal = 'tau=%g' % t if (tpl, o) in TAU_STAR else 'tau=%g(未标定,取1%%下限)' % t
            gate = 'PASS' if d['rel'] <= t else 'FAIL'
            w.writerow([tid, tpl, 'J1', 'none', o, d.get('est'), d.get('truth'),
                        '%.6f' % d['rel'], t, gate, cal])
        # ---- J2 / J3 ----
        for cname, fn in (('J2', C.j2_conservation), ('J3', C.j3_pairing)):
            res = fn(base, task, tau=None)
            bag = res.get('per_stat') or res.get('per_obs') or {}
            for k, d in bag.items():
                rel = d.get('rel')
                if rel is None:
                    w.writerow([tid, tpl, cname, 'none', k, '', '', '', '', 'NA',
                                d.get('status', '')[:120]])
                    continue
                if k == 'J2c_busy':
                    gate = 'PASS' if rel <= 0.01 else 'FAIL'
                else:
                    gate = 'PASS' if rel < 0.01 else 'FAIL'
                w.writerow([tid, tpl, cname, 'none', k, d.get('est'), '',
                            '%.6e' % rel, 0.01, gate,
                            (d.get('status', '') + ' ' + (d.get('note') or '')
                             + (' field=' + d['field'] if d.get('field') else '')).strip()[:120]])
        # ---- J0 自报口径自洽（四条腿；吸收并替换原先写死 0.01 的 G6）----
        # 2026-10-18：旧 G6 只做 `dep_rate` 对题面 λ 一条腿，且阈值硬编码 0.01、不进 τ* 表
        # ⇒ 腿 B 永远用不到它。现在统一由 criteria.j0_unit_anchor 出，阈值走 τ*（缺行就停下）。
        # `horizon` 传调用参数，J0e 那腿才是"工件改不动"的那一条。
        j0 = C.j0_unit_anchor(base, task, tau=None, horizon=HOR)
        for k, d in (j0.get('per_stat') or {}).items():
            rel = d.get('rel')
            if rel is None:
                w.writerow([tid, tpl, 'J0', 'none', k, '', '', '', '', 'NA',
                            d.get('status', '')[:120]])
                continue
            t0 = TAU_J0.get((tpl, k))
            if t0 is None:
                w.writerow([tid, tpl, 'J0', 'none', k, d.get('est'), d.get('paired'),
                            '%.6e' % rel, '', 'NA', 'no_tau(未标定，不给默认阈值)'])
                continue
            w.writerow([tid, tpl, 'J0', 'none', k, d.get('est'), d.get('paired'),
                        '%.6e' % rel, t0, 'PASS' if rel <= t0 else 'FAIL',
                        'tau=%g %s' % (t0, (d.get('status') or '')[:60])])
        # **口径违规单独占一行，并且用 FAIL**（第四轮 R4-4：`unknown_unit` 只记 NA 等于让
        # "一个生词单位同时关掉 J0a/J0c/J2a/J3a 四条判据"这件事隐形）。
        # 我方 64 个参照件全在词表内 ⇒ 这一行今天不会出现；一旦出现就该把门禁拦下来，
        # 而不是混进 NA 里当"这道题不可判"。
        for s in (j0.get('unit_violation') or []):
            w.writerow([tid, tpl, 'J0', 'none', 'unit_violation', '', '', '', '', 'FAIL',
                        '口径违规(词表外单位)：%s' % s[:110]])

        # ---- J4 方向（与基线同 seed 段）----
        for pt in C.PERTURBATIONS.get(tpl, ()):
            pert, dt2, n2 = C.run_artifact(path, SEEDS, HOR, pt, 1)
            if pert is None:
                w.writerow([tid, tpl, 'J4', pt, '', '', '', '', '', 'NA', n2])
                fh.flush()
                continue
            r4 = C.j4_direction(base, pert, pt, margin=None)
            # 注意：j4_direction 返回的是**扁平**结构（obs/base/pert/viol/se_diff/fired_at），
            # 不是 per_stat 字典。上一版按 per_stat 取会一行都取不到 ⇒ 整个 J4 静默失踪。
            if r4.get('status') != 'ok':
                w.writerow([tid, tpl, 'J4', pt, r4.get('obs'), '', '', '', '', 'NA',
                            str(r4.get('status'))[:120]])
                continue
            fa = r4.get('fired_at') or {}
            fired = fa.get('0.01')
            gate = 'FAIL' if fired else 'PASS'
            w.writerow([tid, tpl, 'J4', pt, r4.get('obs'), r4.get('base'), r4.get('pert'),
                        '%.6f' % (r4.get('viol') or 0.0), 0.01, gate,
                        'se_diff=%s powered=%s' % (r4.get('se_diff'),
                                                   (r4.get('fired_powered_at') or {}).get('0.01'))])
        fh.flush()
        print('[xcheck %d/%d] %s done base=%.1fs' % (shard, nshard, tid, dt), flush=True)
    fh.close()


if __name__ == '__main__':
    main()
