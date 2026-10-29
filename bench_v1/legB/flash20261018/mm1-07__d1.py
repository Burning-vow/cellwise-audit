import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        pass
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    tot_area = 0.0; tot_busy = 0.0; tot_wait = 0.0; tot_waitn = 0.0
    tot_depw = 0.0; tot_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area = 0.0; busy_area = 0.0
        wsum = 0.0; wn = 0; depw = 0.0
        arr_w = 0; dep_w = 0; blk_w = 0
        last = 0.0
        while True:
            tn = min(next_arr, next_dep)
            if tn > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if n > 0 else 0) * dt
                t = H
                break
            dt = tn - t
            if t >= warm:
                area += n * dt
                busy_area += (1 if n > 0 else 0) * dt
            t = tn
            if next_arr <= next_dep:
                arr_w += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    next_dep = t + svc
                    if t >= warm:
                        wsum += svc; wn += 1
                else:
                    n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep_w += 1
                if t >= warm:
                    depw += 1
                if n > 0:
                    n -= 1
                    if n > 0:
                        svc = rng.expovariate(mu)
                        next_dep = t + svc
                        if t >= warm:
                            wsum += svc; wn += 1
                    else:
                        next_dep = float('inf')
                else:
                    next_dep = float('inf')
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = (wsum / wn) if wn > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 1.0 - (wn / arr_w) if arr_w > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
        tot_area += area; tot_busy += busy_area
        tot_wait += wsum; tot_waitn += wn
        tot_depw += depw; tot_win += win
    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_waitn if tot_waitn > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_depw / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = dep_rate / 60.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 1.0 - (tot_waitn / tot_arr) if tot_arr > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf,
        'busy_util': bf, 'busy_occupied': bf,
        'p_wait': p_wait, 'p_loss': p_loss,
        'runtime_units': H, 'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'seed_list': seeds, 'seeds_used': ns,
        'arr': arr, 'dep': dep, 'blk': blk,
        'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl, 'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
