# -*- coding: utf-8 -*-
"""P5 外部教材题：独立闭式真值（只 import 标准库，不 import simcore）。

用途：
  1) 生成 external_tasks.jsonl（schema 与 bench_v1/tasks.jsonl 一致）；
  2) 生成 EXTERNAL_TRUTH.md（逐题公式与数值，供人工复核）；
  3) 供 check_external_ref.py 与 simcore 参照件对账。

约束：这些题不进入 64 题主表，不参与 tau* 标定；真值只由本文件计算。
"""
import json
import math
import os
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_OUT = os.path.join(HERE, 'external_tasks.jsonl')
MD_OUT = os.path.join(HERE, 'EXTERNAL_TRUTH.md')


def _r6(x):
    return round(float(x), 6)


def erlang_c(a, c):
    """M/M/c 的 Erlang C：到达的顾客需要等待的概率（a=lambda/mu）。"""
    if c <= 0 or a <= 0 or a >= c:
        raise ValueError('erlang_c 需要 0 < a < c')
    tail = a ** c / (math.factorial(c) * (1.0 - a / c))
    head = sum(a ** n / math.factorial(n) for n in range(c))
    return tail / (head + tail)


def mm1(lam, mu):
    rho = lam / mu
    if not 0 < rho < 1:
        raise ValueError('mm1 需要 0<rho<1')
    L = rho / (1.0 - rho)
    Lq = rho * rho / (1.0 - rho)
    W = L / lam * 60.0
    Wq = Lq / lam * 60.0
    return dict(rho=rho, L=L, Lq=Lq, W=W, Wq=Wq, p_wait=rho, busy_frac=rho)


def mmc(c, lam, mu):
    a = lam / mu
    rho = a / c
    if not 0 < rho < 1:
        raise ValueError('mmc 需要 0<rho<1')
    pw = erlang_c(a, c)
    Wq = pw / (c * mu - lam) * 60.0
    W = Wq + 60.0 / mu
    L = lam * W / 60.0
    Lq = lam * Wq / 60.0
    return dict(rho=rho, L=L, Lq=Lq, W=W, Wq=Wq, p_wait=pw, busy_frac=rho)


def _bd_weights(c, K, a):
    """M/M/c/K 的未归一化生灭链权重：n<=c 用 a^n/n!，n>c 用 a^n/(c! c^(n-c))。"""
    w = []
    for n in range(K + 1):
        if n <= c:
            w.append(a ** n / math.factorial(n))
        else:
            w.append(a ** n / (math.factorial(c) * c ** (n - c)))
    return w


def mmck(c, K, lam, mu):
    """M/M/c/K 乘积形式；busy_frac 按 1-pi0（至少一台在忙），与 simcore 的 occupied 口径一致。"""
    if K < c:
        raise ValueError('mmck 需要 K>=c')
    a = lam / mu
    w = _bd_weights(c, K, a)
    s = sum(w)
    p = [x / s for x in w]
    p0 = p[0]
    pK = p[K]
    eff = lam * (1.0 - pK)
    L = sum(n * p[n] for n in range(K + 1))
    Lq = sum((n - c) * p[n] for n in range(c + 1, K + 1))
    W = L / eff * 60.0
    Wq = Lq / eff * 60.0
    # simcore 的 waits 只在“未被拒绝且无空闲台”时 +1，分母是全部到达 ⇒ 这是无条件等待概率。
    p_wait = sum(p[n] for n in range(c, K))
    return dict(rho=a / c, L=L, Lq=Lq, W=W, Wq=Wq, p_loss=pK,
                eff_arrival=eff, busy_frac=1.0 - p0, p_wait=p_wait)


def md1(lam, mu):
    rho = lam / mu
    if not 0 < rho < 1:
        raise ValueError('md1 需要 0<rho<1')
    Wq = rho / (2.0 * mu * (1.0 - rho)) * 60.0
    W = Wq + 60.0 / mu
    L = lam * W / 60.0
    Lq = lam * Wq / 60.0
    return dict(rho=rho, L=L, Lq=Lq, W=W, Wq=Wq, p_wait=rho, busy_frac=rho)


