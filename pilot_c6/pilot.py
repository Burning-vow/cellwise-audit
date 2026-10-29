"""C6' 预实验：排队论闭式真值 × 变异算子 × 四种判据 → 判据盲区谱。

全程本地，不调用任何 API，不读任何旧工作区。
- 仿真器是手写的 SimPy 模型（时间窗内统计，避免全时长/窗口分母混用）；
- 变异算子 = 可控注入的建模错误；
- 被判的对象是"模型的行为"。V4（逐字段与参考模型比对）在本实验里用变异标签当理想上界。

统计口径（写死）：
- 丢弃前 warm_frac 的预热；
- 每种配置跑 K 个独立种子；窗口内到达/离开分别计数；
- L = N(t) 在窗口上的时间平均；W = 窗口内离开顾客的逗留时间均值；
- λ̂ = 窗口内离开数 / 窗口长；busy = 窗口内服务台占用时间 / (窗口长 × c)；
- W 的置信区间用"每 rep 10 个批均值 + 跨 rep 合并"的批均值法，t 系数取 2.262（df=9）。
"""
import io
import os
import sys
import math
import json
import random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '_pylibs'))

import simpy
from analytics import mmc, mm1_K, newsvendor_normal, _norm_ppf


# ---------------------------------------------------------------- 单种子仿真
def run_once(lam, mu, c=1, horizon=8000.0, warm_frac=0.25, seed=1,
             arr='poisson', svc='exp', discipline='fcfs', cap=None,
             batch=1, double_count=False, no_warmout=False, noise_state=False,
             scale_both=1.0):
    rng = random.Random(seed)
    rng2 = random.Random(seed * 7919 + 13)   # 只用于排队规则抽取，保证不同规则共享同一到达/服务流（配对比较）
    env = simpy.Environment()
    lam = lam * scale_both
    mu = mu * scale_both
    win_start = 0.0 if no_warmout else warm_frac * horizon
    win = horizon - win_start

    S = dict(N=0, in_svc=0, waiting=[],
             arr_all=0, blk_all=0,
             arr_win=0, dep_win=0, blk_win=0,
             area=0.0, busy=0.0, last=0.0,
             soj=[], batches=[[] for _ in range(10)], junk=[])

    def integ():
        a0 = max(S['last'], win_start)
        if env.now > a0:
            S['area'] += S['N'] * (env.now - a0)
        S['last'] = env.now

    def pick():
        if discipline == 'fcfs':
            return S['waiting'].pop(0)
        if discipline == 'lcfs':
            return S['waiting'].pop()
        if discipline == 'siro':
            return S['waiting'].pop(rng2.randrange(len(S['waiting'])))
        raise ValueError(discipline)

    def pump():
        while S['waiting'] and S['in_svc'] < c:
            cust = pick()
            S['in_svc'] += 1
            env.process(serve(cust))

    def serve(cust):
        d = rng.expovariate(mu) if svc == 'exp' else 1.0 / mu
        t0 = env.now
        yield env.timeout(d)
        a0 = max(t0, win_start)
        if env.now > a0:
            S['busy'] += env.now - a0
        integ()                      # 先按"事件前的 N"积分，再改状态
        S['in_svc'] -= 1
        S['N'] -= 1
        if env.now >= win_start:
            inc_dep = 2 if (double_count and rng2.random() < 0.05) else 1
            S['dep_win'] += inc_dep
            S['soj'].append(env.now - cust['t'])
            bi = min(9, int((env.now - win_start) / win * 10))
            S['batches'][bi].append(env.now - cust['t'])
        if noise_state:
            S['junk'].append(env.now)
        pump()

    def source():
        while env.now < horizon:
            dt = rng.expovariate(lam) if arr == 'poisson' else 1.0 / lam
            yield env.timeout(dt)
            for _ in range(batch):
                S['arr_all'] += 1
                inwin = env.now >= win_start
                if inwin:
                    S['arr_win'] += 1
                if cap is not None and S['N'] >= cap:
                    S['blk_all'] += 1
                    if inwin:
                        S['blk_win'] += 1
                    continue
                integ()              # 先按"事件前的 N"积分，再改状态
                S['N'] += 1
                S['waiting'].append(dict(t=env.now))
                pump()

    integ()
    env.process(source())
    env.run(until=horizon)
    integ()

    bm = [sum(b) / len(b) for b in S['batches'] if b]
    return dict(win=win, area=S['area'], busy_frac=S['busy'] / (win * c), soj=S['soj'], bm=bm,
                arr_win=S['arr_win'], dep_win=S['dep_win'], blk_win=S['blk_win'],
                arr_all=S['arr_all'], blk_all=S['blk_all'],
                n_junk=len(S['junk']))


