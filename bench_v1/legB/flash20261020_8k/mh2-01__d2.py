import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 3.0
    mean_s = 0.1
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2
    var_s = (cv * mean_s) ** 2
    p2 = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p2 = min(max(p2, 0.0), 1.0)
    m1 = mean_s * (1.0 - math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2)))) if var_s > mean_s**2 else mean_s
    m1 = max(m1, 1e-9)
    m2 = (mean_s - p2 * m1) / (1.0 - p2) if p2 < 1.0 else m1
    m2 = max(m2, 1e-9)
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
        arr_t = t + rng.expovariate(lam)
        dep_t = float('inf')
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr_c = dep_c = blk_c = 0.0
        while True:
            nxt = min(arr_t, dep_t)
            if nxt > H:
                dt = H - t
                if dt > 0:
                    if t >= warm:
                        area += n * dt
                        busy_area += (1 if busy else 0) * dt
                    t = H
                break
            dt = nxt - t
            if dt > 0 and t >= warm:
                area += n * dt
                busy_area += (1 if busy else 0) * dt
            t = nxt
            if arr_t <= dep_t:
                arr_t = t + rng.expovariate(lam)
                s = m1 if rng.random() < p2 else m2
                if t >= warm:
                    arr_c += 1
                if not busy:
                    busy = True
                    rem = s
                    dep_t = t + rem
                    if t >= warm:
                        wait_n += 1
                else:
                    n += 1
                    if t >= warm:
                        blk_c += 1
            else:
                if t >= warm:
                    dep_c += 1
                if n > 0:
                    n -= 1
                    s = m1 if rng.random() < p2 else m2
                    rem = s
                    dep_t = t + rem
                else:
                    busy = False
                    dep_t = float('inf')
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = (area / (dep_c if dep_c > 0 else 1.0)) * 60.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = blk_c / (blk_c + wait_n) if (blk_c + wait_n) > 0 else 0.0
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
    W = (tot_area / tot_dep) * 60.0 if tot_dep > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_blk / (tot_blk + tot_wait_n) if (tot_blk + tot_wait_n) > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
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
