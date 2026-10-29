import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
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
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
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
        dep_w_sum = 0.0
        dep_w_c = 0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    area += n * (H - t)
                    busy_t += (H - t)
                else:
                    area += n * (H - t)
                break
            area += n * dt
            if busy:
                busy_t += dt
            t += dt
            if busy and t >= next_dep:
                n -= 1
                dep_c += 1
                if t >= warm:
                    dep_w_sum += 1
                    dep_w_c += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                if t >= warm:
                    pass
                if n == 0:
                    n = 1
                    busy = True
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                else:
                    n += 1
                    svc = rng.expovariate(mu)
                    if n > 1:
                        blk_c += 1
                        n -= 1
        win = H - warm
        Ls = area / H
        Ws = Ls / lam if lam > 0 else 0.0
        bf = busy_t / H
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = 0.0
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
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = H - warm
    dep_rate = dep / win * 60.0
    lam_eff = lam * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'p_wait': pw,
        'p_loss': pl,
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
