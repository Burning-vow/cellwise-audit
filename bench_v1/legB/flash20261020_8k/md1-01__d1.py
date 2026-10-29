import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_dep = None
        queue = []
        area = 0.0
        busy_area = 0.0
        wsum = 0.0
        wn = 0
        arr = dep = blk = 0
        last = 0.0
        while True:
            if next_dep is None:
                dt = rng.expovariate(lam)
                t_next = t + dt
            else:
                dt = rng.expovariate(lam)
                t_next = min(t + dt, next_dep)
            if t_next > H:
                if t < H:
                    area += n * (H - t)
                    busy_area += busy * (H - t)
                break
            area += n * (t_next - t)
            busy_area += busy * (t_next - t)
            t = t_next
            if next_dep is not None and t >= next_dep - 1e-12:
                n -= 1
                busy = 0
                dep += 1
                if queue:
                    cust = queue.pop(0)
                    busy = 1
                    n += 1
                    next_dep = t + cust['svc']
                    if t >= warm:
                        wsum += t - cust['arr']
                        wn += 1
                else:
                    next_dep = None
            else:
                svc = rng.expovariate(mu)
                cust = {'arr': t, 'svc': svc}
                if busy < c:
                    busy += 1
                    n += 1
                    arr += 1
                    if next_dep is None:
                        next_dep = t + svc
                    else:
                        next_dep = min(next_dep, t + svc)
                else:
                    blk += 1
                    arr += 1
        win = H - warm
        L = area / H
        W = wsum / wn if wn > 0 else 0.0
        bf = busy_area / H
        pl = blk / arr if arr > 0 else 0.0
        pw = wn / arr if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_area
        tot_wait += wsum
        tot_wait_n += wn
        tot_win += win

    ns = len(seeds)
    L = tot_area / (H * ns)
    W = tot_wait / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / (H * ns)
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (H / 60.0) if H > 0 else 0.0
    lam_eff = arr_avg / (H / 60.0) if H > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H - warm,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep_avg,
        'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
