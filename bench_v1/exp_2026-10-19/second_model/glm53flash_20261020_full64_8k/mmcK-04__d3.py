import argparse, json, random, heapq, math

def run_seed(seed, H, lam, mu, c, K, warm):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy = 0
    events = []
    heapq.heappush(events, (rng.expovariate(lam), 'arr'))
    arrive = 0.0; blocked = 0.0; depart = 0.0
    waited = 0.0; waited_n = 0
    area_n = 0.0; area_busy = 0.0; area_nonempty = 0.0
    last = 0.0
    t_w = warm * H
    sum_w = 0.0; sum_w_n = 0
    while events:
        t, ev = heapq.heappop(events)
        if t > H: break
        dt = t - last
        if t >= t_w:
            area_n += n * dt
            area_busy += busy * dt
            area_nonempty += (1.0 if n > 0 else 0.0) * dt
        last = t
        if ev == 'arr':
            arrive += 1
            st = rng.expovariate(mu)
            if n < K:
                if n >= c:
                    waited += st; waited_n += 1
                n += 1
                if n <= c: busy += 1
                heapq.heappush(events, (t + st, ('dep', st)))
            else:
                blocked += 1
            heapq.heappush(events, (t + rng.expovariate(lam), 'arr'))
        else:
            _, st = ev
            if t >= t_w: sum_w += st; sum_w_n += 1
            n -= 1
            depart += 1
            if n >= c: busy = c
            else: busy = n
    win = H - t_w
    return dict(arr=arrive/win, dep=depart/win, blk=blocked/win,
                L=area_n/win, busy_frac=area_nonempty/win,
                busy_util=area_busy/win/c, p_loss=blocked/max(1.0, arrive),
                p_wait=waited_n/max(1, sum_w_n + 0), W=(sum_w/sum_w_n*60 if sum_w_n else 0.0),
                dep_rate=depart/win, lam_eff=(arrive-blocked)/win)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c, K = 2, 4
    lam, mu = 8.0, 10.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c += 1
    warm = 0.25
    seeds = [a.seed_start + i for i in range(a.seeds)]
    rs = [run_seed(s, a.horizon, lam, mu, c, K, warm) for s in seeds]
    n = len(rs)
    avg = lambda k: sum(r[k] for r in rs)/n
    out = {
        'L': avg('L'), 'W': avg('W'), 'busy_frac': avg('busy_frac'),
        'p_loss': avg('p_loss'), 'runtime_units': 'hours',
        'seed_list': seeds, 'seeds_used': n, 'time_unit': 'hour',
        'win': a.horizon*(1-warm),
        'arr': avg('arr'), 'blk': avg('blk'), 'busy_util': avg('busy_util'),
        'busy_occupied': avg('busy_frac'), 'dep': avg('dep'), 'dep_rate': avg('dep_rate'),
        'lam_eff': avg('lam_eff'), 'p_wait': avg('p_wait'),
        'per_seed_L': [r['L'] for r in rs], 'per_seed_W': [r['W'] for r in rs],
        'per_seed_busy_frac': [r['busy_frac'] for r in rs],
        'per_seed_p_loss': [r['p_loss'] for r in rs],
        'per_seed_p_wait': [r['p_wait'] for r in rs],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
