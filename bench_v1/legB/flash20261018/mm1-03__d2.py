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
    tot_waited = 0.0
    tot_served = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_sum = 0.0
        waited_c = 0
        served_c = 0
        last = 0.0
        while True:
            tn = min(next_arr, next_dep)
            if tn > H:
                dt = H - last
                if last >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                break
            dt = tn - last
            if last >= warm:
                area += n * dt
                busy_area += (1 if busy else 0) * dt
            elif tn > warm:
                dt2 = tn - warm
                area += n * dt2
                busy_area += (1 if busy else 0) * dt2
            last = tn
            if next_arr <= next_dep:
                t = next_arr
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        served_c += 1
                else:
                    n += 1
                    blk_c += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = next_dep
                dep_c += 1
                n -= 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        Ws = Ls / (dep_c / win) if dep_c > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = 1.0 - (dep_c / arr_c) if arr_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
    ns = a.seeds
    win = H - warm
    L = tot_area / (ns * win) if win > 0 else 0.0
    busy_frac = tot_busy / (ns * win) if win > 0 else 0.0
    dep_rate = tot_dep / (ns * win) if win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    p_loss = blk / arr if arr > 0 else 0.0
    p_wait = 1.0 - dep / arr if arr > 0 else 0.0
    lam_eff = dep_rate
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seed_list,
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
