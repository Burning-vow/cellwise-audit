"""题集生成器 + 解析真值 + 三道验证闸。

设计约束（写死在这里，免得以后偷工）：
- G2 的 CTMC 必须**数值解 πQ=0**，不许复用乘积形式递推，否则等于拿同一个公式验自己。
- 描述里的 W 单位是**分钟**，真值必须换算后存入 truth_print，否则判分会拿小时比分钟。
"""
import os
import sys
import json
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'pilot_c6'))
import analytics as A  # noqa: E402
import numpy as np  # noqa: E402


# ---------------------------------------------------------------- 通用 M/G/1 P-K
def mg1_pkc(lam, mean_s, es2):
    """M/G/1 单服务台 Pollaczek-Khinchine：Lq = lam^2 E[S^2] / (2(1-rho))。"""
    rho = lam * mean_s
    if rho >= 1.0:
        return None
    lq = lam * lam * es2 / (2.0 * (1.0 - rho))
    wq = lq / lam
    w = wq + mean_s
    return dict(rho=rho, L=lam * w, Lq=lq, W=w, Wq=wq, busy_frac=rho)


def h2_moments(mu, cv):
    """两阶段混合指数 H2，精确匹配 mean=1/mu 与 CV=cv（cv>1）。

    坑（前两次都栽在这）：混合分布的二阶矩是 E[X^2] = 2(p a^2 + q b^2)，
    不是"支均值的加权平方差"——支内指数方差必须算进去。
    取缩放支均值 a=1+tq、b=1−tp（自动满足 pa+qb=1），则
      CV^2 = 2(p a^2 + q b^2) - 1 = 1 + 2 t^2 p q   =>  t = sqrt((cv^2-1)/(2pq))
    可行域 b>0 要求 p < 2/(1+cv^2)，故取 p = 1/(1+cv^2)。"""
    if cv <= 1.0:
        raise ValueError('H2 只能表示 cv>1（cv=1 请用 M/M/1）')
    p = 1.0 / (1.0 + cv * cv)
    q = 1.0 - p
    t = math.sqrt((cv * cv - 1.0) / (2.0 * p * q))
    a = 1.0 + t * q                     # 慢支均值（单位 1/mu）
    b = 1.0 - t * p                     # 快支均值，必须 > 0
    if b <= 0.0:
        raise ValueError('infeasible H2: fast branch <= 0')
    r1, r2 = mu / a, mu / b
    mean_s = p / r1 + q / r2
    es2 = 2.0 * p / (r1 * r1) + 2.0 * q / (r2 * r2)
    return dict(p1=p, p2=q, r1=r1, r2=r2, mean_s=mean_s, es2=es2,
                cv_check=math.sqrt(es2 / (mean_s ** 2) - 1.0))


# ---------------------------------------------------------------- CTMC
def _solve_stationary(Q):
    N = Q.shape[0]
    M = Q.T.copy()
    b = np.zeros(N)
    M[0, :] = 1.0
    b[0] = 1.0
    pi = np.linalg.solve(M, b)
    pi = np.maximum(pi, 0.0)
    s = pi.sum()
    if s <= 0:
        raise RuntimeError('stationary solve failed')
    return pi / s


def stationary_birthdeath(lamv, muv):
    n = len(lamv)
    Q = np.zeros((n, n))
    for i in range(n):
        if i + 1 < n and lamv[i] > 0:
            Q[i, i] -= lamv[i]
            Q[i, i + 1] += lamv[i]
        if i - 1 >= 0 and muv[i] > 0:
            Q[i, i] -= muv[i]
            Q[i, i - 1] += muv[i]
    return _solve_stationary(Q)


def _mean_level(states, pi):
    return sum(s[0] * p for s, p in zip(states, pi))


def stationary_erlang1(lam, mu, k, nmax):
    """M/Erlang-k/1：状态 (n, 阶段j)，服务由 k 个速率 k*mu 的阶段串联。"""
    r = k * mu
    states = [(0, 0)]
    for n in range(1, nmax + 1):
        states += [(n, j) for j in range(1, k + 1)]
    idx = {s: i for i, s in enumerate(states)}
    N = len(states)
    Q = np.zeros((N, N))
    for s, i in idx.items():
        n, j = s
        if n < nmax:
            Q[i, i] -= lam
            Q[i, idx[(n + 1, j) if n >= 1 else (1, 1)]] += lam   # 到达不改在服务者的阶段
        if n >= 1:
            if j < k:
                Q[i, i] -= r
                Q[i, idx[(n, j + 1)]] += r
            else:
                Q[i, i] -= r
                Q[i, idx[(n - 1, 1)] if n - 1 >= 1 else idx[(0, 0)]] += r
    pi = _solve_stationary(Q)
    return _mean_level(states, pi)


