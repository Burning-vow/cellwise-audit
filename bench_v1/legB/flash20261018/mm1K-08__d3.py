import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
    K = 6
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 7
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wsum = 0.0
        wcnt = 0
        arr = 0
        dep = 0
        blk = 0
        waiters = 0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            t_next = t + dt
            if t_next > H:
                dt = H - t
                if t < H:
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_occ += (1.0 if n > 0 else 0.0) * dt
                t = H
                break
            area_n += n * dt
            area_busy += (1.0 if busy else 0.0) * dt
            area_occ += (1.0 if n > 0 else 0.0) * dt
            t = t_next
            if rng.random() < lam / rate:
                arr += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        next_dep = t + svc
                    else:
                        waiters += 1
                        if not hasattr(rng, '_q'):
                            pass
                        if 'q' not in dir():
                            q = []
                        q.append((t, svc))
                else:
                    blk += 1
            else:
                dep += 1
                n -= 1
                if n > 0:
                    if 'q' in dir() and q:
                        at, svc = q.pop(0)
                        wsum += t - at
                        wcnt += 1
                        next_dep = t + svc
                    else:
                        busy = False
                        next_dep = float('inf')
                else:
                    busy = False
                    next_dep = float('inf')
        win = H - warm
        if win <= 0:
            win = H
        per_L.append(area_n / H)
        per_bf.append(area_occ / H)
        per_pl.append(blk / arr if arr > 0 else 0.0)
        per_pw.append(wcnt / arr if arr > 0 else 0.0)
        per_W.append(wsum / wcnt if wcnt > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    seeds_used = a.seeds
    L = sum(per_L) / seeds_used
    W = sum(per_W) / seeds_used
    bf = sum(per_bf) / seeds_used
    pl = sum(per_pl) / seeds_used
    pw = sum(per_pw) / seeds_used
    arr_avg = tot_arr / seeds_used
    dep_avg = tot_dep / seeds_used
    blk_avg = tot_blk / seeds_used
    dep_rate = dep_avg / H
    busy_util = L / K
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(seeds_used)],
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': arr_avg / H,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
