import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=str, default='2000')
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    H = float(a.horizon)
    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    seeds = [a.seed_start + i for i in range(a.seeds)]
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
    tot_wait_cnt = 0.0
    tot_dep_wait = 0.0
    win_total = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        warm = 0.25 * H
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_cnt = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        dep_wait = 0.0
        last = 0.0
        while True:
            tn = min(next_arr, next_dep)
            if tn > H:
                if t < H:
                    dt = H - t
                    if t >= warm:
                        area += n * dt
                        busy_area += (1 if n >= 1 else 0) * dt
                    t = H
                break
            dt = tn - t
            if t >= warm:
                area += n * dt
                busy_area += (1 if n >= 1 else 0) * dt
            t = tn
            if next_arr <= next_dep:
                arr_c += 1
                if n >= 1:
                    blk_c += 1
                else:
                    n = 1
                    busy = 1
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                next_arr = t + rng.expovariate(lam)
            else:
                dep_c += 1
                n = 0
                busy = 0
                next_dep = float('inf')
        wlen = H - warm
        win_total += wlen
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        Ls = area / wlen if wlen > 0 else 0.0
        bfs = busy_area / wlen if wlen > 0 else 0.0
        Ws = Ls / (lam * (1 - 0)) if lam > 0 else 0.0
        pls = blk_c / arr_c if arr_c > 0 else 0.0
        pws = 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
    L = tot_area / win_total if win_total > 0 else 0.0
    busy_frac = tot_busy / win_total if win_total > 0 else 0.0
    lam_eff = lam * (1 - (tot_blk / tot_arr if tot_arr > 0 else 0.0))
    W = L / lam_eff if lam_eff > 0 else 0.0
    dep_rate = tot_dep / win_total if win_total > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': win_total / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
