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
    tot_waited = 0
    tot_dep_w = 0
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
        busy_t = 0.0
        wait_sum = 0.0
        waited_c = 0
        dep_w = 0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    area += n * (H - t)
                    busy_t += (H - t)
                break
            area += n * dt
            if busy:
                busy_t += dt
            t += dt
            if busy and t >= next_dep - 1e-12:
                n -= 1
                dep_c += 1
                if t >= warm:
                    dep_w += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        waited_c += 1
                        wait_sum += 0.0
                else:
                    n += 1
                    if t >= warm:
                        waited_c += 1
                        wait_sum += svc
        win = H - warm
        Ls = area / H
        Ws = (area / H) / (lam * (1.0 - 0.0)) if lam > 0 else 0.0
        bf = busy_t / H
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = waited_c / dep_w if dep_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_t
        tot_wait += wait_sum
        tot_waited += waited_c
        tot_dep_w += dep_w
    ns = a.seeds
    L = tot_area / (ns * H)
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / (ns * H)
    p_wait = tot_waited / tot_dep_w if tot_dep_w > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / H
    lam_eff = arr / H
    p_loss = blk / arr if arr > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': arr,
        'dep': dep,
        'blk': blk,
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

if __name__ == "__main__":
    main()
