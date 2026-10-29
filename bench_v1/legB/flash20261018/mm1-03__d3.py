import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_dep_w = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        dep_w_time = 0.0
        while True:
            dt = min(next_arr, next_dep) - t
            if dt > 0:
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if n >= 1 else 0) * dt
                t += dt
            if t >= H:
                break
            if next_arr <= next_dep:
                if t >= warm:
                    arr_w += 1
                if n >= 1:
                    if t >= warm:
                        blk_w += 1
                else:
                    n = 1
                    busy = 1
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                next_arr = t + rng.expovariate(lam)
            else:
                n = 0
                busy = 0
                next_dep = float('inf')
                if t >= warm:
                    dep_w += 1
                    dep_w_time += 1
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = L / (dep_w / win) if dep_w > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 1.0 - (dep_w / arr_w) if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
    ns = len(seeds)
    win = H - warm
    L = tot_area / (ns * win) if win > 0 else 0.0
    bf = tot_busy / (ns * win) if win > 0 else 0.0
    dep_rate = tot_dep / (ns * win) if win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    p_loss = blk / arr if arr > 0 else 0.0
    p_wait = 1.0 - dep / arr if arr > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
