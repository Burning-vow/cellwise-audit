import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 5.0
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr = 0
        blk = 0
        dep = 0
        area_n = 0.0
        area_busy = 0.0
        area_wait = 0.0
        waiters = 0
        wait_start = []
        win_arr = 0
        win_blk = 0
        win_dep = 0
        win_area_n = 0.0
        win_area_busy = 0.0
        win_area_wait = 0.0
        win_waiters = 0
        win_wait_start = []
        win_len = 0.0
        while t < H:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                dt = H - t
                nt = H
            in_win = t >= warm
            if in_win:
                win_area_n += n * dt
                win_area_busy += (1.0 if busy else 0.0) * dt
                win_area_wait += win_waiters * dt
                win_len += dt
            if nt >= H:
                t = H
                break
            t = nt
            if busy and rng.random() < mu / rate:
                busy = False
                rem = 0.0
                dep += 1
                if t >= warm:
                    win_dep += 1
                if waiters > 0:
                    waiters -= 1
                    if t >= warm:
                        win_waiters -= 1
                    ws = wait_start.pop(0)
                    if t >= warm:
                        win_area_wait += 0
                    busy = True
                    rem = rng.expovariate(mu)
                    if t >= warm:
                        win_waiters += 1
                        win_wait_start.append(t)
            else:
                arr += 1
                if t >= warm:
                    win_arr += 1
                if n < K:
                    n += 1
                    if not busy:
                        busy = True
                        rem = rng.expovariate(mu)
                    else:
                        waiters += 1
                        wait_start.append(t)
                        if t >= warm:
                            win_waiters += 1
                            win_wait_start.append(t)
                else:
                    blk += 1
                    if t >= warm:
                        win_blk += 1
        L = win_area_n / win_len if win_len > 0 else 0.0
        bf = win_area_busy / win_len if win_len > 0 else 0.0
        W = (win_area_wait / win_dep) if win_dep > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = (win_waiters / win_arr) if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
    nseeds = len(seeds)
    L = sum(per_L) / nseeds
    W = sum(per_W) / nseeds
    bf = sum(per_bf) / nseeds
    pl = sum(per_pl) / nseeds
    pw = sum(per_pw) / nseeds
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': nseeds,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': 0.0,
        'blk': 0.0,
        'busy_util': bf,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': 0.0,
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