def stationary_h2_1(lam, mu, cv, nmax):
    """M/H2/1：到达时按 0.5/0.5 抽一支速率，服务完成即离开。状态 (n, 类型j)。"""
    h = h2_moments(mu, cv)
    rates = [h['r1'], h['r2']]
    wts = [h['p1'], h['p2']]
    states = [(0, 0)]
    for n in range(1, nmax + 1):
        states += [(n, 1), (n, 2)]
    idx = {s: i for i, s in enumerate(states)}
    N = len(states)
    Q = np.zeros((N, N))
    for s, i in idx.items():
        n, j = s
        if n < nmax:
            Q[i, i] -= lam
            if n >= 1:
                Q[i, idx[(n + 1, j)]] += lam          # 在服务者的类型不因到达而改变
            else:
                Q[i, idx[(1, 1)]] += lam * wts[0]
                Q[i, idx[(1, 2)]] += lam * wts[1]
        if n >= 1:
            r = rates[j - 1]
            Q[i, i] -= r
            if n - 1 >= 1:      # 下一位在服务的是队首顾客，类型要重新按权重抽
                Q[i, idx[(n - 1, 1)]] += r * wts[0]
                Q[i, idx[(n - 1, 2)]] += r * wts[1]
            else:
                Q[i, idx[(0, 0)]] += r
    pi = _solve_stationary(Q)
    return _mean_level(states, pi)


# ---------------------------------------------------------------- 模板真值函数
def mmcK_truth(lam, mu, c, K):
    """M/M/c/K：容量 K（含在服务中），满则被拒。用数值生灭链算（独立闭式仅用于对账）。"""
    n = K + 1
    lamv = [lam if i < K else 0.0 for i in range(n)]
    muv = [0.0] + [min(i, c) * mu for i in range(1, n)]
    pi = stationary_birthdeath(lamv, muv)
    p_loss = pi[K]
    L = sum(i * pi[i] for i in range(n))
    eff = lam * (1.0 - p_loss)
    W = L / eff if eff > 0 else None
    return dict(rho=lam / (c * mu), L=L, W=W, p_loss=p_loss, eff_arrival=eff,
                busy_frac=1.0 - pi[0])


def mmcK_productform(lam, mu, c, K):
    """M/M/c/K 的**闭式**稳态（与 CTMC 数值解相互独立，用于对账）：
    pi_n ∝ a^n/n! (n<=c) ; a^n/(c! c^(n-c)) (c<n<=K)。"""
    a = lam / mu
    raw = []
    for n in range(K + 1):
        if n <= c:
            raw.append(a ** n / math.factorial(n))
        else:
            raw.append(a ** n / (math.factorial(c) * c ** (n - c)))
    s = sum(raw)
    pi = [v / s for v in raw]
    p_loss = pi[K]
    L = sum(n * pi[n] for n in range(K + 1))
    eff = lam * (1.0 - p_loss)
    return dict(L=L, p_loss=p_loss, W=L / eff if eff > 0 else None,
                busy_frac=1.0 - pi[0], rho=a / c)


def truth_mm1(p):
    return A.mmc(p['lambda'], p['mu'], 1)


def truth_mmc(p):
    return A.mmc(p['lambda'], p['mu'], p['c'])


def truth_mm1K(p):
    return A.mm1_K(p['lambda'], p['mu'], p['K'])


def truth_mmcK(p):
    return mmcK_truth(p['lambda'], p['mu'], p['c'], p['K'])


def truth_md1(p):
    mu = p['mu']
    return mg1_pkc(p['lambda'], 1.0 / mu, 1.0 / (mu * mu))


def truth_mh2(p):
    h = h2_moments(p['mu'], p['cv'])
    t = mg1_pkc(p['lambda'], h['mean_s'], h['es2'])
    if t is not None:
        t.update(dict(cv=p['cv'], p1=h['p1'], r1=h['r1'], p2=h['p2'], r2=h['r2'], es2=h['es2']))
    return t


def truth_jackson2(p):
    return A.jackson_series(p['lambda'], p['mu1'], p['mu2'])


def truth_newsvendor(p):
    return A.newsvendor_normal(p['mu_d'], p['sd'], p['price'], p['cost'], p['salvage'])


