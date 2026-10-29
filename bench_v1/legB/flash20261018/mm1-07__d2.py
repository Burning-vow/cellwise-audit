import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
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
    arr_tot = 0.0
    dep_tot = 0.0
    blk_tot = 0.0
    win_tot = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = 0
        area_n = 0.0
        area_b = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0
        last = 0.0
        queue = []
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        while t < H:
            if next_arr <= next_dep:
                nt = next_arr
                if nt > H:
                    nt = H
                if nt > warm:
                    area_n += n * (nt - last)
                    area_b += busy * (nt - last)
                last = nt
                t = nt
                if t >= H:
                    break
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = 1
                    next_dep = t + svc
                    if t >= warm:
                        arr_w += 1
                else:
                    n += 1
                    queue.append(svc)
                    if t >= warm:
                        arr_w += 1
                        wait_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                nt = next_dep
                if nt > H:
                    nt = H
                if nt > warm:
                    area_n += n * (nt - last)
                    area_b += busy * (nt - last)
                last = nt
                t = nt
                if t >= H:
                    break
                if t >= warm:
                    dep_w += 1
                if queue:
                    svc = queue.pop(0)
                    next_dep = t + svc
                else:
                    n = 0
                    busy = 0
                    next_dep = float('inf')
        if H > warm:
            area_n += n * (H - last)
            area_b += busy * (H - last)
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_b / win if win > 0 else 0.0
        W = L / (dep_w / win) if dep_w > 0 else 0.0
        pw = wait_w / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        arr_tot += arr_w
        dep_tot += dep_w
        blk_tot += blk_w
        win_tot += win
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    arr = arr_tot / ns
    dep = dep_tot / ns
    blk = blk_tot / ns
    win = win_tot / ns
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = arr / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': pw,
        'p_loss': 0.0,
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
