import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 10.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1
        cap = cap + 1

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    tot_depw = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_wait = 0.0
        w_waitn = 0
        w_depw = 0.0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                t_next = H
            dtw = t_next - last
            if t >= warm:
                area_n += n * dtw
                area_busy += (1 if n > 0 else 0) * dtw
                area_util += min(n, c) * dtw
            last = t_next
            t = t_next
            if t >= H:
                break
            if n < cap:
                svc = rng.expovariate(mu)
                n += 1
                w_arr += 1
                if t >= warm:
                    pass
                queue.append((t, svc))
            else:
                w_blk += 1
            while queue and len(servers) < c:
                at, svc = queue.pop(0)
                servers.append((at, svc, t))
            newservers = []
            for at, svc, st in servers:
                if st + svc <= t:
                    n -= 1
                    w_dep += 1
                    if t >= warm:
                        w_wait += (st - at)
                        w_waitn += 1
                        w_depw += 1
                else:
                    newservers.append((at, svc, st))
            servers = newservers
            while queue and len(servers) < c:
                at, svc = queue.pop(0)
                servers.append((at, svc, t))
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_util / win if win > 0 else 0.0
        pl = w_blk / (w_arr + w_blk) if (w_arr + w_blk) > 0 else 0.0
        pw = w_waitn / w_arr if w_arr > 0 else 0.0
        W = w_wait / w_waitn if w_waitn > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += w_arr
        tot_dep += w_dep
        tot_blk += w_blk
        tot_busy += bf
        tot_util += bu
        tot_wait += w_wait
        tot_waitn += w_waitn
        tot_depw += w_depw

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = H - warm
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = tot_util / ns

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
