import argparse, json, random, math, heapq

def run_seed(seed, horizon, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    warm = horizon * 0.25
    n = 0
    area_L = 0.0
    area_busy = 0.0
    arr_w = 0
    dep_w = 0
    wait_sum = 0.0
    served_wait = 0
    waited_cnt = 0
    arr_t = []
    next_arr = rng.expovariate(lam)
    next_dep = None
    while t < horizon:
        if next_dep is None:
            t1 = next_arr if next_arr <= horizon else horizon
            t2 = horizon
            dt = min(t1, t2) - t
            dt2 = dt
        else:
            t1 = next_arr if next_arr <= horizon else horizon
            t2 = next_dep if next_dep <= horizon else horizon
            dt = min(t1, t2) - t
            dt2 = dt
        if t + dt2 > warm:
            w0 = max(t, warm)
            w1 = min(t + dt2, horizon)
            eff = max(0.0, w1 - w0)
            area_L += n * eff
            area_busy += (1 if n > 0 else 0) * eff
        t += dt2
        if t >= horizon:
            break
        if next_arr <= (next_dep if next_dep is not None else float('inf')):
            if t + 0 <= warm:
                pass
            n += 1
            if t >= warm:
                arr_w += 1
            st = rng.expovariate(mu)
            arr_t.append((t, st))
            next_arr = t + rng.expovariate(lam)
        else:
            a, st = arr_t.pop(0)
            if t >= warm:
                wait_sum += (t - a)
                served_wait += 1
                if (t - a) > 0:
                    waited_cnt += 1
                dep_w += 1
            n -= 1
        if n > 0 and next_dep is None:
            next_dep = t
        next_dep = t if n > 0 else None
        if n > 0:
            a, st = arr_t[0]
            if next_dep == t and st is None:
                pass
    return arr_w, dep_w, area_L, area_busy, wait_sum, served_wait, waited_cnt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu = 6.0, 12.0
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    elif a.pert == 'c_up':
        mu *= 1.05
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    win = a.horizon * 0.75
    pL, pW, pBF, pPW = [], [], [], []
    tot_arr = tot_dep = 0
    for s in seed_list:
        arr_w, dep_w, area_L, area_busy, wait_sum, served, waited = run_seed(s, a.horizon, lam, mu)
        pL.append(area_L / win)
        pBF.append(area_busy / win)
        pW.append(wait_sum / served if served > 0 else 0.0)
        pPW.append(waited / served if served > 0 else 0.0)
        tot_arr += arr_w
        tot_dep += dep_w
    k = len(seed_list)
    arr = tot_arr / k
    dep = tot_dep / k
    L = sum(pL) / k
    W = sum(pW) / k
    busy_frac = sum(pBF) / k
    p_wait = sum(pPW) / k
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': a.horizon, 'seed_list': seed_list, 'seeds_used': k,
        'time_unit': 'hour', 'win': win,
        'arr': arr, 'blk': 0.0, 'busy_util': busy_frac, 'busy_occupied': busy_frac,
        'dep': dep, 'dep_rate': dep / win, 'lam_eff': arr / win,
        'p_loss': 0.0,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pBF,
        'per_seed_p_loss': [0.0] * k, 'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