def truth_eoq(p):
    return A.eoq(p['D'], p['S'], p['H'])


TEMPLATES = {
    'mm1': dict(fn=truth_mm1, kind='queue', rho=lambda p: p['lambda'] / p['mu'],
                cands=dict(lambda_=(4, 6, 7, 8), mu=(10, 12))),
    'mmc': dict(fn=truth_mmc, kind='queue', rho=lambda p: p['lambda'] / (p['c'] * p['mu']),
                cands=dict(c=(2, 3, 4), lambda_=(8, 10, 14), mu=(5, 6, 10))),
    'mm1K': dict(fn=truth_mm1K, kind='queue', rho=lambda p: p['lambda'] / p['mu'],
                 cands=dict(K=(4, 6, 10), lambda_=(6, 8, 9), mu=(10, 12))),
    'mmcK': dict(fn=truth_mmcK, kind='queue', rho=lambda p: p['lambda'] / (p['c'] * p['mu']),
                 cands=dict(c=(2, 3), K=(4, 6, 8), lambda_=(6, 8), mu=(5, 10))),
    'md1': dict(fn=truth_md1, kind='queue', rho=lambda p: p['lambda'] / p['mu'],
                cands=dict(lambda_=(4, 6, 8), mu=(10, 12))),
    'mh2': dict(fn=truth_mh2, kind='queue', rho=lambda p: p['lambda'] / p['mu'],
                cands=dict(cv=(1.5, 2.0, 3.0), lambda_=(3, 5), mu=(10,))),
    'jackson2': dict(fn=truth_jackson2, kind='queue',
                     rho=lambda p: max(p['lambda'] / p['mu1'], p['lambda'] / p['mu2']),
                     cands=dict(lambda_=(4, 6), mu1=(8, 10), mu2=(10, 12))),
    'newsvendor': dict(fn=truth_newsvendor, kind='inventory', rho=None,
                       cands=dict(mu_d=(60, 90, 120), sd=(15, 25), price=(20, 30),
                                  cost=(12, 15), salvage=(4, 7))),
    'eoq': dict(fn=truth_eoq, kind='inventory', rho=None,
                cands=dict(D=(1000, 5000), S=(50, 200), H=(2, 10))),
}

