import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    K = 6
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1
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
        last_t = 0.0
        while t < H:
            if busy:
                rate = lam + mu
            else:
                rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                nt = H
            if nt > warm:
                w0 = max(t, warm)
                dur = nt - w0
                if dur > 0:
                    area_n += n * dur
                    if busy:
                        area_busy += dur
                        area_util += min(n, K) * dur
            t = nt
            if t >= H:
                break
            if busy and t >= next_dep - 1e-12:
                n -= 1
                dep_c += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                if n >= K:
                    blk_c += 1
                else:
                    n += 1
                    if not busy:
                        busy = True
                        next_dep = t + rng.expovariate(mu)
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_util / (K * win) if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / dep_c if dep_c > 0 else 0.0
        W = wait_sum / dep_c if dep_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += bf
        tot_util += bu
        tot_wait += wait_sum
        tot_waitn += wait_n
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    win = H - warm
    arr_rate = tot_arr / (ns * win) if win > 0 else 0.0
    dep_rate = tot_dep / (ns * win) if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': 'hour',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr_rate,
        'blk': tot_blk / ns,
        'busy_util': tot_util / ns,
        'busy_occupied': bf,
        'dep': tot_dep / ns,
        'dep_rate': dep_rate,
        'lam_eff': arr_rate,
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
