import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2
    svc = 60.0 / mu

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_served = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        server_free = 0.0
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        waited = 0
        served = 0
        last = 0.0
        while True:
            rate = lam / 60.0
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                break
            area += n * (t_next - t)
            busy_area += busy * (t_next - t)
            t = t_next
            if t >= warm:
                arr += 1
            if n < c:
                n += 1
                busy = 1
                st = t + svc
                queue.append((st, t))
            else:
                if t >= warm:
                    blk += 1
            while queue and queue[0][0] <= t:
                st, at = queue.pop(0)
                n -= 1
                busy = 1 if n >= c else 0
                if st >= warm:
                    dep += 1
                    served += 1
                    wait_sum += st - svc - at
                    if st - svc - at > 0:
                        waited += 1
        area += n * (H - t)
        busy_area += busy * (H - t)
        win = H - warm
        L = area / H
        W = L / (lam / 60.0) if lam > 0 else 0.0
        bf = busy_area / H
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / served if served > 0 else 0.0
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
        tot_win += win
        tot_wait += wait_sum
        tot_waited += waited
        tot_served += served

    ns = len(seeds)
    L = tot_area / (H * ns)
    W = L / (lam / 60.0) if lam > 0 else 0.0
    busy_frac = tot_busy / (H * ns)
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) * 60.0 if tot_win > 0 else 0.0
    lam_eff = lam * (1 - (tot_blk / tot_arr if tot_arr > 0 else 0.0))
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac / c,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
