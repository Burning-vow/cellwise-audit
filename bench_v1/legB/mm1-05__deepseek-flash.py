import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0
    mu = 10.0
    c = 1.0
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c * 1.2
    seeds = [a.seed_start + i for i in range(a.seeds)]
    H = a.horizon
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area_n = 0.0
    tot_area_b = 0.0
    tot_wait = 0.0
    tot_dep_n = 0
    win_total = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        cur_end = None
        area_n = 0.0
        area_b = 0.0
        wait_sum = 0.0
        dep_n = 0
        arr_n = 0
        blk_n = 0
        last = 0.0
        while True:
            if cur_end is not None and cur_end <= next_arr:
                ev = cur_end
            else:
                ev = next_arr
            if ev > H:
                dt = H - last
                if last >= warm:
                    area_n += n * dt
                    area_b += (1.0 if busy > 0 else 0.0) * dt
                break
            dt = ev - last
            if last >= warm:
                area_n += n * dt
                area_b += (1.0 if busy > 0 else 0.0) * dt
            last = ev
            if cur_end is not None and cur_end <= next_arr:
                t = cur_end
                n -= 1
                busy = 0.0
                dep_n += 1
                if queue:
                    cust = queue.pop(0)
                    w = t - cust[0]
                    if t >= warm:
                        wait_sum += w
                    cur_end = t + cust[1]
                    busy = 1.0
                    n += 1
                else:
                    cur_end = None
            else:
                t = next_arr
                svc = rng.expovariate(mu) / c
                cust = (t, svc)
                if t >= warm:
                    arr_n += 1
                if cur_end is None:
                    cur_end = t + svc
                    busy = 1.0
                    n += 1
                else:
                    queue.append(cust)
                    n += 1
                    if t >= warm:
                        blk_n += 1
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        win_total += win
        Ls = area_n / win
        Bs = area_b / win
        Ws = Ls / (lam * c) if lam > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(Bs)
        tot_area_n += area_n
        tot_area_b += area_b
        tot_arr += arr_n
        tot_dep += dep_n
        tot_blk += blk_n
        tot_wait += wait_sum
        tot_dep_n += dep_n
    L = tot_area_n / win_total
    W = L / (lam * c) if lam > 0 else 0.0
    arr_rate = tot_arr / win_total
    dep_rate = tot_dep / win_total
    blk_rate = tot_blk / win_total
    out = {
        'L': L,
        'W': W,
        'arr': arr_rate,
        'blk': blk_rate,
        'dep': dep_rate,
        'dep_rate': dep_rate,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': 'hour',
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': win_total / len(seeds)
    }
    print(json.dumps(out))

main()
