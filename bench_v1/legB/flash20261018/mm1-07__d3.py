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
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_waits = 0.0
    tot_served = 0.0
    tot_arrivals_win = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waits = 0.0
        served = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        while True:
            if busy:
                dt = next_dep - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                if t >= H:
                    break
                n -= 1
                dep_win += 1
                served += 1
                if n > 0:
                    next_dep = t + rng.expovariate(mu)
                    busy = True
                else:
                    busy = False
                    next_dep = float('inf')
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    if t >= warm:
                        area += n * (H - t)
                    t = H
                    break
                t += dt
                if t >= warm:
                    arr_win += 1
                n += 1
                svc = rng.expovariate(mu)
                if n == 1:
                    next_dep = t + svc
                    busy = True
                if t >= warm:
                    wait_area += n * 0.0
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        per_L.append(L)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if arr_win > 0 else 0.0)
        per_W.append(L / (arr_win / win) if arr_win > 0 else 0.0)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += blk_win
        tot_area += area
        tot_busy += busy_area
        tot_arrivals_win += arr_win
    nseeds = a.seeds
    win = H - warm
    L = tot_area / (win * nseeds) if win > 0 and nseeds > 0 else 0.0
    busy_frac = tot_busy / (win * nseeds) if win > 0 and nseeds > 0 else 0.0
    arr_rate = tot_arr / (win * nseeds) if win > 0 and nseeds > 0 else 0.0
    dep_rate = tot_dep / (win * nseeds) if win > 0 and nseeds > 0 else 0.0
    W = L / arr_rate if arr_rate > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': 1.0 if arr_rate > 0 else 0.0,
        'p_loss': 0.0,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / nseeds if nseeds > 0 else 0.0,
        'dep': tot_dep / nseeds if nseeds > 0 else 0.0,
        'blk': tot_blk / nseeds if nseeds > 0 else 0.0,
        'dep_rate': dep_rate * 60.0,
        'lam_eff': arr_rate * 60.0,
        'seed_list': seed_list,
        'seeds_used': nseeds,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
