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
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 4
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
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_win = 0.0

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
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_w = 0.0
        served_w = 0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            t_next = t + dt
            if t_next > H:
                break
            area_n += n * (t_next - t)
            area_busy += (1 if busy > 0 else 0) * (t_next - t)
            area_util += min(busy, c) * (t_next - t)
            t = t_next
            if t >= warm:
                arr_w += 1
            if n < cap:
                st = rng.expovariate(mu)
                queue.append((t, st))
                n += 1
                if busy < c:
                    busy += 1
                    arr_t, sv = queue.pop(0)
                    servers.append((arr_t, t + sv))
            else:
                if t >= warm:
                    blk_w += 1
            while servers and servers[0][1] <= t:
                at, ft = servers.pop(0)
                busy -= 1
                if ft >= warm:
                    dep_w += 1
                    wait_w += (ft - at) - (ft - at)
                if queue:
                    busy += 1
                    at2, sv2 = queue.pop(0)
                    servers.append((at2, t + sv2))
        while servers:
            at, ft = servers.pop(0)
            if ft > H:
                ft = H
            if ft >= warm:
                dep_w += 1
            busy -= 1
            if queue:
                busy += 1
                at2, sv2 = queue.pop(0)
                servers.append((at2, ft + sv2))
        win = H - warm
        L = area_n / H
        bf = area_busy / H
        util = area_util / (c * H)
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(0.0)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy += bf
        tot_util += util
        tot_win += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = 0.0
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    busy_util = tot_util / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
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
