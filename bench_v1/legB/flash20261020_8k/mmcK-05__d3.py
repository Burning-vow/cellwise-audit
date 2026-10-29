import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 5.0
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
    tot_win = 0.0
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait_n = 0.0
    tot_wait_sum = 0.0
    tot_served = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        last = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_n = 0
        wait_sum = 0.0
        served_w = 0
        win_start = warm
        win_len = H - warm
        if win_len <= 0:
            win_len = H
            win_start = 0.0

        def integrate(now):
            nonlocal area_n, area_busy, area_util, last
            dt = now - last
            if dt > 0:
                lo = last
                hi = now
                if hi > win_start:
                    s = max(lo, win_start)
                    area_n += n * (hi - s)
                    area_busy += (1 if busy > 0 else 0) * (hi - s)
                    area_util += min(busy, c) * (hi - s)
            last = now

        while True:
            rate = lam
            u = rng.random()
            dt = -math.log(1.0 - u) / rate
            t_next = t + dt
            if t_next > H:
                integrate(H)
                break
            integrate(t_next)
            t = t_next
            if t >= win_start:
                arr_w += 1
            if n < cap:
                n += 1
                st = rng.expovariate(mu)
                queue.append((t, st))
                if t >= win_start:
                    pass
            else:
                if t >= win_start:
                    blk_w += 1
            while queue and busy < c:
                at, st = queue.pop(0)
                busy += 1
                servers.append((t + st, at, st))
                if t >= win_start:
                    wait_n += 1
                    wait_sum += (t - at)
                    served_w += 1
            while servers and servers[0][0] <= t:
                servers.sort()
                ft, at, st = servers.pop(0)
                busy -= 1
                n -= 1
                if ft >= win_start:
                    dep_w += 1
                while queue and busy < c:
                    at2, st2 = queue.pop(0)
                    busy += 1
                    servers.append((t + st2, at2, st2))
                    if t >= win_start:
                        wait_n += 1
                        wait_sum += (t - at2)
                        served_w += 1

        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_busy / win_len if win_len > 0 else 0.0
        bu = area_util / (c * win_len) if win_len > 0 else 0.0
        W = (wait_sum / wait_n) if wait_n > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_n / arr_w if arr_w > 0 else 0.0

        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_win += win_len
        tot_busy += bf
        tot_util += bu
        tot_wait_n += wait_n
        tot_wait_sum += wait_sum
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
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    busy_util = sum(tot_util) / ns if False else tot_util / ns

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
