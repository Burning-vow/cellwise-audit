"""解析真值：教科书闭式解。全部只用标准库，便于核对。"""
import math


def erlang_c_prob_wait(a, c):
    """a = lambda/mu (offered load, Erlang), c = 服务台数。返回等待概率 C(a,c)。
    C = [a^c/c! * c/(c-a)] / [sum_{k=0}^{c-1} a^k/k! + a^c/c! * c/(c-a)]
    """
    rho = a / c
    if rho >= 1.0:
        return float('inf')
    term = 1.0
    s = 1.0                     # sum_{k=0}^{c-1} 累加到 k=c-1 为止
    for k in range(1, c):
        term = term * a / k
        s += term
    # 此刻 term = a^(c-1)/(c-1)!，补一步得到 a^c/c!
    term_c = term * a / c
    num = term_c * c / (c - a)
    return num / (s + num)


def mmc(an, mu, c):
    """M/M/c 无限等待位。返回 dict of analytic truths."""
    a = an / mu
    rho = a / c
    if rho >= 1.0:
        return None
    pw = erlang_c_prob_wait(a, c)
    wq = pw / (c * mu - an)
    w = wq + 1.0 / mu
    return dict(rho=rho, L=an * w, Lq=an * wq, W=w, Wq=wq, busy_frac=rho, p_wait=pw)


def mdc(an, mu, c):
    """M/D/c 无闭式（用 c=1 的 Pollaczek-Khinchine）。"""
    if c != 1:
        return None
    rho = an / mu
    if rho >= 1.0:
        return None
    wq = an / (2.0 * mu * (mu - an))
    w = wq + 1.0 / mu
    return dict(rho=rho, L=an * w, Lq=an * wq, W=w, Wq=wq, busy_frac=rho, p_wait=None)


def mm1_K(an, mu, K):
    """M/M/1/K：系统容量上限 K（含在服务中的）。精确生灭链稳态。"""
    rho = an / mu
    if abs(rho - 1.0) < 1e-9:
        pk = [1.0 / (K + 1.0)] * (K + 1)
    else:
        denom = sum(rho ** k for k in range(K + 1))
        pk = [rho ** k / denom for k in range(K + 1)]
    p_loss = pk[K]
    L = sum(k * pk[k] for k in range(K + 1))
    eff = an * (1.0 - p_loss)
    busy = 1.0 - pk[0]
    W = L / eff if eff > 0 else None
    Wq = W - 1.0 / mu if W is not None else None
    return dict(rho=an / mu, L=L, W=W, Wq=Wq, p_loss=p_loss, eff_arrival=eff, busy_frac=busy)


def jackson_series(an, mu1, mu2):
    """两节点串联开排队网络（Jackson 积式）：每节点 M/M/1。"""
    n1 = mmc(an, mu1, 1)
    n2 = mmc(an, mu2, 1)
    if n1 is None or n2 is None:
        return None
    return dict(L=n1['L'] + n2['L'], L1=n1['L'], L2=n2['L'],
                W=n1['W'] + n2['W'], W1=n1['W'], W2=n2['W'])


def newsvendor_normal(mu_d, sd, price, cost, salvage):
    """报童：正态需求，闭式最优量与期望成本。"""
    cu = price - cost
    co = cost - salvage
    if cu <= 0 or co <= 0:
        return None
    cf = cu / (cu + co)                      # critical fractile
    z = _norm_ppf(cf)
    q = mu_d + sd * z
    # E[min(D,q)] = mu - sd*[phi(z) - (1-CDF(z))*z] 形式；用标准 loss 函数
    expect_loss = sd * (std_normal_pdf(z) - z * (1.0 - _norm_cdf(z)))
    exp_sales = mu_d - expect_loss           # E[min(D,q)]
    exp_profit = price * exp_sales - cost * q + salvage * (q - exp_sales)
    return dict(fractile=cf, q=q, exp_profit=exp_profit, cu=cu, co=co)


def std_normal_pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def _norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _norm_ppf(p):
    """逆正态分位：二分法对 math.erf 求根。避免手写有理近似系数的出错风险。"""
    if p <= 0.0 or p >= 1.0:
        raise ValueError('p out of (0,1)')
    lo, hi = -12.0, 12.0
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if _norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def eoq(D, S, H):
    q = math.sqrt(2.0 * D * S / H)
    return dict(q=q, cost=math.sqrt(2.0 * D * S * H))
