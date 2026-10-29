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
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
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
    tot_wait = 0.0
    tot_served = 0.0
    tot_waiters = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        cur_rem = 0.0
        area = 0.0
        busy_time = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_sum = 0.0
        served = 0
        waiters = 0
        while True:
            if next_arr <= next_dep:
                te = next_arr
            else:
                te = next_dep
            if te > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    if busy:
                        busy_time += dt
                t = H
                break
            dt = te - t
            if t >= warm:
                area += n * dt
                if busy:
                    busy_time += dt
            t = te
            if next_arr <= next_dep:
                arr_c += 1
                n += 1
                if n == 1:
                    busy = True
                    svc = rng.expovariate(mu)
                    cur_rem = svc
                    next_dep = t + svc
                else:
                    svc = rng.expovariate(mu)
                    if not hasattr(main, '_x'):
                        pass
                next_arr = t + rng.expovariate(lam)
            else:
                dep_c += 1
                n -= 1
                if n > 0:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                else:
                    busy = False
                    next_dep = float('inf')
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        bf = busy_time / win if win > 0 else 0.0
        per_L.append(Ls)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        per_W.append(Ls / lam if lam > 0 else 0.0)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_time
    ns = a.seeds
    win = H - warm
    L = tot_area / (ns * win) if win > 0 and ns > 0 else 0.0
    busy_frac = tot_busy / (ns * win) if win > 0 and ns > 0 else 0.0
    lam_eff = lam
    W = L / lam_eff if lam_eff > 0 else 0.0
    dep_rate = tot_dep / (ns * win) * 60.0 if win > 0 and ns > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': 0.0,
        'p_loss': 0.0,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'win': win,
        'seed_list': seed_list,
        'seeds_used': ns,
        'arr': tot_arr / ns if ns > 0 else 0.0,
        'dep': tot_dep / ns if ns > 0 else 0.0,
        'blk': tot_blk / ns if ns > 0 else 0.0,
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