DESC = {
 'mm1': dict(
   zh="某打印店只有 1 名值班员。顾客按泊松流到达，平均每小时 {lambda:g} 人；每人服务时间服从指数分布、平均 {service_min:g} 分钟。系统稳定，请给出稳态下顾客在店内的平均停留时间 W（单位：分钟）与店内平均人数 L（单位：人）。",
   en="One attendant in a print shop. Poisson arrivals {lambda:g}/hour; exponential service with mean {service_min:g} minutes. Give the steady-state mean time in system W (MINUTES) and mean number in system L (customers)."),
 'mmc': dict(
   zh="某银行网点同时开放 {c:d} 个柜台。顾客按泊松流到达、平均每小时 {lambda:g} 人，每人服务时间服从指数分布、平均 {service_min:g} 分钟，先到先服务。请给出平均等待+办理时间 W（分钟）、店内平均人数 L，以及到达时需要排队的概率 p_wait。",
   en="A bank branch opens {c:d} counters. Poisson arrivals {lambda:g}/hour, exponential service mean {service_min:g} minutes, FCFS. Give mean sojourn W (MINUTES), mean number in system L, and probability an arrival must wait."),
 'mm1K': dict(
   zh="某小诊室只有 1 名医生，候诊区连同诊室内一共只能容纳 {K:d} 人（含正在就诊者）。患者按泊松流到达、平均每小时 {lambda:g} 人，诊疗时间指数分布、平均 {service_min:g} 分钟；满员则患者当场离开。请给出 W（分钟）、L 和被拒概率 p_loss。",
   en="Clinic with 1 doctor and room for at most {K:d} patients including the one in service. Poisson arrivals {lambda:g}/hour, exponential service mean {service_min:g} minutes; blocked arrivals leave. Give W (MINUTES), L and blocking probability p_loss."),
 'mmcK': dict(
   zh="某收费站开放 {c:d} 个车道，站前总共只能容纳 {K:d} 辆车（含正在通行的）。车辆按泊松流到达、平均每小时 {lambda:g} 辆，通过时间指数分布、平均 {service_min:g} 分钟；车位满时后来的车直接驶离。请给出 W（分钟）、L、被拒概率 p_loss 与车道忙度。",
   en="Toll plaza with {c:d} lanes and space for {K:d} vehicles including those passing. Poisson arrivals {lambda:g}/hour, exponential pass time mean {service_min:g} minutes; overflow vehicles divert. Give W (MINUTES), L, loss probability and lane utilisation."),
 'md1': dict(
   zh="某自动洗车机每次洗车固定 {service_min:g} 分钟（完全不波动）。车辆按泊松流到达、平均每小时 {lambda:g} 辆，先到先洗。请给出稳态平均停留时间 W（分钟）与场内平均车辆数 L。",
   en="An automatic car wash takes exactly {service_min:g} minutes per car (no variation). Poisson arrivals {lambda:g}/hour, FCFS. Give steady-state mean sojourn W (MINUTES) and mean number on site L."),
 'mh2': dict(
   zh="某客服热线只有 1 个坐席。呼叫按泊松流到达、平均每小时 {lambda:g} 通；通话时长为两阶段混合指数分布，平均 {service_min:g} 分钟、变异系数 {cv:g}（只要均值与变异系数定了，P-K 公式给出的 W 与 L 就定了，与具体是哪种两阶分布无关）。请给出平均处理时长 W（分钟）与系统中平均呼叫数 L。",
   en="One help-desk agent. Poisson call arrivals {lambda:g}/hour; talk time is two-phase hyper-exponential with mean {service_min:g} minutes and coefficient of variation {cv:g} (the first two moments fix W and L via Pollaczek-Khinchine). Give mean sojourn W (MINUTES) and mean number in system L."),
 'jackson2': dict(
   zh="某车间两道工序串联：工件以每小时 {lambda:g} 件的泊松流进入工序 1（单台设备，指数加工平均 {s1:g} 分钟），完工后全部进入工序 2（单台设备，指数加工平均 {s2:g} 分钟），两道工序各自排队。请给出工件在两道工序内的总平均停留时间 W（分钟）与全系统平均在制品数 L。",
   en="Two-station series line: Poisson job arrivals {lambda:g}/hour to station 1 (one machine, exponential mean {s1:g} min), then all jobs go to station 2 (one machine, exponential mean {s2:g} min), each queueing separately. Give total mean flow time W (MINUTES) and mean work-in-process L."),
 'newsvendor': dict(
   zh="某面包店每天订一次货。日需求服从正态分布、均值 {mu_d:g} 个、标准差 {sd:g} 个；售价每个 {price:g} 元，成本每个 {cost:g} 元，卖不完当天按每个 {salvage:g} 元处理。请给出最优订货量 q（个）与对应的期望日利润（元）。",
   en="A bakery orders once daily. Demand is normal with mean {mu_d:g} and standard deviation {sd:g}; price {price:g}, unit cost {cost:g}, salvage {salvage:g}. Give the optimal order quantity q and the expected daily profit."),
 'eoq': dict(
   zh="某仓库全年需求量 {D:g} 件、需求均匀；每次下固定订单的手续与运输费 {S:g} 元，每件每年库存持有成本 {H:g} 元。请给出经济订货批量 q（件）与全年最小相关总成本（元）。",
   en="Annual demand {D:g} units at constant rate, ordering cost {S:g} per order, holding cost {H:g} per unit-year. Give the EOQ quantity and the minimum total relevant cost."),
}


def _grid(cands):
    keys = sorted(cands.keys())
    out = [{}]
    for k in keys:
        out = [dict(d, **{k: v}) for d in out for v in cands[k]]
    return [{('lambda' if kk == 'lambda_' else kk): vv for kk, vv in d.items()} for d in out]


def _unit_fields(kind, tpl, t):
    """把真值换算成**输出契约里点名的字段**（键名必须与 contract 完全一致，否则判分取不到值）。
    统一保留 6 位小数：真值不该带着 1e-15 的浮点噪声进题集，那是假精度。"""
    def r6(x):
        return None if x is None else round(x, 6)
    if kind == 'queue':
        out = {'W': r6(t['W'] * 60.0), 'L': r6(t['L'])}
        for key in ('p_loss', 'p_wait', 'busy_frac', 'rho'):
            if t.get(key) is not None:
                out[key] = r6(t[key])
        if t.get('eff_arrival') is not None:
            out['eff_arrival'] = r6(t['eff_arrival'])
        return out
    if tpl == 'newsvendor':
        return dict(q=r6(t['q']), exp_profit=r6(t['exp_profit']))
    return dict(q=r6(t['q']), cost=r6(t['cost']))


