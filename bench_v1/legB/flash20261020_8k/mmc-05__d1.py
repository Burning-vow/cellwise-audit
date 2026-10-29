import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 10.0
    mu = 10.0
    if a.pert == 'lam_up':
        lam = 12.0
    elif a.pert == 'mu_up':
        mu = 12.0
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_win = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wsum = 0.0
        wcnt = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        pw_cnt = 0
        arr_cnt = 0
        last = 0.0
        while True:
            if busy < c:
                dt = rng.expovariate(lam)
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            area_q += len(queue) * (nt - t)
            t = nt
            svc = rng.expovariate(mu)
            n += 1
            if t >= warm:
                arr_w += 1
                arr_cnt += 1
            if busy < c:
                busy += 1
                servers.append((t + svc, svc))
            else:
                if t >= warm:
                    pw_cnt += 1
                queue.append((t, svc))
            while servers and servers[0][0] <= t:
                servers.pop(0)
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, sv = queue.pop(0)
                    wsum += (t - at) + sv
                    wcnt += 1
                    busy += 1
                    servers.append((t + sv, sv))
                    servers.sort()
        area_n += n * (H - t)
        area_busy += busy * (H - t)
        area_q += len(queue) * (H - t)
        win = H - warm
        L = area_n / win
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_busy / (c * win)
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = pw_cnt / arr_cnt if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_win += win
    ns = a.seeds
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': 'minute',
        'seed_list': [a.seed_start + i for i in range(ns)],
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': pl,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
