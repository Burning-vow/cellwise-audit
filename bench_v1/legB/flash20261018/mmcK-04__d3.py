import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 10.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

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
    tot_busy_area = 0.0
    tot_util_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_w = 0
        dep_w = 0
        blk_w = 0
        busy_area = 0.0
        util_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                if t < H:
                    busy_area += busy * (H - t)
                    util_area += min(n, c) * (H - t)
                break
            busy_area += busy * (t_next - t)
            util_area += min(n, c) * (t_next - t)
            t = t_next
            if t >= warm:
                arr_w += 1
            if n < cap:
                n += 1
                svc = rng.expovariate(mu)
                queue.append((t, svc))
            else:
                if t >= warm:
                    blk_w += 1
            while True:
                while len(servers) < c and queue:
                    at, svc = queue.pop(0)
                    servers.append((t + svc, at))
                if not servers:
                    break
                servers.sort()
                if servers[0][0] <= t:
                    ft, at = servers.pop(0)
                    n -= 1
                    if ft >= warm:
                        dep_w += 1
                        wait_area += (ft - at)
                        wait_n += 1
                else:
                    break
        win = H - warm
        L = busy_area / win if win > 0 else 0.0
        W = wait_area / wait_n if wait_n > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_n / dep_w if dep_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy_area += busy_area
        tot_util_area += util_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win

    ns = len(seeds)
    L = tot_busy_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    busy_util = tot_util_area / (tot_win * c) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_dep if tot_dep > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': tot_win / ns,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
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