def simpy_ref(tpl, p):
    """把题接到**可运行的参照实现**上；不能直接跑的要老实标出来，不许假装都有。"""
    if tpl in ('mm1', 'mmc', 'mm1K', 'mmcK', 'md1'):
        kw = dict(lam=p['lambda'], mu=p['mu'], c=p.get('c', 1))
        if tpl in ('mm1K', 'mmcK'):
            kw['cap'] = p['K']
        if tpl == 'md1':
            kw['svc'] = 'det'
        return dict(engine='pilot_c6/pilot.py::run_once', kwargs=kw, ready=True)
    if tpl == 'mh2':
        return dict(engine=None, ready=False, reason='pilot 尚不支持 H2 抽样，需加 svc=h2')
    if tpl == 'jackson2':
        return dict(engine=None, ready=False, reason='pilot 尚无两节点串联路由，需加 station2 转派')
    if tpl == 'newsvendor':
        return dict(engine=None, ready=False, reason='需补蒙特卡洛需求抽样 + 利润核算的参照程序')
    return dict(engine=None, ready=False, reason='EOQ 是确定性闭式，无随机参照实现（只作真值校验）')


def _contract(kind, tpl):
    base = {'W': '分钟', 'L': '个(无量纲)'}
    if tpl in ('mm1K', 'mmcK'):
        base['p_loss'] = '概率0-1'
    if tpl == 'mmc':
        base['p_wait'] = '概率0-1'
    # busy_frac 不进这张表：它的**定义**逐题不同（util / 1−π₀ / c=1 恒等），
    # 由 build_tasks 里的 _busy_definition() 现算并写入，避免这里再写一份模板名对照。
    if tpl == 'newsvendor':
        base = {'q': '个', 'exp_profit': '元/天'}
    if tpl == 'eoq':
        base = {'q': '件', 'cost': '元/年'}
    return base


BUSY_TEXT = {
    'util': '每台平均利用率 E[min(N,c)]/c（不是"有没有人在忙"）',
    'occupied': '站不空的时间比例 1−π₀（不是每台平均利用率）',
    'coincident': '每台利用率 E[min(N,1)]/1 与 1−π₀ 在 c=1 时恒等，报哪个都一样',
}


def _busy_definition(t, p):
    """**由真值自己声明** busy_frac 用的是哪个口径，不写模板名对照表。

    判据：真值里的 `rho` 就是 a/c（每台平均）。
      · busy_frac == rho            → 该题用的是"每台平均"；若同时 c==1，两式恒等，标 coincident
      · busy_frac != rho            → 用的必然是 1−π₀（有限容量下 ρ 与占用率分开）
    外部审计 P-05 的原话是"内核按模板切换定义去贴真值"⇒ 参照件那条判据构造性恒过。
    把定义钉进契约之后，内核只许读声明（simcore.resolve 的 busy_def），不许再看模板名。
    """
    bf, rho = t.get('busy_frac'), t.get('rho')
    if bf is None:
        return None
    if rho is None:
        raise AssertionError('真值给了 busy_frac 却没给 rho，没法判口径：%s' % (sorted(t),))
    same = abs(bf - rho) <= 1e-9
    if not same:
        return 'occupied'
    return 'coincident' if int(p.get('c', 1)) == 1 else 'util'


def build_tasks(per_template_cap=8):
    tasks, skipped = [], []
    for tpl, spec in TEMPLATES.items():
        kept = []
        for p in _grid(spec['cands']):
            try:
                t = spec['fn'](p)
            except Exception as ex:
                skipped.append((tpl, p, 'EXC %s' % ex))
                continue
            reqkey = 'W' if spec['kind'] == 'queue' else ('exp_profit' if tpl == 'newsvendor' else 'cost')
            if t is None or t.get(reqkey) is None:
                skipped.append((tpl, p, 'rho>=1 / 不稳定 / 无解'))
                continue
            # 题质量闸：报童若临界分位≈0.5，则"忽略成本结构、直接订均值"也能对，区分度为零
            if tpl == 'newsvendor' and abs(t['fractile'] - 0.5) < 0.05:
                skipped.append((tpl, p, '临界分位 %.3f≈0.5，退化成"订均值"也能对' % t['fractile']))
                continue
            if spec['rho'] is not None and spec['rho'](p) >= 0.98:
                skipped.append((tpl, p, 'rho=%.3f 太接近 1' % spec['rho'](p)))
                continue
            kept.append((p, t))
        cap = per_template_cap if spec['kind'] == 'queue' else 6
        for i, (p, t) in enumerate(kept[:cap]):
            q = dict(p)
            if 'mu' in q:
                q['service_min'] = round(60.0 / q['mu'], 4)
            if 'mu1' in q:
                q['s1'] = round(60.0 / q['mu1'], 4)
                q['s2'] = round(60.0 / q['mu2'], 4)
            contract = _contract(spec['kind'], tpl)
            busy_def = _busy_definition(t, p)
            if busy_def:                       # 声明了定义，才许把 busy_frac 写进契约并计分
                contract['busy_frac'] = BUSY_TEXT[busy_def]
            tasks.append(dict(
                task_id='%s-%02d' % (tpl, i + 1), template=tpl, kind=spec['kind'],
                params=q,
                busy_def=busy_def,             # None = 这道题没有忙度真值（jackson2/eoq/newsvendor）
                truth_raw=t,                      # 原始单位：时间=小时、率=每小时
                truth_print=_unit_fields(spec['kind'], tpl, t),
                output_contract=contract,
                simpy_ref=simpy_ref(tpl, p),
                desc_zh=DESC[tpl]['zh'].format(**q),
                desc_en=DESC[tpl]['en'].format(**q),
            ))
    return tasks, skipped


