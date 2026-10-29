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
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    tot_depn = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = rng.expovariate(lam)
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        area_wait = 0.0
        last = 0.0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        n_wait = 0
        sum_wait = 0.0
        while True:
            if not busy:
                nxt = arr_t
                if nxt > H:
                    dt = H - t
                    if t >= warm:
                        area_n += n * dt
                        area_busy += (1 if busy else 0) * dt
                        area_util += min(n, K) * dt
                        area_wait += 0.0
                    t = H
                    break
                dt = nxt - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += 0.0
                    area_util += min(n, K) * dt
                t = nxt
                n_arr += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    if n == 1:
                        busy = True
                        rem = svc
                        if t >= warm:
                            pass
                    else:
                        pass
                    if n == 1:
                        pass
                else:
                    n_blk += 1
                arr_t = t + rng.expovariate(lam)
            else:
                nxt = min(arr_t, t + rem)
                if nxt > H:
                    dt = H - t
                    if t >= warm:
                        area_n += n * dt
                        area_busy += dt
                        area_util += min(n, K) * dt
                    t = H
                    break
                dt = nxt - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += dt
                    area_util += min(n, K) * dt
                t = nxt
                if arr_t <= t + 1e-12 and abs(arr_t - t) < 1e-9:
                    n_arr += 1
                    if n < K:
                        n += 1
                        svc = rng.expovariate(mu)
                        if n == 1:
                            busy = True
                            rem = svc
                    else:
                        n_blk += 1
                    arr_t = t + rng.expovariate(lam)
                else:
                    rem -= dt
                    if rem <= 1e-12:
                        n -= 1
                        n_dep += 1
                        if n > 0:
                            rem = rng.expovariate(mu)
                        else:
                            busy = False
                            rem = 0.0
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        util = area_util / (win * K) if win > 0 else 0.0
        pl = n_blk / n_arr if n_arr > 0 else 0.0
        pw = n_wait / n_dep if n_dep > 0 else 0.0
        W = L / (n_dep / win) if n_dep > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += n_arr
        tot_dep += n_dep
        tot_blk += n_blk
        tot_busy += bf
        tot_util += util
        tot_wait += sum_wait
        tot_waitn += n_wait
        tot_depn += n_dep
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    win = H - warm
    dep_rate = (tot_dep / ns) / win if win > 0 else 0.0
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
        'arr': tot_arr / ns,
        'blk': tot_blk / ns,
        'busy_util': tot_util / ns,
        'busy_occupied': bf,
        'dep': tot_dep / ns,
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