def pool(reps):
    """把多个独立种子的原始量合成 KPI 与置信区间。"""
    K = float(len(reps))
    win = sum(r['win'] for r in reps) / K
    L = sum(r['area'] for r in reps) / (win * K)
    soj = [x for r in reps for x in r['soj']]
    W = sum(soj) / len(soj) if soj else float('nan')
    dep = sum(r['dep_win'] for r in reps) / (win * K)
    arr = sum(r['arr_win'] for r in reps) / (win * K)
    blk = sum(r['blk_win'] for r in reps) / (win * K)
    busy = sum(r['busy_frac'] for r in reps) / K
    bm = [x for r in reps for x in r['bm']]
    if len(bm) >= 3:
        m = sum(bm) / len(bm)
        v = sum((x - m) ** 2 for x in bm) / (len(bm) - 1)
        hw = 2.262 * math.sqrt(v / len(bm))
    else:
        hw = float('nan')
    loss = blk / arr if arr > 0 else 0.0
    return dict(L=L, W=W, lam_hat=dep, arr=arr, blk=blk, busy=busy, loss=loss,
                hw=hw, rel_hw=hw / W if W else float('nan'),
                n=len(soj), little_res=abs(L - dep * W) / L if L else float('nan'),
                cons_res=(abs(arr - dep - blk) / arr) if arr > 0 else 0.0)


# ---------------------------------------------------------------- 四种判据
TAUS = (0.01, 0.05)


def V1(kpi, truth, key='W'):
    """解析对账。fired = 相对误差超容差；fired_powered 还要求效应超过 2 倍置信半宽，
    否则"抓到了"只是噪声，不能算可检。"""
    t = truth.get(key)
    if t is None or t != t:
        return dict(rel=None, fired=[False, False], fired_powered=[False, False])
    rel = abs(kpi[key] - t) / abs(t)
    band = 2.0 * kpi['rel_hw'] if kpi['rel_hw'] == kpi['rel_hw'] else 0.0
    return dict(rel=rel, band=band,
                fired=[rel > x for x in TAUS],
                fired_powered=[rel > max(x, band) for x in TAUS])


def V2(kpi, eps_little=0.02, tol_cons=0.02):
    ok_l = kpi['little_res'] <= eps_little
    ok_c = kpi['cons_res'] <= tol_cons
    ok_s = kpi['busy'] <= 1.0 + 0.01
    return dict(fired=not (ok_l and ok_c and ok_s),
                little=kpi['little_res'], cons=kpi['cons_res'], busy=kpi['busy'])


def V3(runs, tol=0.0):
    """runs: dict tag -> kpi。方向一致性：λ↑ ⇒ W↑；μ↓ ⇒ W↑；c↑ ⇒ W↓。"""
    w = {k: v['W'] for k, v in runs.items()}
    checks = {
        'dW_dlam>=0': w['lam12'] >= w['base'] - tol * w['base'],
        'dW_dmu>=0': w['mu08'] >= w['base'] - tol * w['base'],
        'dW_dc>=0': w['c2'] <= w['base'] + tol * w['base'],
    }
    return dict(fired=not all(checks.values()), checks=checks)


def V4(mut_name, benign_names=('unit_scale_both', 'noop_extra_state')):
    """理想化的结构/逐字段比对：只要代码与参考实现不同就报警（上界）。"""
    return dict(fired=(mut_name != 'ref'), benign_alarm=(mut_name in benign_names))


# ---------------------------------------------------------------- 场景与变异目录
SCENES = [
    dict(id='mm1_r80', kind='mm1', p=dict(lam=0.8, mu=1.0, c=1)),
    dict(id='mmc2_r85', kind='mmc', p=dict(lam=1.7, mu=1.0, c=2)),
    dict(id='mmc3_r80', kind='mmc', p=dict(lam=2.4, mu=1.0, c=3)),
    dict(id='mm1K_cap8', kind='mm1K', p=dict(lam=0.8, mu=1.0, c=1, cap=8)),
    dict(id='mm1K_cap20', kind='mm1K', p=dict(lam=0.8, mu=1.0, c=1, cap=20)),
]

