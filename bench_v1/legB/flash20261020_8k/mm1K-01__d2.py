import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        cap = cap + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    tot_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        arr_c = 0
        dep_c = 0
        blk_c = 0
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        wait_sum = 0.0
        wait_n = 0
        last = warm
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            ta = t + dt
            td = next_dep
            if ta < td:
                nt = ta
            else:
                nt = td
            if nt > H:
                nt = H
            if nt > last:
                area_n += n * (nt - last)
                area_busy += (1.0 if busy else 0.0) * (nt - last)
                area_util += (1.0 if busy else 0.0) * (nt - last)
                last = nt
            if nt >= H:
                t = H
                break
            if ta < td:
                t = ta
                arr_c += 1
                if n < cap:
                    n += 1
                    if n == 1:
                        busy = True
                        svc = rng.expovariate(mu)
                        next_dep = t + svc
                    else:
                        svc = rng.expovariate(mu)
                        if n == 1:
                            next_dep = t + svc
                else:
                    blk_c += 1
            else:
                t = td
                dep_c += 1
                n -= 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        util = area_util / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = 0.0
        W = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += area_busy
        tot_util += area_util
        tot_win += win
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    busy_util = (tot_util / tot_win) if tot_win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
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