def mh2(lam, mu, cv):
    rho = lam / mu
    if not 0 < rho < 1:
        raise ValueError('mh2 需要 0<rho<1')
    Wq = rho * (1.0 + cv * cv) / (2.0 * mu * (1.0 - rho)) * 60.0
    W = Wq + 60.0 / mu
    L = lam * W / 60.0
    Lq = lam * Wq / 60.0
    return dict(rho=rho, L=L, Lq=Lq, W=W, Wq=Wq, p_wait=rho, busy_frac=rho, cv=cv)


def jackson2(lam, mu1, mu2):
    for mu in (mu1, mu2):
        if lam >= mu:
            raise ValueError('jackson2 需要 lambda < 每个 mu')
    W1 = 1.0 / (mu1 - lam) * 60.0
    W2 = 1.0 / (mu2 - lam) * 60.0
    W = W1 + W2
    L1 = lam * W1 / 60.0
    L2 = lam * W2 / 60.0
    return dict(W=W, W1=W1, W2=W2, L=L1 + L2, L1=L1, L2=L2,
                rho1=lam / mu1, rho2=lam / mu2)


def eoq(D, S, H):
    q = math.sqrt(2.0 * D * S / H)
    cost = D / q * S + q / 2.0 * H
    return dict(q=q, cost=cost)


def newsvendor(mu_d, sd, cost, price, salvage):
    cu = price - cost
    co = cost - salvage
    if cu <= 0 or co <= 0:
        raise ValueError('newsvendor 需要 price>cost>salvage')
    frac = cu / (cu + co)
    q = mu_d + sd * NormalDist().inv_cdf(frac)
    z = (q - mu_d) / sd
    phi = NormalDist().pdf(z)
    Phi = NormalDist().cdf(z)
    e_over = sd * (phi + z * Phi)          # E[(q-D)^+]
    e_under = sd * (phi - z * (1.0 - Phi))  # E[(D-q)^+]
    exp_profit = price * (mu_d - e_under) - cost * q + salvage * e_over
    return dict(fractile=frac, q=q, exp_profit=exp_profit, cu=cu, co=co,
                e_over=e_over, e_under=e_under, z=z)


def _spec(tid, tpl, kind, params, fn, print_keys, busy_def, desc_zh, desc_en, source_note):
    return dict(task_id=tid, template=tpl, kind=kind, params=params, fn=fn,
                print_keys=print_keys, busy_def=busy_def, desc_zh=desc_zh,
                desc_en=desc_en, source_note=source_note)


