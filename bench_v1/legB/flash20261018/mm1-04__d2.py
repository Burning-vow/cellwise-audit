import json, random, argparse, math

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
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_area = 0.0
    tot_waited = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        w_area = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        waited_c = 0
        served_c = 0
        busy_time = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    area += n * (H - t)
                    busy_time += H - t
                else:
                    area += n * (H - t)
                break
            area += n * dt
            if busy:
                busy_time += dt
            t += dt
            if busy:
                n -= 1
                dep_c += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = True
                    next_dep = t + svc
                else:
                    n += 1
        # window stats
        wlen = H - warm
        # recompute windowed area by re-simulating? approximate: use full-run scaled
        # We'll do a second pass simulation for windowed stats
        rng2 = random.Random(s + 1000000)
        t2 = 0.0
        n2 = 0
        busy2 = False
        nd2 = float('inf')
        w_area = 0.0
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_waited = 0
        w_served = 0
        w_busy = 0.0
        w_wait_sum = 0.0
        while True:
            if busy2:
                dt2 = nd2 - t2
            else:
                dt2 = rng2.expovariate(lam)
            if t2 + dt2 > H:
                if t2 < H and t2 + dt2 > warm:
                    lo = max(t2, warm)
                    w_area += n2 * (H - lo)
                    if busy2:
                        w_busy += H - lo
                break
            lo = max(t2, warm)
            hi = t2 + dt2
            if hi > warm:
                w_area += n2 * (hi - lo)
                if busy2:
                    w_busy += hi - lo
            t2 += dt2
            if busy2:
                n2 -= 1
                if t2 >= warm:
                    w_dep += 1
                if n2 == 0:
                    busy2 = False
                    nd2 = float('inf')
                else:
                    nd2 = t2 + rng2.expovariate(mu)
            else:
                if t2 >= warm:
                    w_arr += 1
                svc = rng2.expovariate(mu)
                if n2 == 0:
                    n2 = 1
                    busy2 = True
                    nd2 = t2 + svc
                else:
                    n2 += 1
        Ls = w_area / wlen if wlen > 0 else 0.0
        bf = w_busy / wlen if wlen > 0 else 0.0
        Ws = Ls / (lam * (1 - 0)) if lam > 0 else 0.0
        # W via Little: L = lam_eff * W
        lam_eff = w_dep / wlen if wlen > 0 else 0.0
        Ws = Ls / lam_eff if lam_eff > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if bf > 0 else 0.0)
        tot_arr += w_arr
        tot_dep += w_dep
        tot_blk += w_blk
        tot_busy += w_busy
        tot_area += w_area
        tot_served += w_dep
    ns = len(seeds)
    wlen = H - warm
    L = tot_area / (wlen * ns) if ns > 0 and wlen > 0 else 0.0
    busy_frac = tot_busy / (wlen * ns) if ns > 0 and wlen > 0 else 0.0
    dep_rate = tot_dep / (wlen * ns) if ns > 0 and wlen > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    arr_avg = tot_arr / ns if ns > 0 else 0.0
    dep_avg = tot_dep / ns if ns > 0 else 0.0
    blk_avg = tot_blk / ns if ns > 0 else 0.0
    p_loss = blk_avg / (arr_avg + blk_avg) if (arr_avg + blk_avg) > 0 else 0.0
    p_wait = 1.0 - (1.0 - busy_frac) if busy_frac > 0 else 0.0
    p_wait = busy_frac
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': wlen,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_frac,
        'dep': dep_avg,
        'dep_rate': dep_rate * 60.0,
        'lam_eff': dep_rate * 60.0,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
