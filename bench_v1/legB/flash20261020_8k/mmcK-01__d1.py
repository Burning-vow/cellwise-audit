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
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
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
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        wsum = 0.0
        wcnt = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        win_start = warm
        win_len = H - warm
        last_t = 0.0
        in_win = False

        def integrate(t0, t1):
            nonlocal area_n, area_busy, area_util
            if t1 <= t0:
                return
            lo = max(t0, win_start)
            hi = min(t1, H)
            if hi <= lo:
                return
            dt = hi - lo
            area_n += n * dt
            area_busy += (1 if busy > 0 else 0) * dt
            area_util += min(busy, c) * dt

        while t < H:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                integrate(t, H)
                t = H
                break
            integrate(t, nt)
            t = nt
            if t >= win_start:
                in_win = True
            if n < cap:
                n += 1
                if t >= win_start:
                    arr_w += 1
                st = rng.expovariate(mu)
                queue.append((t, st))
            else:
                if t >= win_start:
                    blk_w += 1
            while busy < c and queue:
                at, st = queue.pop(0)
                busy += 1
                dep_t = t + st
                wsum += (t - at)
                wcnt += 1
                if t >= win_start:
                    pass
                queue.append(('busy', dep_t))
            newq = []
            for item in queue:
                if isinstance(item, tuple) and len(item) == 2 and item[0] == 'busy':
                    if item[1] <= t:
                        busy -= 1
                        n -= 1
                        if t >= win_start:
                            dep_w += 1
                    else:
                        newq.append(item)
                else:
                    newq.append(item)
            queue = newq
            while busy < c and queue and not (isinstance(queue[0], tuple) and len(queue[0]) == 2 and queue[0][0] == 'busy'):
                at, st = queue.pop(0)
                busy += 1
                dep_t = t + st
                wsum += (t - at)
                wcnt += 1
                queue.append(('busy', dep_t))

        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_busy / win_len if win_len > 0 else 0.0
        bu = area_util / (c * win_len) if win_len > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        pl = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
        pw = wcnt / arr_w if arr_w > 0 else 0.0

        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy += bf
        tot_util += bu
        tot_wait += W
        tot_served += wcnt
        tot_win += win_len

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    bu = tot_util / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
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
        'busy_util': bu,
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
