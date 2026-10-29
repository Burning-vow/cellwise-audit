import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
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
    per_busy = []
    per_ploss = []
    per_pwait = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy_area = 0.0
    tot_wait_area = 0.0
    tot_waiters_area = 0.0
    tot_dep_time = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        arr_c = 0
        dep_c = 0
        blk_c = 0
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        dep_time_sum = 0.0
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    area += n * (H - t)
                    if busy:
                        busy_area += (H - t)
                    if n > 0:
                        waiters_area += n * (H - t)
                break
            if busy:
                t = next_dep
                n -= 1
                dep_c += 1
                dep_time_sum += t
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                t = t + dt
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    busy = True
                    next_dep = t + svc
                    n = 1
                else:
                    n += 1
        per_L.append(area / H if H > 0 else 0.0)
        per_busy.append(busy_area / H if H > 0 else 0.0)
        per_ploss.append(0.0)
        per_pwait.append(waiters_area / H if H > 0 else 0.0)
        per_W.append(0.0)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy_area += busy_area
        tot_wait_area += wait_area
        tot_waiters_area += waiters_area
        tot_dep_time += dep_time_sum
    seeds_used = a.seeds
    win = H
    L = tot_area / (seeds_used * H) if seeds_used * H > 0 else 0.0
    busy_frac = tot_busy_area / (seeds_used * H) if seeds_used * H > 0 else 0.0
    p_wait = tot_waiters_area / (seeds_used * H) if seeds_used * H > 0 else 0.0
    arr = tot_arr / seeds_used
    dep = tot_dep / seeds_used
    blk = tot_blk / seeds_used
    dep_rate = (tot_dep / (seeds_used * H)) * 60.0 if seeds_used * H > 0 else 0.0
    lam_eff = (tot_arr / (seeds_used * H)) * 60.0 if seeds_used * H > 0 else 0.0
    W = (tot_waiters_area / tot_dep) * 60.0 if tot_dep > 0 else 0.0
    per_W = [ (per_L[i] / (dep / seeds_used) * 60.0) if dep > 0 else 0.0 for i in range(seeds_used) ]
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