# ---------------------------------------------------------------- 闸 1：手算特例
def gate1():
    rows, ok = [], True

    def chk(name, cond, detail):
        nonlocal ok
        ok = ok and cond
        rows.append('  [%s] %s | %s' % ('PASS' if cond else 'FAIL', name, detail))

    for lam, mu in [(4, 10), (8, 10), (7, 12)]:
        t = A.mmc(lam, mu, 1)
        chk('G1.1 c=1 时 Erlang-C 等待概率=rho', abs(t['p_wait'] - lam / mu) < 1e-12,
            'lam=%g mu=%g p_wait=%.12f rho=%.12f' % (lam, mu, t['p_wait'], lam / mu))
    for lam, mu in [(8, 10), (6, 10), (7, 12)]:
        t = A.mmc(lam, mu, 1)
        ref = 1.0 / (mu - lam)
        chk('G1.2 M/M/1 W=1/(mu-lambda)', abs(t['W'] - ref) < 1e-12,
            '%.12f vs %.12f' % (t['W'], ref))
        chk('G1.2b Little L=lambda*W', abs(t['L'] - lam * t['W']) < 1e-9,
            'L=%.6f lambda*W=%.6f' % (t['L'], lam * t['W']))
    t = A.mm1_K(10.0, 10.0, 5)
    chk('G1.3 M/M/1/K 在 rho=1 时均匀( p_K=1/(K+1) )', abs(t['p_loss'] - 1 / 6) < 1e-12,
        'p_loss=%.12f 1/6=%.12f' % (t['p_loss'], 1 / 6))
    t = A.newsvendor_normal(100.0, 20.0, 20.0, 12.0, 4.0)
    chk('G1.4 报童 cu=co 时 q=均值', abs(t['q'] - 100.0) < 1e-6,
        'fractile=%.6f q=%.8f' % (t['fractile'], t['q']))
    t = A.eoq(1000.0, 50.0, 2.0)
    hold = t['q'] / 2.0 * 2.0
    order = 1000.0 / t['q'] * 50.0
    chk('G1.5 EOQ 最优处持有=订货成本', abs(hold - order) < 1e-6,
        'hold=%.8f order=%.8f' % (hold, order))
    big = mmcK_truth(8.0, 10.0, 1, 200)
    ref = A.mmc(8.0, 10.0, 1)
    chk('G1.6 M/M/1/200 收敛到 M/M/1', abs(big['L'] - ref['L']) / ref['L'] < 1e-6,
        'L(K=200)=%.8f L(∞)=%.8f' % (big['L'], ref['L']))
    for cv in (1.2, 1.5, 2.0, 3.0):
        h = h2_moments(10.0, cv)
        got_cv = math.sqrt(h['es2'] / (h['mean_s'] ** 2) - 1.0)
        es2_id = h['mean_s'] ** 2 * (1.0 + cv * cv)
        chk('G1.7 H2 参数化 cv=%.1f' % cv,
            abs(got_cv - cv) < 1e-9 and abs(h['mean_s'] - 0.1) < 1e-12
            and h['r1'] > 0 and h['r2'] > 0 and abs(h['es2'] - es2_id) < 1e-12,
            'p1=%.6f r1=%.6f r2=%.6f mean_s=%.10f cv_算出=%.10f' % (
                h['p1'], h['r1'], h['r2'], h['mean_s'], got_cv))
    t = mg1_pkc(8.0, 1 / 10.0, 2.0 / (10.0 * 10.0))     # cv=1 => E[S^2]=2/mu^2 => M/M/1
    ref = A.mmc(8.0, 10.0, 1)
    chk('G1.8 P-K 在 cv=1 时必须退化成 M/M/1', abs(t['L'] - ref['L']) < 1e-12,
        'L_PK=%.10f L_MM1=%.10f' % (t['L'], ref['L']))
    t1 = A.mdc(6.0, 10.0, 1)
    t2 = mg1_pkc(6.0, 0.1, 0.01)
    chk('G1.9 M/D/1 两条实现一致（analytics.mdc vs mg1_pkc）',
        abs(t1['L'] - t2['L']) < 1e-12, '%.10f vs %.10f' % (t1['L'], t2['L']))
    pf1 = mmcK_productform(9.0, 10.0, 1, 6)
    cf1 = A.mm1_K(9.0, 10.0, 6)
    chk('G1.10 M/M/1/K 闭式(阶乘形式)与 mm1_K 一致',
        abs(pf1['L'] - cf1['L']) < 1e-9 and abs(pf1['p_loss'] - cf1['p_loss']) < 1e-9,
        'L %.10f vs %.10f ; p_loss %.10f vs %.10f' % (pf1['L'], cf1['L'], pf1['p_loss'], cf1['p_loss']))
    return ok, rows
