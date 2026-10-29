import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0
    mean_s = 0.1
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 0.01), 0.99)
    m1 = mean_s * p
    m2 = mean_s * (1.0 - p)
    if m1 <= 0: m1 = mean_s * 0.5
    if m2 <= 0: m2 = mean_s * 0.5

    H = float(a.horizon)
    warm = 0.25 * H
    nseeds = a.seeds
    seed_list = [a.seed_start + i for i in range(nseeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = 0.0
    tot_win = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0

    for sd in seed_list:
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
        win_arr = dep_w = blk_w = 0
        win_area = 0.0
        win_busy = 0.0
        win_wait_area = 0.0
        win_wait_n = 0
        last_t = 0.0
        while t < H:
            if not busy:
                dt = next_arr - t
                if t + dt > H:
                    if t >= warm:
                        win_area += n * (H - t)
                        win_busy += (1 if busy else 0) * (H - t)
                    t = H
                    break
                if t >= warm:
                    win_area += n * dt
                    win_busy += (1 if busy else 0) * dt
                t += dt
                n += 1
                arr_c += 1
                if t >= warm:
                    win_arr += 1
                s = m1 if rng.random() < p else m2
                s = rng.expovariate(1.0 / s)
                if not busy:
                    busy = True
                    rem = s
                    if t >= warm:
                        win_wait_n += 1
                        win_wait_area += 0.0
                else:
                    pass
                next_arr = t + rng.expovariate(lam)
            else:
                dt = min(rem, next_arr - t)
                if t + dt > H:
                    if t >= warm:
                        win_area += n * (H - t)
                        win_busy += 1 * (H - t)
                    t = H
                    break
                if t >= warm:
                    win_area += n * dt
                    win_busy += 1 * dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep_c += 1
                    if t >= warm:
                        dep_w += 1
                    if n > 0:
                        s = m1 if rng.random() < p else m2
                        s = rng.expovariate(1.0 / s)
                        busy = True
                        rem = s
                        if t >= warm:
                            win_wait_n += 1
                            win_wait_area += 0.0
                if t >= next_arr - 1e-12 and next_arr <= H:
                    n += 1
                    arr_c += 1
                    if t >= warm:
                        win_arr += 1
                    s = m1 if rng.random() < p else m2
                    s = rng.expovariate(1.0 / s)
                    if not busy:
                        busy = True
                        rem = s
                        if t >= warm:
                            win_wait_n += 1
                            win_wait_area += 0.0
                    next_arr = t + rng.expovariate(lam)
        wl = H - warm
        if wl <= 0: wl = H
        Ls = win_area / wl
        Ws = (Ls / (win_arr / wl)) if win_arr > 0 else 0.0
        bfs = win_busy / wl
        pls = blk_w / win_arr if win_arr > 0 else 0.0
        pws = win_wait_n / win_arr if win_arr > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += win_arr
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += win_area
        tot_win += wl
        tot_busy += win_busy
        tot_wait_area += win_wait_area
        tot_wait_n += win_wait_n

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (L / (tot_arr / tot_win)) if tot_arr > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_rate = tot_arr / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': nseeds,
        'time_unit': 'hour',
        'win': tot_win / nseeds if nseeds > 0 else 0.0,
        'arr': tot_arr / nseeds if nseeds > 0 else 0.0,
        'blk': tot_blk / nseeds if nseeds > 0 else 0.0,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': tot_dep / nseeds if nseeds > 0 else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': arr_rate,
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
