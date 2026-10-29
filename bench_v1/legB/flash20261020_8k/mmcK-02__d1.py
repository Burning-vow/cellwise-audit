import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = c + 1
        cap = cap + 1

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        servers = []
        queue = []
        arr_times = []
        areaN = 0.0
        areaB = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_waited = 0
        win_dep_w = 0.0
        last = 0.0
        while True:
            rate = lam + (mu * busy)
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                areaN += n * (H - t)
                areaB += busy * (H - t)
                t = H
                break
            areaN += n * (nt - t)
            areaB += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    if busy < c:
                        busy += 1
                        servers.append((t + svc, svc))
                    else:
                        queue.append((t, svc))
                    if t >= warm:
                        win_arr += 1
                else:
                    if t >= warm:
                        win_blk += 1
            else:
                servers.sort()
                endt, svc = servers.pop(0)
                busy -= 1
                if t >= warm:
                    win_dep += 1
                    win_dep_w += 1
                if queue:
                    at, qsvc = queue.pop(0)
                    busy += 1
                    servers.append((t + qsvc, qsvc))
                    w = t - at
                    if t >= warm:
                        win_wait += w
                        win_waited += 1
        per_L.append(areaN / H)
        per_bf.append(areaB / (c * H))
        per_pl.append(win_blk / win_arr if win_arr > 0 else 0.0)
        per_pw.append(win_waited / win_arr if win_arr > 0 else 0.0)
        per_W.append(win_wait / win_waited if win_waited > 0 else 0.0)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_areaN += areaN
        tot_areaB += areaB
        tot_win += H
        tot_wait += win_wait
        tot_waited += win_waited
        tot_dep_w += win_dep_w

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / 60.0) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