def gate2():
    rows, worst = [], {}

    def cmp_(name, v_ctmc, v_closed):
        d = abs(v_ctmc - v_closed) / abs(v_closed)
        worst[name] = d
        rows.append('  [%s] %-26s CTMC=%.8f 闭式=%.8f 相对差=%.3e' % (
            'PASS' if d < 5e-4 else 'FAIL', name, v_ctmc, v_closed, d))

    # 2.0 先自检 CTMC 机械：Erlang-1 就是 M/M/1
    cmp_('ctmc_selftest(M/M/1)', stationary_erlang1(8.0, 10.0, 1, 150), A.mmc(8.0, 10.0, 1)['L'])

    for k in (2, 4, 8, 16):
        lam, mu = 6.0, 10.0
        es2 = (k + 1.0) / (k * mu * mu)
        cmp_('PK path (Erlang-%d)' % k, stationary_erlang1(lam, mu, k, 220),
             mg1_pkc(lam, 1.0 / mu, es2)['L'])
    for cv in (1.5, 2.0, 3.0):
        lam, mu = 3.0, 10.0
        h = h2_moments(mu, cv)
        cmp_('M/H2/1 cv=%.1f' % cv, stationary_h2_1(lam, mu, cv, 220),
             mg1_pkc(lam, h['mean_s'], h['es2'])['L'])
    for c in (2, 3, 4):
        lam, mu = {2: 8.0, 3: 10.0, 4: 14.0}[c], {2: 6.0, 3: 5.0, 4: 6.0}[c]
        n = 160
        pi = stationary_birthdeath([lam] * n, [0.0] + [min(i, c) * mu for i in range(1, n)])
        cmp_('Erlang-C c=%d' % c, sum(i * pi[i] for i in range(n)), A.mmc(lam, mu, c)['L'])
    for K in (4, 6, 10):
        lam, mu = 9.0, 10.0
        n = K + 1
        pi = stationary_birthdeath([lam if i < K else 0.0 for i in range(n)],
                                   [0.0] + [mu] * K)
        closed = A.mm1_K(lam, mu, K)
        cmp_('M/M/1/К=%d L' % K, sum(i * pi[i] for i in range(n)), closed['L'])
        cmp_('M/M/1/K=%d p_loss' % K, pi[K], closed['p_loss'])
    for mu1, mu2 in ((8.0, 10.0), (10.0, 12.0)):
        lam = 4.0
        n = 140
        p1 = stationary_birthdeath([lam] * n, [0.0] + [mu1] * n)
        p2 = stationary_birthdeath([lam] * n, [0.0] + [mu2] * n)
        L = sum(i * p1[i] for i in range(n)) + sum(i * p2[i] for i in range(n))
        cmp_('Jackson 2 节点 lam=%g' % lam, L, A.jackson_series(lam, mu1, mu2)['L'])
    for c, K, lam, mu in ((2, 6, 6.0, 5.0), (3, 8, 8.0, 10.0), (2, 4, 6.0, 5.0), (3, 6, 8.0, 5.0)):
        ct = mmcK_truth(lam, mu, c, K)
        pf = mmcK_productform(lam, mu, c, K)
        cmp_('M/M/%d/%d L CTMC vs 闭式' % (c, K), ct['L'], pf['L'])
        cmp_('M/M/%d/%d p_loss' % (c, K), ct['p_loss'], pf['p_loss'])
        cmp_('M/M/%d/%d W= L/λeff (Little)' % (c, K), ct['W'], pf['W'])
    return rows, worst


