import json, math, random, argparse

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
    r1 = 2.0 * p * mean_s
    r2 = 2.0 * (1.0 - p) * mean_s

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = tot_waitn = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        nxt = rng.expovariate(lam)
        area = 0.0
        busy_t = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wn = 0
        last = 0.0
        while True:
            if not busy:
                tn = nxt
                if tn > H:
                    dt = H - t
                    if t >= warm:
                        area += n * dt
                        busy_t += 0.0
                    t = H
                    break
                dt = tn - t
                if t >= warm:
                    area += n * dt
                t = tn
                if t >= warm:
                    arr += 1
                n += 1
                if n == 1:
                    busy = True
                    rem = r1 if rng.random() < p else r2
                nxt = t + rng.expovariate(lam)
            else:
                td = t + rem
                tn = nxt
                if td <= tn:
                    if td > H:
                        dt = H - t
                        if t >= warm:
                            area += n * dt
                            busy_t += dt
                        t = H
                        break
                    dt = td - t
                    if t >= warm:
                        area += n * dt
                        busy_t += dt
                    t = td
                    if t >= warm:
                        dep += 1
                    n -= 1
                    if n > 0:
                        rem = r1 if rng.random() < p else r2
                    else:
                        busy = False
                        rem = 0.0
                else:
                    if tn > H:
                        dt = H - t
                        if t >= warm:
                            area += n * dt
                            busy_t += dt
                        t = H
                        break
                    dt = tn - t
                    if t >= warm:
                        area += n * dt
                        busy_t += dt
                    t = tn
                    if t >= warm:
                        arr += 1
                    n += 1
                    nxt = t + rng.expovariate(lam)
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (busy_t / dep) if dep > 0 else 0.0
        bfs = busy_t / win if win > 0 else 0.0
        pls = blk / arr if arr > 0 else 0.0
        pws = 1.0 if arr > 0 and dep < arr else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_busy / tot_dep) if tot_dep > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_m = tot_arr / ns
    dep_m = tot_dep / ns
    blk_m = tot_blk / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 1.0 if tot_arr > 0 and tot_dep < tot_arr else 0.0
    lam_eff = dep_rate

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr_m, 'blk': blk_m, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep_m, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
