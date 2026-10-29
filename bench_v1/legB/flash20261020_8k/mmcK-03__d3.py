import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr = dep = blk = 0
        areaN = areaB = 0.0
        wait_sum = 0.0
        waited = 0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            tnext = t + dt
            if servers:
                tdep = min(servers)
            else:
                tdep = float('inf')
            if tnext <= tdep and tnext <= H:
                areaN += n * (tnext - t)
                areaB += busy * (tnext - t)
                t = tnext
                arr += 1
                svc = rng.expovariate(mu)
                if n < cap:
                    n += 1
                    if busy < c:
                        busy += 1
                        servers.append(t + svc)
                    else:
                        queue.append((t, svc))
                else:
                    blk += 1
            elif tdep <= H:
                areaN += n * (t - last) if False else 0
                areaN += n * (tdep - t)
                areaB += busy * (tdep - t)
                t = tdep
                servers.remove(tdep)
                busy -= 1
                dep += 1
                if queue:
                    at, svc = queue.pop(0)
                    wait_sum += t - at
                    waited += 1
                    busy += 1
                    servers.append(t + svc)
                n -= 1
            else:
                areaN += n * (H - t)
                areaB += busy * (H - t)
                t = H
                break
        win = H - warm
        if win <= 0:
            win = H
        L = areaN / H if H > 0 else 0.0
        W = (wait_sum / waited) if waited > 0 else 0.0
        bf = areaB / H if H > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / arr if arr > 0 else 0.0
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
        tot_win += H
        tot_wait += wait_sum
        tot_waited += waited
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    busy_util = (tot_areaB / tot_win) / c if tot_win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'busy_occupied': bf,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
