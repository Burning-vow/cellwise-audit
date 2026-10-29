import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 5.0
    mu = 10.0
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2
    cs2 = cv * cv
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (cs2 - 1.0) / (cs2 + 1.0))))
    r1 = 2.0 * p * mu
    r2 = 2.0 * (1.0 - p) * mu
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seeds = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seeds.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr_c = dep_c = blk_c = 0.0
        while t < H:
            if not busy:
                dt = arr_t - t
                if t + dt > H:
                    if t < warm:
                        pass
                    else:
                        area += n * (H - t)
                        busy_area += 0.0
                    t = H
                    break
                if t < warm:
                    seg_end = min(arr_t, warm)
                    area += n * (seg_end - t)
                    busy_area += 0.0
                else:
                    area += n * (arr_t - t)
                    busy_area += 0.0
                t = arr_t
                n += 1
                if t >= warm:
                    arr_c += 1
                if n == 1:
                    busy = True
                    rem = rng.expovariate(r1 if rng.random() < p else r2)
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                arr_t = t + rng.expovariate(lam)
            else:
                dt = rem
                if t + dt > H:
                    if t < warm:
                        seg_end = min(t + dt, warm)
                        area += n * (seg_end - t)
                        busy_area += (seg_end - t)
                    else:
                        area += n * (H - t)
                        busy_area += (H - t)
                    t = H
                    break
                if t < warm:
                    seg_end = min(t + dt, warm)
                    area += n * (seg_end - t)
                    busy_area += (seg_end - t)
                else:
                    area += n * dt
                    busy_area += dt
                t += dt
                n -= 1
                if t >= warm:
                    dep_c += 1
                if n == 0:
                    busy = False
                else:
                    rem = rng.expovariate(r1 if rng.random() < p else r2)
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (area / max(1e-12, dep_c)) if dep_c > 0 else 0.0
        bfs = busy_area / win if win > 0 else 0.0
        pls = blk_c / arr_c if arr_c > 0 else 0.0
        pws = wait_n / arr_c if arr_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win
    nseed = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_area / tot_dep) if tot_dep > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / nseed
    dep = tot_dep / nseed
    blk = tot_blk / nseed
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': nseed,
        'time_unit': 'minute',
        'win': tot_win / nseed if nseed > 0 else 0.0,
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
