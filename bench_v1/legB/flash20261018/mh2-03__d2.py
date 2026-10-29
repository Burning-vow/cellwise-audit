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
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 1e-9), 1.0 - 1e-9)
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
        arr = dep = blk = 0.0
        area = busy_t = wait_area = 0.0
        wait_n = 0.0
        last = 0.0
        while True:
            if not busy:
                tn = nxt
            else:
                tn = min(nxt, t + rem)
            if tn > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_t += (1 if busy else 0) * dt
                t = H
                break
            dt = tn - t
            if t >= warm:
                area += n * dt
                busy_t += (1 if busy else 0) * dt
            t = tn
            if busy and t >= t - rem + rem:
                pass
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep += 1
                    if n > 0:
                        rem = rng.choice([r1, r2]) if False else (r1 if rng.random() < p else r2)
                        busy = True
            if abs(t - nxt) < 1e-12:
                arr += 1
                s = r1 if rng.random() < p else r2
                nxt = t + rng.expovariate(lam)
                if n == 0:
                    n = 1
                    busy = True
                    rem = s
                else:
                    n += 1
                    if t >= warm:
                        wait_area += 0.0
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        W = L / (arr / win) if arr > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    win = tot_win / ns
    lam_eff = arr_avg / win if win > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    W = L / lam_eff if lam_eff > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
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
