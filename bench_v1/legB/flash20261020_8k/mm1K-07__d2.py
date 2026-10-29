import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu = 1.0 / 6.0
    cap = 6
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cap = 7
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
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wsum = 0.0
        wcnt = 0
        arr = 0
        dep = 0
        blk = 0
        waited = 0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                dt = H - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_occ += min(n, cap) * dt
                t = H
                break
            if t >= warm:
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
                area_occ += min(n, cap) * dt
            t = nt
            if rng.random() < lam / rate:
                if t >= warm:
                    arr += 1
                if n < cap:
                    svc = rng.expovariate(mu)
                    if n == 0 and not busy:
                        busy = True
                        rem = svc
                        n = 1
                        if t >= warm:
                            wsum += 0.0
                            wcnt += 1
                    else:
                        queue.append((t, svc))
                        n += 1
                else:
                    if t >= warm:
                        blk += 1
            else:
                if busy:
                    if t >= warm:
                        dep += 1
                    if queue:
                        at, svc = queue.pop(0)
                        rem = svc
                        if t >= warm:
                            wsum += (t - at)
                            wcnt += 1
                            waited += 1
                    else:
                        busy = False
                        n = 0
                        rem = 0.0
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_occ / win / cap if win > 0 else 0.0
        W = (wsum / wcnt) if wcnt > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / arr if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    ns = a.seeds
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr_m = tot_arr / ns
    dep_m = tot_dep / ns
    blk_m = tot_blk / ns
    dep_rate = dep_m / win if win > 0 else 0.0
    lam_eff = arr_m / win if win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_m,
        'blk': blk_m,
        'busy_util': busy_util,
        'dep': dep_m,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
