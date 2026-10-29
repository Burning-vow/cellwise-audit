import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
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
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_area = 0.0
    tot_time = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        w_area = 0.0
        w_cnt = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        busy_t = 0.0
        win_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    area += n * (H - t)
                    busy_t += (H - t)
                    win_t += (H - t)
                else:
                    win_t += (H - t)
                break
            if busy:
                area += n * dt
                busy_t += dt
                win_t += dt
                t = next_dep
                n -= 1
                dep_c += 1
                if t >= warm:
                    pass
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                area += n * dt
                win_t += dt
                t = t + dt
                arr_c += 1
                svc = rng.expovariate(mu)
                n += 1
                busy = True
                next_dep = t + svc
                if t >= warm:
                    w_area += svc
                    w_cnt += 1
        per_L.append(area / H if H > 0 else 0.0)
        per_W.append(w_area / w_cnt if w_cnt > 0 else 0.0)
        per_bf.append(busy_t / H if H > 0 else 0.0)
        per_pl.append(0.0)
        per_pw.append(1.0 if arr_c > 0 else 0.0)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy += busy_t
        tot_area += area
        tot_time += H
        tot_wait += w_area
        tot_served += w_cnt
    L = tot_area / tot_time if tot_time > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_busy / tot_time if tot_time > 0 else 0.0
    p_wait = 1.0 if tot_arr > 0 else 0.0
    dep_rate = (tot_dep / tot_time) * 60.0 if tot_time > 0 else 0.0
    lam_eff = (tot_arr / tot_time) * 60.0 if tot_time > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': a.seeds,
        'time_unit': 'minute',
        'win': H,
        'arr': tot_arr / a.seeds,
        'blk': tot_blk / a.seeds,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': tot_dep / a.seeds,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