# ---------------------------------------------------------------- 闸 3：参照实现 CI 覆盖
def gate3(seeds=12, horizon=40000.0, alpha=0.05):
    sys.path.insert(0, os.path.join(HERE, '..', 'pilot_c6'))
    import pilot
    T = 2.262  # t_{0.975, df=9}
    rows, ok = [], True
    cases = [
        ('mm1  lam=8 mu=10', dict(lam=8.0, mu=10.0, c=1), A.mmc(8.0, 10.0, 1)),
        ('mmc  lam=8 mu=6 c=2', dict(lam=8.0, mu=6.0, c=2), A.mmc(8.0, 6.0, 2)),
        ('mm1K lam=9 mu=10 K=6', dict(lam=9.0, mu=10.0, c=1, cap=6), A.mm1_K(9.0, 10.0, 6)),
        ('md1  lam=6 mu=10', dict(lam=6.0, mu=10.0, c=1, svc='det'), mg1_pkc(6.0, 0.1, 0.01)),
    ]
    for name, kw, truth in cases:
        Ls, Ws = [], []
        for s in range(1, seeds + 1):
            k = pilot.run_once(horizon=horizon, seed=s, **kw)
            Ls.append(k['area'] / k['win'])
            Ws.append(sum(k['soj']) / len(k['soj']))
        for label, vals, tv in (('L', Ls, truth['L']), ('W', Ws, truth['W'])):
            m = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
            hw = T * sd / math.sqrt(len(vals))
            cover = abs(m - tv) <= hw
            ok = ok and cover
            rows.append('  [%s] %-22s %s 参照实现 mean=%.6f hw=%.6f  闭式真值=%.6f 覆盖=%s' % (
                'PASS' if cover else 'FAIL', name, label, m, hw, tv, cover))
    return ok, rows


# ---------------------------------------------------------------- 主流程
def main():
    tasks, skipped = build_tasks()
    with open(os.path.join(HERE, 'tasks.jsonl'), 'w', encoding='utf-8') as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + '\n')

    g1_ok, g1 = gate1()
    g2_rows, g2_worst = gate2()
    g3_ok, g3 = gate3()

    lines = ['# 题集 v1 验证报告（闸1 手算特例 / 闸2 独立 CTMC / 闸3 参照实现 CI）', '']
    lines.append('题数=%d 跳过=%d  模板数=%d' % (len(tasks), len(skipped), len(TEMPLATES)))
    lines.append('')
    lines.append('## 闸1 手算特例  => %s' % ('PASS' if g1_ok else 'FAIL'))
    lines += g1
    lines.append('')
    lines.append('## 闸2 独立 CTMC（数值解 πQ=0，阈值相对差 5e-4）')
    lines += g2_rows
    mx = max(g2_worst.items(), key=lambda kv: kv[1])
    lines.append('  最大相对差: %s = %.3e' % (mx[0], mx[1]))
    lines.append('')
    lines.append('## 闸3 参照实现 CI 覆盖（%d 种子 × %g 时域）=> %s' % (
        12, 40000, 'PASS' if g3_ok else 'FAIL'))
    lines += g3
    lines.append('')
    lines.append('## 被跳过的参数组合（不稳定/太接近饱和）')
    for tpl, p, why in skipped:
        lines.append('  %s %s : %s' % (tpl, json.dumps(p, ensure_ascii=False), why))
    open(os.path.join(HERE, 'VERIFY.md'), 'w', encoding='utf-8').write('\n'.join(lines))

    bytpl = {}
    for t in tasks:
        bytpl[t['template']] = bytpl.get(t['template'], 0) + 1
    print('tasks=%d skipped=%d per_template=%s' % (len(tasks), len(skipped),
          json.dumps(bytpl, ensure_ascii=False)))
    print('gate1=%s gate3=%s gate2_max_rel=%s' % (g1_ok, g3_ok, '%s %.3e' % mx))
    print('VERIFY.md written')


if __name__ == '__main__':
    main()
