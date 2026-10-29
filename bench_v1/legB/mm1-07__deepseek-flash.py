import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
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
    tot_dep_rate = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area_n = 0.0
        area_busy = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        sum_w = 0.0
        cnt_w = 0
        last = 0.0
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                t_arr = t + dt
                if t_arr > H:
                    if t < H:
                        area_n += n * (H - t)
                        area_busy += (1.0 if busy else 0.0) * (H - t)
                    break
                if t < H:
                    area_n += n * (t_arr - t)
                    area_busy += (1.0 if busy else 0.0) * (t_arr - t)
                t = t_arr
                svc = rng.expovariate(mu)
                n += 1
                if t >= warm:
                    arr_w += 1
                if not busy:
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        pass
                else:
                    pass
            else:
                dt = rng.expovariate(lam)
                t_arr = t + dt
                t_dep = next_dep
                if t_arr < t_dep:
                    if t_arr > H:
                        if t < H:
                            area_n += n * (H - t)
                            area_busy += 1.0 * (H - t)
                        break
                    if t < H:
                        area_n += n * (t_arr - t)
                        area_busy += 1.0 * (t_arr - t)
                    t = t_arr
                    svc = rng.expovariate(mu)
                    n += 1
                    if t >= warm:
                        arr_w += 1
                else:
                    if t_dep > H:
                        if t < H:
                            area_n += n * (H - t)
                            area_busy += 1.0 * (H - t)
                        break
                    if t < H:
                        area_n += n * (t_dep - t)
                        area_busy += 1.0 * (t_dep - t)
                    t = t_dep
                    n -= 1
                    if t >= warm:
                        dep_w += 1
                        sum_w += (t - 0.0)
                        cnt_w += 1
                    if n > 0:
                        next_dep = t + rng.expovariate(mu)
                    else:
                        busy = False
                        next_dep = float('inf')
        win = H - warm
        Ls = area_n / win if win > 0 else 0.0
        Ws = (Ls / (lam * c)) * 60.0 if lam > 0 else 0.0
        bs = area_busy / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += 0.0
        win_total += win
        tot_dep_rate += (dep_w / win) if win > 0 else 0.0

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep_rate / ns
    win = win_total / ns

    out = {
        'L': L,
        'W': W,
        'arr': arr,
        'blk': blk,
        'dep': dep,
        'dep_rate': dep_rate,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': 'hour',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win * 60.0
    }
    print(json.dumps(out))

main()
