import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

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
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        servers = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        last = 0.0
        while t < H:
            cand = next_arr
            if servers:
                cand = min(cand, servers[0][0])
            if cand >= H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += min(n, c) * dt
                t = H
                break
            dt = cand - t
            if t >= warm:
                area += n * dt
                busy_area += min(n, c) * dt
            t = cand
            if servers and servers[0][0] <= t:
                servers.pop(0)
                n -= 1
                if t >= warm:
                    dep_w += 1
            if abs(t - next_arr) < 1e-12:
                if t >= warm:
                    arr_w += 1
                if n < c:
                    svc = rng.expovariate(mu)
                    n += 1
                    servers.append((t + svc, svc))
                    servers.sort()
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                else:
                    if t >= warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (area / (dep_w if dep_w > 0 else 1)) if dep_w > 0 else 0.0
        bfs = busy_area / win if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = (arr_w - blk_w) / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_area / tot_dep) if tot_dep > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = (tot_arr - tot_blk) / tot_arr if tot_arr > 0 else 0.0
    busy_util = busy_frac / c
    busy_occupied = busy_frac

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
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
