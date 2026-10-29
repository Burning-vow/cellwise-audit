import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
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
        busy = False
        rem = 0.0
        arr = 0; dep = 0; blk = 0
        area_n = 0.0; area_busy = 0.0; area_wait = 0.0
        wsum = 0.0; wcnt = 0
        wq = []
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += (1.0 if busy else 0.0) * (H - t)
                    area_wait += len(wq) * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += (1.0 if busy else 0.0) * (nt - t)
            area_wait += len(wq) * (nt - t)
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep += 1
                    if wq:
                        wq.pop(0)
                        busy = True
                        rem = rng.expovariate(mu)
                        n += 1
                        if t >= warm:
                            wsum += 0.0
                            wcnt += 1
            else:
                if rng.random() < lam / rate:
                    arr += 1
                    if n < K:
                        n += 1
                        if not busy:
                            busy = True
                            rem = rng.expovariate(mu)
                        else:
                            wq.append(t)
                    else:
                        blk += 1
        win = H - warm
        if win <= 0:
            win = H
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = (arr - blk) / arr if arr > 0 else 0.0
        W = (area_wait / win) / (arr / win) if arr > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot_arr += arr; tot_dep += dep; tot_blk += blk
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    win = H - warm
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / win if win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'busy_occupied': bf, 'dep': dep_avg, 'dep_rate': dep_rate,
        'lam_eff': lam, 'p_wait': pw,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
