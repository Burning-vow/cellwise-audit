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
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waiters = 0.0

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
        waiters = 0
        served = 0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
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
                st = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + st)
                    if t >= warm:
                        served += 1
                else:
                    queue.append((t, st))
                    if t >= warm:
                        waiters += 1
            else:
                if t >= warm:
                    blk_w += 1
            while servers and servers[0] <= t:
                servers.pop(0)
                busy -= 1
                if queue:
                    at, st = queue.pop(0)
                    servers.append(t + st)
                    busy += 1
                    if t >= warm:
                        served += 1
                        wait_area += (t - at)
                else:
                    n -= 1
            servers.sort()
        win = H - warm
        L = busy_area / H if H > 0 else 0.0
        Lw = busy_area / win if win > 0 else 0.0
        bf = busy_area / H if H > 0 else 0.0
        util = util_area / (H * c) if H > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waiters / arr_w if arr_w > 0 else 0.0
        W = wait_area / served if served > 0 else 0.0
        per_L.append(Lw)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += served
        tot_blk += blk_w
        tot_busy_area += busy_area
        tot_util_area += util_area
        tot_win += win
        tot_wait += wait_area
        tot_served += served
        tot_waiters += waiters

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
    busy_util = tot_util_area / (tot_win * c) if tot_win > 0 else 0.0
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
