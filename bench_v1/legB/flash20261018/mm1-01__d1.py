import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
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
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area_n = 0.0
    tot_area_busy = 0.0
    tot_wait_time = 0.0
    tot_waiters = 0.0
    tot_served = 0.0
    win_total = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        arr_c = 0
        dep_c = 0
        blk_c = 0
        area_n = 0.0
        area_busy = 0.0
        wait_time = 0.0
        waiters = 0
        served = 0
        last_t = 0.0
        while True:
            if next_arr <= next_dep:
                nt = next_arr
            else:
                nt = next_dep
            if nt > H:
                dt = H - last_t
                if last_t >= warm:
                    area_n += n * dt
                    area_busy += (1 if busy else 0) * dt
                elif nt > warm:
                    dt2 = H - warm
                    area_n += n * dt2
                    area_busy += (1 if busy else 0) * dt2
                break
            dt = nt - last_t
            if last_t >= warm:
                area_n += n * dt
                area_busy += (1 if busy else 0) * dt
            elif nt > warm:
                dt2 = nt - warm
                area_n += n * dt2
                area_busy += (1 if busy else 0) * dt2
            last_t = nt
            if next_arr <= next_dep:
                t = next_arr
                arr_c += 1
                svc = rng.expovariate(mu)
                if n < 1:
                    n += 1
                    busy = 1
                    next_dep = t + svc
                    if t >= warm:
                        served += 1
                else:
                    blk_c += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = next_dep
                dep_c += 1
                n -= 1
                if n == 0:
                    busy = 0
                    next_dep = float('inf')
                else:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
        win = H - warm
        win_total += win
        Ls = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        Ws = Ls / (lam * (1 - 0)) if lam > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = 1.0 - (dep_c / arr_c) if arr_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area_n += area_n
        tot_area_busy += area_busy
    nseeds = a.seeds
    win_avg = win_total / nseeds if nseeds > 0 else 0.0
    L = sum(per_L) / nseeds if nseeds > 0 else 0.0
    W = sum(per_W) / nseeds if nseeds > 0 else 0.0
    bf = sum(per_bf) / nseeds if nseeds > 0 else 0.0
    pl = sum(per_pl) / nseeds if nseeds > 0 else 0.0
    pw = sum(per_pw) / nseeds if nseeds > 0 else 0.0
    arr_avg = tot_arr / nseeds if nseeds > 0 else 0.0
    dep_avg = tot_dep / nseeds if nseeds > 0 else 0.0
    blk_avg = tot_blk / nseeds if nseeds > 0 else 0.0
    dep_rate = dep_avg / win_avg if win_avg > 0 else 0.0
    lam_eff = arr_avg / win_avg if win_avg > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': pw,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': nseeds,
        'time_unit': 'minute',
        'win': win_avg,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
