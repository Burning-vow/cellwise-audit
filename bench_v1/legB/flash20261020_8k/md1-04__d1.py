import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy_area = 0.0
    tot_wait = tot_waited = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy_until = 0.0
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        waited = 0
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait = 0.0
        win_waited = 0
        last = 0.0
        while True:
            t += rng.expovariate(lam)
            if t > H:
                break
            svc = 1.0 / mu
            if t >= warm:
                win_area += n * (t - last)
                win_busy += (1 if n >= c else n) * (t - last)
            else:
                area += n * (t - last)
                busy_area += (1 if n >= c else n) * (t - last)
            last = t
            arr += 1
            if t >= warm:
                win_arr += 1
            if n >= c:
                blk += 1
                if t >= warm:
                    win_blk += 1
            else:
                n += 1
                start = max(t, busy_until)
                wait = start - t
                wait_sum += wait
                if wait > 0:
                    waited += 1
                if t >= warm:
                    win_wait += wait
                    if wait > 0:
                        win_waited += 1
                busy_until = start + svc
                dep += 1
                if t >= warm:
                    win_dep += 1
        if H >= warm:
            win_area += n * (H - last)
            win_busy += (1 if n >= c else n) * (H - last)
        else:
            area += n * (H - last)
            busy_area += (1 if n >= c else n) * (H - last)
        wl = H - warm
        if wl <= 0:
            wl = 1e-9
        Ls = win_area / wl
        Ws = (win_wait / win_dep) if win_dep > 0 else 0.0
        bfs = win_busy / wl
        pls = (win_blk / win_arr) if win_arr > 0 else 0.0
        pws = (win_waited / win_dep) if win_dep > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy_area += win_busy
        tot_wait += win_wait
        tot_waited += win_waited
        tot_win += wl

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_wait / tot_dep) if tot_dep > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    p_wait = (tot_waited / tot_dep) if tot_dep > 0 else 0.0
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': tot_win / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
