import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
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
    tot_waits = 0.0
    tot_served = 0.0
    tot_arr_w = 0.0
    tot_dep_w = 0.0
    tot_blk_w = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waits = 0.0
        served = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        while True:
            if not busy:
                dt = next_arr - t
                if t + dt > H:
                    if t < H:
                        area += n * (H - t)
                        busy_area += 0.0
                    break
                area += n * dt
                t = next_arr
                n += 1
                if t >= warm:
                    arr_w += 1
                svc = rng.expovariate(mu)
                if n == 1:
                    busy = True
                    rem = svc
                    if t >= warm:
                        wait_area += 0.0
                        waits += 0
                    next_arr = t + rng.expovariate(lam)
                else:
                    pass
            else:
                dt = min(rem, next_arr - t)
                if t + dt > H:
                    area += n * (H - t)
                    busy_area += (H - t)
                    break
                area += n * dt
                busy_area += dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    n -= 1
                    served += 1
                    if t >= warm:
                        dep_w += 1
                    if n > 0:
                        svc = rng.expovariate(mu)
                        rem = svc
                        if t >= warm:
                            wait_area += 0.0
                    else:
                        busy = False
                if abs(t - next_arr) < 1e-12:
                    n += 1
                    if t >= warm:
                        arr_w += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        rem = svc
                    next_arr = t + rng.expovariate(lam)
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        Ws = Ls / (lam * (1.0 - 0.0)) if lam > 0 else 0.0
        if dep_w > 0:
            Ws = Ls / (dep_w / win)
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_area += area
        tot_busy += busy_area
        tot_arr_w += arr_w
        tot_dep_w += dep_w
        tot_blk_w += blk_w
        tot_served += served
    ns = len(seeds)
    win = H - warm
    L = tot_area / (ns * win) if win > 0 else 0.0
    busy_frac = tot_busy / (ns * win) if win > 0 else 0.0
    dep_rate = tot_dep_w / (ns * win) if win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    arr = tot_arr_w / ns
    dep = tot_dep_w / ns
    blk = tot_blk_w / ns
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': 0.0,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
