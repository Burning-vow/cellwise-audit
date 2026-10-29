import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
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
        servers = []
        arr = dep = blk = 0
        areaN = areaB = 0.0
        wait_sum = 0.0
        waited = 0
        served = 0
        t_next = rng.expovariate(lam)
        while t < H:
            t_arr = t_next
            t_dep = servers[0] if servers else float('inf')
            t_ev = min(t_arr, t_dep)
            if t_ev >= H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                t = H
                break
            dt = t_ev - t
            if t >= warm:
                areaN += n * dt
                areaB += busy * dt
            t = t_ev
            if t_arr <= t_dep:
                arr += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    cust = [t, svc]
                    if busy < c:
                        busy += 1
                        cust[0] = t
                        servers.append(t + svc)
                        servers.sort()
                    else:
                        queue.append(cust)
                else:
                    blk += 1
                t_next = t + rng.expovariate(lam)
            else:
                servers.pop(0)
                busy -= 1
                dep += 1
                served += 1
                n -= 1
                if queue:
                    cust = queue.pop(0)
                    w = t - cust[0]
                    wait_sum += w
                    waited += 1
                    busy += 1
                    servers.append(t + cust[1])
                    servers.sort()
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaB / (win * c) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / served if served > 0 else 0.0
        W = wait_sum / waited if waited > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaB += areaB
        tot_win += win
        tot_wait += wait_sum
        tot_waited += waited
        tot_served += served

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / (tot_win * c) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H - warm,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': lam,
        'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'busy_occupied': busy_occupied,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