def specs():
    qsrc = ('据 Gross《Fundamentals of Queueing Theory》与 Hillier & Lieberman '
            '《Introduction to Operations Research》排队章主题改写；版次/页码待核')
    isrc = ('据 Hillier & Lieberman 库存章与 Zipkin《Foundations of Inventory Management》'
            'EOQ/newsvendor 章主题改写；版次/页码待核')
    return [
        _spec('ext-mm1-01', 'mm1', 'queue',
              dict(lam=6.0, mu=10.0),
              lambda p: mm1(**p),
              ('W', 'L', 'p_wait', 'busy_frac'), 'coincident',
              '某服务窗口只有 1 名工作人员。顾客按泊松流到达，平均每小时 6 人；'
              '每名顾客的服务时间服从指数分布，平均 10 分钟。系统已达到稳态。'
              '请给出顾客在系统内的平均停留时间 W（分钟）、系统内平均人数 L、'
              '到达时需要等待的概率 p_wait，以及窗口的忙碌时间比例 busy_frac。',
              'A single-server queue: Poisson arrivals at 6/hour, exponential service '
              'with mean 10 minutes. Report steady-state W (minutes), L, p_wait, busy_frac.',
              qsrc),
        _spec('ext-mm1-02', 'mm1', 'queue',
              dict(lam=8.5, mu=10.0),
              lambda p: mm1(**p),
              ('W', 'L', 'p_wait', 'busy_frac'), 'coincident',
              '一个高负荷的单窗口服务点：顾客按泊松流到达，平均每小时 8.5 人；'
              '服务时间服从指数分布，平均 6 分钟。系统稳定。'
              '求顾客平均停留时间 W（分钟）、系统内平均人数 L、到达需等待的概率 p_wait，'
              '以及服务台的忙碌时间比例 busy_frac。',
              'A high-utilization single-server queue: Poisson arrivals 8.5/hour, '
              'exponential service mean 6 minutes. Report W (minutes), L, p_wait, busy_frac.',
              qsrc),
        _spec('ext-mmc-01', 'mmc', 'queue',
              dict(c=3, lam=12.0, mu=5.0),
              lambda p: mmc(**p),
              ('W', 'L', 'p_wait', 'busy_frac'), 'util',
              '某服务站有 3 个并行窗口，顾客排一条队依次接受服务。顾客按泊松流到达，'
              '平均每小时 12 人；每个窗口的服务时间服从指数分布，平均 12 分钟。'
              '求顾客平均停留时间 W（分钟）、系统内平均人数 L、到达需等待的概率 p_wait，'
              '以及每个窗口的平均利用率 busy_frac。',
              'An M/M/3 queue: Poisson arrivals 12/hour, exponential service mean 12 minutes, '
              'one shared queue. Report W (minutes), L, p_wait, and per-server utilization.',
              qsrc),
        _spec('ext-mm1K-01', 'mm1K', 'queue',
              dict(K=5, lam=9.0, mu=10.0),
              lambda p: mmck(1, **p),
              ('W', 'L', 'p_loss', 'p_wait', 'busy_frac'), 'occupied',
              '一个单窗口服务点，系统最多容纳 5 人（包括正在服务的人）；客满时新到顾客立即离开。'
              '顾客按泊松流到达，平均每小时 9 人；服务时间服从指数分布，平均 6 分钟。'
              '求平均停留时间 W（分钟）、系统内平均人数 L、被拒绝概率 p_loss、'
              '到达时需要等待的概率 p_wait（按全部到达计，含被拒者），'
              '以及“至少一人在系统中”的时间比例 busy_frac。',
              'An M/M/1/5 loss system: Poisson arrivals 9/hour, exponential service mean '
              '6 minutes. Report W (minutes), L, p_loss, p_wait over all arrivals, busy_frac.',
              qsrc),
        _spec('ext-mm1K-02', 'mm1K', 'queue',
              dict(K=4, lam=6.0, mu=12.0),
              lambda p: mmck(1, **p),
              ('W', 'L', 'p_loss', 'p_wait', 'busy_frac'), 'occupied',
              '一个容量为 4 的单窗口服务点（含正在服务者），客满即拒绝新到顾客。'
              '到达为泊松流，平均每小时 6 人；服务时间服从指数分布，平均 5 分钟。'
              '求 W（分钟）、L、拒绝概率 p_loss、按全部到达计的等待概率 p_wait，'
              '以及至少一人在系统中的时间比例 busy_frac。',
              'An M/M/1/4 loss system: Poisson arrivals 6/hour, exponential service mean '
              '5 minutes. Report W, L, p_loss, p_wait, busy_frac.',
              qsrc),
        _spec('ext-mmcK-01', 'mmcK', 'queue',
              dict(c=2, K=6, lam=8.0, mu=5.0),
              lambda p: mmck(**p),
              ('W', 'L', 'p_loss', 'p_wait', 'busy_frac'), 'occupied',
              '某服务点有 2 个并行窗口，系统容量为 6 人（包括正在服务的人）；客满时新到顾客离开。'
              '顾客按泊松流到达，平均每小时 8 人；每个窗口的服务时间服从指数分布，平均 12 分钟。'
              '求平均停留时间 W（分钟）、系统内平均人数 L、拒绝概率 p_loss、'
              '按全部到达计的等待概率 p_wait，以及至少一人在系统中的时间比例 busy_frac。',
              'An M/M/2/6 loss system: Poisson arrivals 8/hour, exponential service mean '
              '12 minutes. Report W, L, p_loss, p_wait, busy_frac.',
              qsrc),
        _spec('ext-mmcK-02', 'mmcK', 'queue',
              dict(c=2, K=4, lam=9.0, mu=5.0),
              lambda p: mmck(**p),
              ('W', 'L', 'p_loss', 'p_wait', 'busy_frac'), 'occupied',
              '一个高阻塞的两窗口服务点：2 个并行窗口，系统最多容纳 4 人（含服务中），'
              '客满即拒绝。到达为泊松流，平均每小时 9 人；每个窗口服务时间服从指数分布，'
              '平均 12 分钟。求 W（分钟）、L、拒绝概率 p_loss、按全部到达计的等待概率 p_wait，'
              '以及至少一人在系统中的时间比例 busy_frac。',
              'A high-blocking M/M/2/4 system: Poisson arrivals 9/hour, exponential service '
              'mean 12 minutes. Report W, L, p_loss, p_wait, busy_frac.',
              qsrc),
        _spec('ext-md1-01', 'md1', 'queue',
              dict(lam=6.0, mu=10.0),
              lambda p: md1(**p),
              ('W', 'L', 'busy_frac'), 'coincident',
              '一个单窗口服务点，每名顾客的服务时间固定为 6 分钟（没有随机性）。'
              '顾客按泊松流到达，平均每小时 6 人。系统稳定。'
              '求顾客平均停留时间 W（分钟）、系统内平均人数 L，以及服务台的忙碌时间比例 busy_frac。',
              'An M/D/1 queue: Poisson arrivals 6/hour, deterministic service 6 minutes. '
              'Report W (minutes), L, busy_frac.',
              qsrc),
        _spec('ext-mh2-01', 'mh2', 'queue',
              dict(lam=6.0, mu=10.0, cv=2.0),
              lambda p: mh2(**p),
              ('W', 'L', 'busy_frac'), 'coincident',
              '一个单窗口服务点。服务时间服从两阶段混合指数分布，均值为 6 分钟、'
              '变异系数为 2（即 CV²=4）。顾客按泊松流到达，平均每小时 6 人。'
              '求顾客平均停留时间 W（分钟）、系统内平均人数 L，以及服务台的忙碌时间比例 busy_frac。',
              'An M/H2/1 queue: Poisson arrivals 6/hour, two-phase hyperexponential service '
              'with mean 6 minutes and CV=2. Report W (minutes), L, busy_frac.',
              qsrc),
        _spec('ext-jackson2-01', 'jackson2', 'queue',
              dict(lam=6.0, mu1=10.0, mu2=8.0, s1=6.0, s2=7.5),
              lambda p: jackson2(lam=p['lam'], mu1=p['mu1'], mu2=p['mu2']),
              ('W', 'L'), None,
              '两站串联的无限缓冲服务系统：每站各有 1 个服务台，顾客依次经过两站后离开。'
              '外部到达为泊松流，平均每小时 6 人；站 1 服务时间服从指数分布、平均 6 分钟，'
              '站 2 服务时间服从指数分布、平均 7.5 分钟。求端到端平均停留时间 W（分钟）'
              '与两站合计的平均顾客数 L。',
              'A two-station tandem Jackson network: Poisson arrivals 6/hour, exponential '
              'service means 6 and 7.5 minutes. Report end-to-end W (minutes) and total L.',
              qsrc),
        _spec('ext-eoq-01', 'eoq', 'inventory',
              dict(D=1200.0, S=50.0, H=2.0),
              lambda p: eoq(**p),
              ('q', 'cost'), None,
              '某物料的年需求量为 1200 件，需求确定且均匀；每次订货的固定费用为 50 元，'
              '每件每年的持有费为 2 元；不允许缺货。求经济订货批量 q（件）与年总成本 cost（元/年）。',
              'Deterministic EOQ: annual demand 1200, order cost 50, holding cost 2 per '
              'unit-year. Report q and annual cost.',
              isrc),
        _spec('ext-newsvendor-01', 'newsvendor', 'inventory',
              dict(mu_d=100.0, sd=20.0, cost=10.0, price=14.0, salvage=9.0),
              lambda p: newsvendor(**p),
              ('q', 'exp_profit'), None,
              '单周期报童问题：日需求服从正态分布 N(100, 20)。每件售价 14 元、进价 10 元，'
              '未售出的每件残值为 9 元。求最优订货量 q（件）与期望日利润 exp_profit（元/天）。',
              'A single-period newsvendor: normal demand N(100, 20), price 14, cost 10, '
              'salvage 9. Report optimal q and expected daily profit.',
              isrc),
    ]


