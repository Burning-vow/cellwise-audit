import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass

    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

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
        sum_wait = 0.0
        dep_times = []
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area_n += n * seg
                        area_busy += (1.0 if busy else 0.0) * seg
                    elif t + seg > warm:
                        seg2 = t + seg - warm
                        area_n += n * seg2
                        area_busy += (1.0 if busy else 0.0) * seg2
                break
            if t >= warm:
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
            elif t + dt > warm:
                seg2 = t + dt - warm
                area_n += n * seg2
                area_busy += (1.0 if busy else 0.0) * seg2
            t += dt
            if busy:
                n -= 1
                busy = False
                next_dep = float('inf')
                if t >= warm:
                    dep_w += 1
                    dep_times.append(t)
            else:
                n += 1
                svc = rng.expovariate(mu)
                next_dep = t + svc
                busy = True
                if t >= warm:
                    arr_w += 1
        win = H - warm
        L = area_n / win
        busy_frac = area_busy / win
        W = L / (lam) if lam > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_busy.append(busy_frac)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += 0.0
        tot_dep_rate += dep_w / win
        win_total += win

    ns = len(seeds)
    L_avg = sum(per_L) / ns
    W_avg = sum(per_W) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate_avg = tot_dep_rate / ns
    win_avg = win_total / ns

    out = {
        'L': L_avg,
        'W': W_avg,
        'arr': arr_avg,
        'blk': blk_avg,
        'dep': dep_avg,
        'dep_rate': dep_rate_avg,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_avg,
    }
    print(json.dumps(out))

main()