MUTATIONS = [
    ('ref', 'none', dict()),
    ('disc_lcfs', 'semantics', dict(discipline='lcfs')),
    ('disc_siro', 'semantics', dict(discipline='siro')),
    ('c_minus1', 'semantics', dict(c_delta=-1)),
    ('c_frozen1', 'semantics', dict(force_c=1)),
    ('svc_determ', 'semantics', dict(svc='determ')),
    ('arr_determ', 'semantics', dict(arr='determ')),
    ('cap_omitted', 'semantics', dict(drop_cap=True)),
    ('cap_minus3', 'semantics', dict(cap_delta=-3)),
    ('batch2', 'semantics', dict(batch=2)),
    ('dep_double_count', 'semantics', dict(double_count=True)),
    ('unit_scale_both', 'benign', dict(scale_both=2.0)),
    ('noop_extra_state', 'benign', dict(noise_state=True)),
    ('no_warmout', 'estimation', dict(no_warmout=True)),
]

APPLIES = dict(c_minus1={'mmc2_r85', 'mmc3_r80'}, c_frozen1={'mmc2_r85', 'mmc3_r80'},
               cap_omitted={'mm1K_cap8', 'mm1K_cap20'},
               cap_minus3={'mm1K_cap8', 'mm1K_cap20'})

SEEDS = [11, 23, 37, 51, 67]
HORIZON = 50000.0


def kwargs_for(mut, p, kind):
    kw = dict(lam=p['lam'], mu=p['mu'], c=p['c'], arr='poisson', svc='exp',
              discipline='fcfs', cap=p.get('cap'), batch=1, horizon=HORIZON)
    for k, v in mut.items():
        if k == 'c_delta':
            kw['c'] = max(1, kw['c'] + v)
        elif k == 'force_c':
            kw['c'] = v
        elif k == 'drop_cap':
            kw['cap'] = None
        elif k == 'cap_delta':
            if kw['cap'] is not None:
                kw['cap'] = max(2, kw['cap'] + v)
        else:
            kw[k] = v
    return kw


def truth_for(kind, p):
    if kind in ('mm1', 'mmc'):
        return mmc(p['lam'], p['mu'], p['c'])
    if kind == 'mm1K':
        return mm1_K(p['lam'], p['mu'], p['cap'])
    raise ValueError(kind)


def measure(kw, seeds=SEEDS):
    return pool([run_once(seed=s, **kw) for s in seeds])


