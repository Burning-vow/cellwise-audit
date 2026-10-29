import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0
    mean_s = 6.0
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        pass

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    m1 = mean_s * p
    m2 = mean_s * (1.0 - p)
    if m1 <= 0: m1 = 1e-9
    if m2 <= 0: m2 = 1e-9

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_c = dep_c = blk_c = 0
        last = 0.0
        while True:
            if not busy:
                dt = next_arr - t
                if t + dt > H:
                    if t < H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                    break
                area += n * dt
                busy_area += (1 if busy else 0) * dt
                t = next_arr
                n += 1
                if t >= warm:
                    arr_c += 1
                if n == 1:
                    s = m1 if rng.random() < p else m2
                    rem = rng.expovariate(1.0 / s)
                    busy = True
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dt = min(rem, next_arr - t)
                if t + dt > H:
                    if t < H:
                        area += n * (H - t)
                        busy_area += (H - t)
                        if t >= warm:
                            wait_area += (H - t)
                    break
                area += n * dt
                busy_area += dt
                if t >= warm:
                    wait_area += dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep_c += 1
                if abs(t - next_arr) < 1e-12:
                    n += 1
                    if t >= warm:
                        arr_c += 1
                    if not busy:
                        s = m1 if rng.random() < p else m2
                        rem = rng.expovariate(1.0 / s)
                        busy = True
                        if t >= warm:
                            wait_n += 1
                    next_arr = t + rng.expovariate(lam)
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = wait_area / wait_n if wait_n > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / arr_c if arr_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / tot_wait_n if tot_wait_n > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr,
        'dep': dep,
        'blk': blk,
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
