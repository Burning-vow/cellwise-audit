import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = tot_soj = 0.0
    tot_n = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy_until = 0.0
        area = 0.0
        busy_area = 0.0
        w_area = 0.0
        wsum = 0.0
        wcnt = 0
        arr = dep = blk = 0
        last = 0.0
        win = 0.0
        while True:
            t += rng.expovariate(lam)
            if t > H:
                break
            svc = 1.0 / mu
            if t >= warm:
                area += n * (t - last)
                busy_area += (1 if n >= c else 0) * (t - last)
                win += t - last
            last = t
            if n >= c:
                blk += 1
                if t >= warm:
                    pass
            else:
                arr += 1
                n += 1
                if n == 1:
                    busy_until = t + svc
                if t >= warm:
                    w_area += 0
            if n > 0 and t >= busy_until:
                pass
            while n > 0 and busy_until <= t:
                n -= 1
                dep += 1
                if n > 0:
                    busy_until = busy_until + svc
        if H > last:
            if H >= warm:
                area += n * (H - last)
                busy_area += (1 if n >= c else 0) * (H - last)
                win += H - last
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = L / (dep / win) if dep > 0 and win > 0 else 0.0
        pl = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        pw = 1.0 if blk > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_area
        tot_win += win

    L = tot_area / tot_win if tot_win > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    p_loss = tot_blk / (tot_arr + tot_blk) if (tot_arr + tot_blk) > 0 else 0.0
    p_wait = 1.0 if tot_blk > 0 else 0.0
    lam_eff = tot_arr / tot_win if tot_win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': bf,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'hour', 'win': tot_win / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_util': bf, 'busy_occupied': bf,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
        'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
