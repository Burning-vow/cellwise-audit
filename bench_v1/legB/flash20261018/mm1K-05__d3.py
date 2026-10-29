import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 6.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_busy = 0.0
        area_wait = 0.0
        arr_w = 0; dep_w = 0; blk_w = 0; wait_w = 0
        t_last = warm
        # event list: (time, type, patient)
        # type 0 arrival, 1 departure
        events = []
        t_next_arr = rng.expovariate(lam)
        events.append((t_next_arr, 0, None))
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, pat = events.pop(0)
            if te > H:
                break
            dt = te - t
            if t >= warm:
                area_n += n * dt
                area_busy += (1.0 if n > 0 else 0.0) * dt
                if n > 0:
                    area_wait += n * dt
            t = te
            if typ == 0:
                if t >= warm:
                    arr_w += 1
                if n < K:
                    svc = rng.expovariate(mu)
                    n += 1
                    if n == 1:
                        events.append((t + svc, 1, None))
                    else:
                        events.append((t + svc, 1, None))
                else:
                    if t >= warm:
                        blk_w += 1
                t_next_arr = t + rng.expovariate(lam)
                events.append((t_next_arr, 0, None))
            else:
                n -= 1
                if t >= warm:
                    dep_w += 1
                if n > 0:
                    svc = rng.expovariate(mu)
                    events.append((t + svc, 1, None))
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        W = (area_wait / dep_w) if dep_w > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = (arr_w - blk_w) / arr_w if arr_w > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
    ns = len(seeds)
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / win if win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': dep_rate,
        'p_wait': pw,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
