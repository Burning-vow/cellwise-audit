import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0
    tot_waited = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = dep_w = blk_w = 0.0
        wait_sum = 0.0
        served = 0
        waited = 0
        last = 0.0
        while t < H:
            dt = min(next_arr, next_dep) - t
            if t >= warm:
                area += n * dt
                busy_area += min(n, c) * dt
            t += dt
            if t >= H:
                break
            if next_arr <= next_dep:
                if t >= warm:
                    arr_w += 1
                if n < c:
                    n += 1
                    busy = 1
                    st = rng.expovariate(mu)
                    next_dep = t + st
                else:
                    if t >= warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                n -= 1
                if n < c:
                    busy = 0
                if t >= warm:
                    dep_w += 1
                if n >= c:
                    st = rng.expovariate(mu)
                    next_dep = t + st
                else:
                    next_dep = float('inf')
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / (win * c) if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(L / (dep_w / win) if dep_w > 0 else 0.0)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_win += win

    L = tot_area / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    busy_frac = tot_busy / (tot_win * c) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 0.0
    lam_eff = tot_dep / tot_win if tot_win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': tot_win / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_util': busy_frac, 'busy_occupied': busy_frac,
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
