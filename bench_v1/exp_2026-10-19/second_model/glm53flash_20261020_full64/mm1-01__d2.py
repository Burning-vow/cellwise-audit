import argparse, heapq, json, random

def run_seed(seed, lam, mu, t_end, warm):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy = 0.0
    area = 0.0
    s_wait = 0.0
    n_wait = 0
    n_sys = 0
    n_dep = 0
    arr = 0
    dep = 0
    blk = 0
    queue = []
    heapq.heappush(queue, (rng.expovariate(lam), 'a'))
    next_arr = rng.expovariate(lam)
    idle = True
    next_dep = None
    while t < t_end:
        times = [(next_arr, 'a')]
        if next_dep is not None:
            times.append((next_dep, 'd'))
        times.sort()
        t2, kind = times[0]
        if t2 >= t_end:
            t2 = t_end
        dt = t2 - t
        if t2 > warm:
            area += n * dt
            busy += (1 if n > 0 else 0) * dt
        t = t2
        if kind == 'a':
            st = rng.expovariate(mu)
            if idle:
                idle = False
                next_dep = t + st
                if t > warm:
                    s_wait += 0.0
            else:
                heapq.heappush(queue, st)
                if t > warm:
                    n_wait += 1
            n += 1
            if t > warm:
                arr += 1
                n_sys += 1
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t > warm:
                dep += 1
                n_dep += 1
            if queue:
                s = heapq.heappop(queue)
                next_dep = t + s
            else:
                idle = True
                next_dep = None
    win = t_end - warm
    Ws = []
    return {
        'L': area / win if win > 0 else 0.0,
        'busy_frac': busy / win if win > 0 else 0.0,
        'p_wait': (n_wait / arr) if arr > 0 else 0.0,
        'arr': arr / win if win > 0 else 0.0,
        'dep': dep / win if win > 0 else 0.0,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=lambda x: float(x), default=20000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu = 4.0, 10.0
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    warm = a.horizon * 0.25
    win = a.horizon - warm
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    ps = [run_seed(s, lam, mu, a.horizon, warm) for s in seed_list]
    L = sum(p['L'] for p in ps) / len(ps)
    busy = sum(p['busy_frac'] for p in ps) / len(ps)
    p_wait = sum(p['p_wait'] for p in ps) / len(ps)
    arr = sum(p['arr'] for p in ps) / len(ps)
    dep = sum(p['dep'] for p in ps) / len(ps)
    out = {
        'L': L,
        'W': (L / lam) * 60.0,
        'busy_frac': busy,
        'busy_util': busy,
        'busy_occupied': busy,
        'p_wait': p_wait,
        'p_loss': 0.0,
        'runtime_units': len(seed_list),
        'seed_list': seed_list,
        'seeds_used': len(seed_list),
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': 0.0,
        'dep': dep,
        'dep_rate': dep / win if win > 0 else 0.0,
        'lam_eff': dep / win if win > 0 else 0.0,
        'per_seed_L': [p['L'] for p in ps],
        'per_seed_W': [p['L'] / lam * 60.0 for p in ps],
        'per_seed_busy_frac': [p['busy_frac'] for p in ps],
        'per_seed_p_loss': [0.0 for _ in ps],
        'per_seed_p_wait': [p['p_wait'] for p in ps],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
