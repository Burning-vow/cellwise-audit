import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0
    mu = 5.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
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
    tot_win = 0.0
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        area_wait = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0.0
        served_w = 0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                break
            area_n += n * (nt - t)
            area_busy += (1 if n > 0 else 0) * (nt - t)
            area_util += min(n, c) * (nt - t)
            t = nt
            if n < cap:
                n += 1
                svc = rng.expovariate(mu)
                queue.append((t, svc))
                if t >= warm:
                    arr_w += 1
            else:
                if t >= warm:
                    arr_w += 1
                    blk_w += 1
            while queue and queue[0][0] + queue[0][1] <= t:
                st, sv = queue.pop(0)
                n -= 1
                if st + sv >= warm:
                    dep_w += 1
                    if st >= warm:
                        wait_w += 0.0
                    else:
                        wait_w += 0.0
                    served_w += 1
        while queue:
            st, sv = queue.pop(0)
            ft = st + sv
            if ft > H:
                area_n += n * (H - t)
                area_busy += (1 if n > 0 else 0) * (H - t)
                area_util += min(n, c) * (H - t)
                t = H
                break
            area_n += n * (ft - t)
            area_busy += (1 if n > 0 else 0) * (ft - t)
            area_util += min(n, c) * (ft - t)
            t = ft
            n -= 1
            if ft >= warm:
                dep_w += 1
                served_w += 1
        win = H - warm
        L = area_n / H
        bf = area_busy / H
        util = area_util / (c * H)
        W = (area_n / max(dep_w, 1)) * 60.0 if dep_w > 0 else 0.0
        pl = blk_w / max(arr_w, 1)
        pw = 1.0 if blk_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_win += win
        tot_busy += area_busy
        tot_util += area_util
        tot_served += served_w
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    busy_util = tot_util / (c * tot_win) if tot_win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
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
