import json, random, argparse, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    H = float(a.horizon)
    warm = 0.25 * H
    t0 = time.time()
    per_L = []
    per_W = []
    per_busy = []
    per_ploss = []
    per_pwait = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_waiters = 0.0
    tot_dep_wait = 0.0
    win_total = 0.0
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
        arr_c = 0
        dep_c = 0
        blk_c = 0
        dep_wait_sum = 0.0
        dep_wait_c = 0
        while True:
            dt = min(next_arr, next_dep) - t
            if t + dt > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                    wait_area += n * dt
                t = H
                break
            if t >= warm:
                area += n * dt
                busy_area += (1 if busy else 0) * dt
                wait_area += n * dt
            t += dt
            if next_arr <= next_dep:
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = 1
                    next_dep = t + svc
                    dep_wait_sum += 0.0
                    dep_wait_c += 1
                else:
                    n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep_c += 1
                n -= 1
                if n == 0:
                    busy = 0
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
        w = H - warm
        win_total += w
        Ls = area / w
        Ws = wait_area / max(dep_c, 1)
        bs = busy_area / w
        pl = blk_c / max(arr_c, 1)
        pw = 1.0 - (dep_c - 0) / max(arr_c, 1) if arr_c > 0 else 0.0
        pw = max(0.0, min(1.0, pw))
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        per_ploss.append(pl)
        per_pwait.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
    nseeds = len(seeds)
    win = win_total / nseeds if nseeds else 0.0
    L = tot_area / win_total if win_total > 0 else 0.0
    W = tot_wait_area / max(tot_dep, 1)
    busy_frac = tot_busy / win_total if win_total > 0 else 0.0
    p_wait = sum(per_pwait) / nseeds if nseeds else 0.0
    p_loss = tot_blk / max(tot_arr, 1)
    arr_avg = tot_arr / nseeds
    dep_avg = tot_dep / nseeds
    blk_avg = tot_blk / nseeds
    dep_rate = (tot_dep / win_total) * 60.0 if win_total > 0 else 0.0
    lam_eff = (tot_arr / win_total) * 60.0 if win_total > 0 else 0.0
    runtime = time.time() - t0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': runtime,
        'seed_list': seeds,
        'seeds_used': nseeds,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
