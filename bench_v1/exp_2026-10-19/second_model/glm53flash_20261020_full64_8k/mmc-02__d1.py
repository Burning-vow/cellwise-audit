import json, argparse, heapq, random, math

def run(seed, horizon, lam, mu, c):
    rng = random.Random(seed)
    t = 0.0; warm = horizon * 0.25
    busy = 0; q = 0; served = 0; arr = 0; dep = 0; lost = 0
    nwait = 0; narr = 0
    areaN = 0.0; areaBusy = 0.0
    wait_sum = 0.0; soj_sum = 0.0
    t_prev = 0.0
    eventq = []
    heapq.heappush(eventq, (rng.expovariate(lam), 'arr'))
    while eventq:
        t, ev = heapq.heappop(eventq)
        if t > horizon: break
        if t > warm:
            areaN += (t - t_prev) * (busy + q)
            areaBusy += (t - t_prev) * min(busy + q, c)
        else:
            t_prev = t
            pass
        t_prev = t
        if ev == 'arr':
            arr += 1
            st = rng.expovariate(mu)
            if t >= warm: narr += 1
            if busy + q < c:
                heapq.heappush(eventq, (t + st, ('dep', st)))
                busy += 1
            else:
                q += 1
                if t >= warm: nwait += 1
            heapq.heappush(eventq, (t + rng.expovariate(lam), 'arr'))
        else:
            _, st = ev
            dep += 1
            if t >= warm:
                soj_sum += st
                served += 1
            if q > 0:
                q -= 1
                heapq.heappush(eventq, (t + st, ('dep', st)))
            else:
                busy -= 1
    win = horizon - warm
    L = areaN / win
    bf = areaBusy / win / c
    W = soj_sum / served if served else 0.0
    pw = nwait / narr if narr else 0.0
    return dict(L=L, W=W, busy_frac=bf, busy_util=bf, p_wait=pw,
                dep_rate=dep/win, arr=arr/win, dep=dep/win, blk=0.0,
                p_loss=0.0, busy_occupied=1.0 if dep>0 else 0.0)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=2000)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', default='none')
    a = p.parse_args()
    lam, mu, c = 8.0, 6.0, 2
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c = 3
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [run(s, a.horizon, lam, mu, c) for s in seeds]
    n = len(res)
    out = {
        'L': sum(r['L'] for r in res)/n,
        'W': sum(r['W'] for r in res)/n,
        'busy_frac': sum(r['busy_frac'] for r in res)/n,
        'p_wait': sum(r['p_wait'] for r in res)/n,
        'busy_util': sum(r['busy_util'] for r in res)/n,
        'busy_occupied': sum(r['busy_occupied'] for r in res)/n,
        'arr': sum(r['arr'] for r in res)/n,
        'dep': sum(r['dep'] for r in res)/n,
        'blk': 0.0,
        'dep_rate': sum(r['dep_rate'] for r in res)/n,
        'lam_eff': sum(r['arr'] for r in res)/n,
        'p_loss': 0.0,
        'runtime_units': a.horizon,
        'time_unit': 'hour',
        'win': a.horizon * 0.75,
        'seed_list': seeds,
        'seeds_used': n,
        'per_seed_L': [r['L'] for r in res],
        'per_seed_W': [r['W'] for r in res],
        'per_seed_busy_frac': [r['busy_frac'] for r in res],
        'per_seed_p_wait': [r['p_wait'] for r in res],
        'per_seed_p_loss': [0.0]*n,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
