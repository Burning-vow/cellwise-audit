import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 3.0
    mean_s = 0.1
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    cs2 = cv * cv
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (cs2 - 1.0) / (cs2 + 1.0))))
    r1 = 2.0 * p * mean_s
    r2 = 2.0 * (1.0 - p) * mean_s

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        nxt = rng.expovariate(lam)
        arr = dep = blk = 0
        area = busy_area = wait_area = 0.0
        wait_n = 0
        last = 0.0
        win_area = win_busy = win_wait_area = 0.0
        win_wait_n = 0
        win_arr = win_dep = win_blk = 0
        while True:
            if not busy:
                dt = nxt - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                t += dt
                if t >= H:
                    break
                n += 1
                arr += 1
                if t >= warm:
                    win_arr += 1
                if rng.random() < p:
                    s = rng.expovariate(1.0 / r1)
                else:
                    s = rng.expovariate(1.0 / r2)
                rem = s
                busy = True
                nxt = t + rng.expovariate(lam)
            else:
                dt = min(rem, nxt - t)
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                rem -= dt
                if t >= H:
                    break
                if rem <= 1e-12:
                    n -= 1
                    dep += 1
                    if t >= warm:
                        win_dep += 1
                    busy = False
                    if nxt <= t:
                        nxt = t + rng.expovariate(lam)
                else:
                    n += 1
                    arr += 1
                    if t >= warm:
                        win_arr += 1
                    if rng.random() < p:
                        s = rng.expovariate(1.0 / r1)
                    else:
                        s = rng.expovariate(1.0 / r2)
                    rem = s
                    nxt = t + rng.expovariate(lam)
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = L / (lam * (1.0 - 0.0)) if lam > 0 else 0.0
        if win_arr > 0:
            W = (area / win) / (win_arr / win) if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if win_arr > 0 else 0.0)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += area
        tot_busy += busy_area
        tot_win += win

    nseed = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / nseed
    dep_avg = tot_dep / nseed
    blk_avg = tot_blk / nseed
    dep_rate = dep_avg / (tot_win / nseed) if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    lam_eff = arr_avg / (tot_win / nseed) if tot_win > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = 1.0 - p_loss if arr_avg > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': nseed,
        'time_unit': 'hour',
        'win': tot_win / nseed if nseed > 0 else 0.0,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
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