def _truth_for(sp):
    raw = sp['fn'](sp['params'])
    tp = {k: _r6(raw[k]) for k in sp['print_keys']}
    return raw, tp


def _unit_for(tpl, key):
    if key == 'W':
        return '分钟'
    if key == 'L':
        return '个(无量纲)'
    if key in ('p_loss', 'p_wait'):
        return '概率0-1'
    if key == 'busy_frac':
        if tpl == 'mmc':
            return '每台平均利用率 E[min(N,c)]/c'
        if tpl in ('mm1K', 'mmcK'):
            return '站不空的时间比例 1−π0（不是每台平均利用率）'
        return '每台平均利用率 E[min(N,1)]/1 与 1−π0 在 c=1 时恒等'
    if key == 'q':
        return '件' if tpl == 'eoq' else '个'
    if key == 'cost':
        return '元/年'
    if key == 'exp_profit':
        return '元/天'
    raise KeyError('%s/%s' % (tpl, key))


def main():
    rows = []
    md = ['# P5 外部题独立真值', '',
          '> 由 `external_truth.py` 生成；只使用标准库闭式公式，未 import simcore。',
          '> 这些题不进入 64 题主表，不参与 tau* 标定。', '',
          '| task | template | 参数 | 关键真值 | 公式 |', '|---|---|---|---|---|']
    for sp in specs():
        raw, tp = _truth_for(sp)
        contract = {k: _unit_for(sp['template'], k) for k in sp['print_keys']}
        usable_raw = {k: v for k, v in raw.items() if k not in ('e_over', 'e_under', 'z', 'frac')}
        p_out = dict(sp['params'])
        if 'lam' in p_out:
            p_out['lambda'] = p_out.pop('lam')
        row = dict(
            task_id=sp['task_id'], template=sp['template'], kind=sp['kind'],
            params=p_out, busy_def=sp['busy_def'],
            truth_raw=usable_raw, truth_print=tp, output_contract=contract,
            desc_zh=sp['desc_zh'], desc_en=sp['desc_en'],
            simpy_ref={'engine': 'external_truth.py (closed form)', 'kwargs': {}, 'ready': False},
            source_note=sp['source_note'],
        )
        rows.append(row)
        vals = ', '.join('%s=%.6g' % (k, v) for k, v in tp.items())
        md.append('| %s | %s | `%s` | %s | 见脚本函数 |'
                  % (sp['task_id'], sp['template'],
                     json.dumps(p_out, ensure_ascii=False), vals))
    with open(TASKS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with open(MD_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md) + '\n')
    print('wrote %d tasks -> %s' % (len(rows), TASKS_OUT))
    print('wrote %s' % MD_OUT)
    for r in rows:
        print('%s %s %s' % (r['task_id'], r['template'],
                            json.dumps(r['truth_print'], ensure_ascii=True)))


if __name__ == '__main__':
    main()
