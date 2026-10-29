import json, random, argparse, math

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
            if t + dt > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if n > 0 else 0) * dt
                t = H
                break
            if t >= warm:
                area += n * dt
                busy_area += (1 if n > 0 else 0) * dt
            t += dt
            if next_arr <= next_dep:
                if t >= warm:
                    arr_w += 1
                if n == 0:
                    svc = rng.expovariate(mu)
                    n = 1
                    busy = 1
                    next_dep = t + svc
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                else:
                    n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if t >= warm:
                    dep_w += 1
                    dep_w_time += 1
                n -= 1
                if n == 0:
                    busy = 0
                    next_dep = float('inf')
                else:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (Ls / (lam * (1 - 0))) if lam > 0 else 0.0
        if arr_w > 0:
            Ws = Ls / (arr_w / win) if arr_w > 0 else 0.0
        busyf = busy_area / win if win > 0 else 0.0
        ploss = 0.0
        pwait = 1.0 - (1.0 - busyf) if busyf < 1 else 1.0
        pwait = busyf
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(busyf)
        per_ploss.append(ploss)
        per_pwait.append(pwait)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_dep_w += dep_w_time
    nseeds = len(seeds)
    win = H - warm
    L = sum(per_L) / nseeds
    W = sum(per_W) / nseeds
    busy_frac = sum(per_busy) / nseeds
    p_wait = sum(per_pwait) / nseeds
    p_loss = sum(per_ploss) / nseeds
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = (tot_dep / nseeds) / win * 60.0 if win > 0 else 0.0
    lam_eff = arr / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'win': win,
        'seed_list': seeds,
        'seeds_used': nseeds,
        'arr': arr,
        'dep': dep,
        'blk': blk,
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
