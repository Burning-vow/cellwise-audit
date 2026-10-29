"""库存观测量（q / exp_profit / cost）的 J1 对账。

criteria.OBSERVABLES 只有排队那五个，所以照原样跑的话，报童/EOQ 的 60 个变异件
会一个可判实例都没有、静默从主表里消失。这里补上，并刻意放在**独立模块**里：
不动 criteria.OBSERVABLES——Step 2 的标定表是照老常量出的，改了就会对不上分母。
"""
INV_OBS = ('q', 'exp_profit', 'cost')


def j1_inv(obs, task, taus=('0.01', '0.02', '0.03', '0.05')):
    from criteria import rel_dev          # 与 J1 排队侧同一个相对偏差定义
    truth = task.get('truth_print') or {}
    out = {}
    for o in INV_OBS:
        tv = truth.get(o)
        if tv is None:
            continue
        est = obs.get(o)
        if est is None:
            out[o] = dict(rel=None, est=None, truth=tv, status='field_missing')
            continue
        rel = rel_dev(est, tv)
        out[o] = dict(rel=rel, est=est, truth=tv, status='ok',
                      fired_at={t: (rel is not None and rel > float(t)) for t in taus})
    return out
