import json, argparse, heapq, random

def run(seed, lam, mu, c, horizon):
    r = random.Random(seed)
    t = 0.0; n = 0; busy = 0
    area_L = 0.0; area_busy = 0.0
    arr = dep = blk = waits = waits_n = 0
    t0 = 0.25 * horizon
    warm = False
    ev = []
    heapq.heappush(ev, (r.expovariate(lam), 'a'))
    dep_t = float('inf')
    while True:
        nt = min(dep_t, ev[0][0] if ev else float('inf'))
        if nt >= horizon: break
        area_L += n * (nt - t)
        area_busy += (1 if n > 0 else 0) * (nt - t)
        t = nt
        if not warm and t >= t0:
            warm = True
            area_L = 0.0; area_busy = 0.0
            arr = dep = blk = waits = waits_n = 0
        if dep_t <= (ev[0][0] if ev else float('inf')):
            n -= 1; busy -= 1
            dep += 1
            dep_t = r.expovariate(mu) if n > 0 else float('inf')
        else:
            _, k = heapq.heappop(ev)
            arr += 1
            if n < c:
                waits_n += 1
                if n == 0:
                    waits += 0
                n += 1; busy += 1
                if n == 1:
                    dep_t = t + r.expovariate(mu)
            else:
                blk += 1
            heapq.heappush(ev, (t + r.expovariate(lam), 'a'))
    win = horizon - t0
    if win <= 0: win = horizon
    L = area_L / win
    bf = area_busy / win
    W = waits / waits_n if waits_n else 0.0
    pl = blk / arr if arr else 0.0
    pw = waits_n / arr if arr else 0.0
    return dict(L=L, W=W, busy_frac=bf, p_loss=pl, arr=arr, dep=dep, blk=blk,
                p_wait=pw, dep_rate=dep / win, lam_eff=(arr - blk) / win,
                busy_util=busy / win, busy_occupied=bf)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', default='none')
    a = ap.parse_args()
    lam, mu = 6.0, 12.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': pass
    per = [dict(zip(['L','W','busy_frac','p_loss','p_wait'],
        [x['L'], x['W'], x['busy_frac'], x['p_loss'], x['p_wait']]))
        for x in (run(s, lam, mu, 6, a.horizon) for s in range(a.seed_start, a.seed_start + a.seeds))]
    runs = [run(s, lam, mu, 6, a.horizon) for s in range(a.seed_start, a.seed_start + a.seeds)]
    n = len(runs)
    out = {
        'L': sum(x['L'] for x in runs) / n,
        'W': sum(x['W'] for x in runs) / n,
        'busy_frac': sum(x['busy_frac'] for x in runs) / n,
        'p_loss': sum(x['p_loss'] for x in runs) / n,
        'busy_util': sum(x['busy_util'] for x in runs) / n,
        'busy_occupied': sum(x['busy_occupied'] for x in runs) / n,
        'p_wait': sum(x['p_wait'] for x in runs) / n,
        'arr': sum(x['arr'] for x in runs) / n,
        'dep': sum(x['dep'] for x in runs) / n,
        'blk': sum(x['blk'] for x in runs) / n,
        'dep_rate': sum(x['dep_rate'] for x in runs) / n,
        'lam_eff': sum(x['lam_eff'] for x in runs) / n,
        'runtime_units': a.horizon, 'win': a.horizon * 0.75,
        'seed_list': list(range(a.seed_start, a.seed_start + n)),
        'seeds_used': n, 'time_unit': 'hour',
        'per_seed_L': [x['L'] for x in runs],
        'per_seed_W': [x['W'] for x in runs],
        'per_seed_busy_frac': [x['busy_frac'] for x in runs],
        'per_seed_p_loss': [x['p_loss'] for x in runs],
        'per_seed_p_wait': [x['p_wait'] for x in runs],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