def main():
    rows = []
    out = io.open(os.path.join(HERE, 'pilot_results.jsonl'), 'w', encoding='utf-8')
    for sc in SCENES:
        p = sc['p']
        truth = truth_for(sc['kind'], p)
        for mname, sem, mut in MUTATIONS:
            if mname in APPLIES and sc['id'] not in APPLIES[mname]:
                continue
            kw = kwargs_for(mut, p, sc['kind'])
            kpi = measure(kw)
            v1 = V1(kpi, truth)
            v2 = V2(kpi)
            pert = dict(
                base=kpi,
                lam12=measure(dict(kw, lam=kw['lam'] * 1.2)),
                mu08=measure(dict(kw, mu=kw['mu'] * 0.8)),
                c2=measure(dict(kw, c=max(1, kw['c'] * 2))))
            # 对已经用了扰动的变异（如 c_frozen1）要冻结同一个错误，否则测的是"修复"而不是"漏检"
            if 'force_c' in mut:
                pert['c2'] = measure(dict(kw, c=kw['c']))
            if 'c_delta' in mut:
                pert['c2'] = measure(dict(kw, c=max(1, kw['c'] + 1)))
            v3 = V3(pert)
            v4 = V4(mname)
            rec = dict(scene=sc['id'], kind=sc['kind'], mut=mname, sem=sem,
                       truth_W=truth['W'], sim_W=kpi['W'], rel_W=v1['rel'],
                       band=v1.get('band'),
                       truth_L=truth['L'], sim_L=kpi['L'], rel_L=abs(kpi['L'] - truth['L']) / truth['L'],
                       truth_ploss=truth.get('p_loss'), sim_loss=kpi['loss'],
                       v1_fire_1pct=v1['fired'][0], v1_fire_5pct=v1['fired'][1],
                       v1p_fire_1pct=v1['fired_powered'][0], v1p_fire_5pct=v1['fired_powered'][1],
                       v2_fire=v2['fired'], v2_little=v2['little'], v2_cons=v2['cons'], v2_busy=v2['busy'],
                       v3_fire=v3['fired'], v3_checks=v3['checks'],
                       v4_fire=v4['fired'], v4_benign_alarm=v4['benign_alarm'],
                       rel_hw=kpi['rel_hw'], n=kpi['n'], busy=kpi['busy'],
                       arr=kpi['arr'], dep=kpi['lam_hat'])
            rows.append(rec)
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
            out.flush()
    out.close()

    # ---------------- 汇总表：变异 × 判据 → 被抓次数/适用场景数
    import collections
    agg = collections.defaultdict(lambda: dict(n=0, v1a=0, v1b=0, v1pa=0, v1pb=0, v2=0, v3=0, v4=0))
    for r in rows:
        if r['mut'] == 'ref':
            continue
        a = agg[r['mut']]
        a['n'] += 1
        a['v1a'] += 1 if r['v1_fire_5pct'] else 0
        a['v1b'] += 1 if r['v1_fire_1pct'] else 0
        a['v1pa'] += 1 if r['v1p_fire_5pct'] else 0
        a['v1pb'] += 1 if r['v1p_fire_1pct'] else 0
        a['v2'] += 1 if r['v2_fire'] else 0
        a['v3'] += 1 if r['v3_fire'] else 0
        a['v4'] += 1 if r['v4_fire'] else 0

    def frac(x, n):
        return '-' if n == 0 else '%d/%d' % (x, n)

    lines = ['%-20s %-10s %3s %8s %8s %6s %6s %6s' % ('变异', '性质', 'n', 'V1@5%功效', 'V1@1%功效', 'V2', 'V3', 'V4')]
    for mname, sem, _ in MUTATIONS:
        if mname == 'ref':
            continue
        a = agg[mname]
        lines.append('%-20s %-10s %3d %8s %8s %6s %6s %6s' % (
            mname, sem, a['n'], frac(a['v1pa'], a['n']), frac(a['v1pb'], a['n']),
            frac(a['v2'], a['n']), frac(a['v3'], a['n']), frac(a['v4'], a['n'])))
    # 参照模型自身的假阳性率
    ref = [r for r in rows if r['mut'] == 'ref']
    lines.append('')
    lines.append('REF 模型（应为 0 报警）: n=%d  V1@1%%误报=%d  V1@5%%误报=%d  V2误报=%d  V3误报=%d  最大 rel_W=%.4f  平均 rel_hw=%.4f' % (
        len(ref), sum(1 for r in ref if r['v1_fire_1pct']), sum(1 for r in ref if r['v1_fire_5pct']),
        sum(1 for r in ref if r['v2_fire']), sum(1 for r in ref if r['v3_fire']),
        max(r['rel_W'] for r in ref), sum(r['rel_hw'] for r in ref) / len(ref)))
    txt = '\n'.join(lines)
    io.open(os.path.join(HERE, 'pilot_matrix.txt'), 'w', encoding='utf-8').write(txt + '\n')
    print(txt)

    # ---------------- 报童：解析真值 vs 三种错型（无仿真噪声）
    nv = newsvendor_normal(100.0, 30.0, 30.0, 20.0, 5.0)
    cu, co = nv['cu'], nv['co']
    cases = [('ref', nv['q']),
             ('swap_Cu_Co', 100.0 + 30.0 * _norm_ppf(co / (cu + co))),
             ('ignore_salvage', 100.0 + 30.0 * _norm_ppf(cu / (cu + 20.0))),
             ('order_the_mean', 100.0)]
    nv_rows = []
    for name, q in cases:
        prof = _nv_profit(q, 100.0, 30.0, 30.0, 20.0, 5.0)
        nv_rows.append(dict(case=name, q=q, profit=prof,
                            rel_gap=(nv['exp_profit'] - prof) / nv['exp_profit']))
    io.open(os.path.join(HERE, 'pilot_newsvendor.json'), 'w', encoding='utf-8').write(
        json.dumps(dict(truth=nv, rows=nv_rows), ensure_ascii=False, indent=1))
    print('\nNEWSVENDOR  truth q=%.4f  E[profit]=%.4f' % (nv['q'], nv['exp_profit']))
    for r in nv_rows:
        print('  %-16s q=%8.3f  profit=%10.4f  相对损失=%.5f' % (r['case'], r['q'], r['profit'], r['rel_gap']))


def _nv_profit(q, mu_d, sd, price, cost, salvage):
    """Simpson 数值积分算期望利润，用来交叉验证闭式解。"""
    n = 4000
    lo, hi = mu_d - 8 * sd, mu_d + 8 * sd
    h = (hi - lo) / (n - 1)
    s = 0.0
    for i in range(n):
        x = lo + i * h
        f = math.exp(-0.5 * ((x - mu_d) / sd) ** 2) / (sd * math.sqrt(2.0 * math.pi))
        sales = min(x, q)
        g = price * sales - cost * q + salvage * (q - sales)
        w = 0.5 if i in (0, n - 1) else (4.0 if i % 2 == 1 else 2.0)
        s += w * g * f
    return s * h / 3.0


if __name__ == '__main__':
    main()
