import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
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
    nseeds = a.seeds
    seed_list = [a.seed_start + i for i in range(nseeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy_time = 0.0
    tot_util_area = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waiters = 0.0
    win_total = 0.0

    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        served_w = 0
        waiters_w = 0
        last_t = 0.0
        win_start = warm
        win_len = H - warm
        while t < H:
            dt = min(next_arr, next_dep) - t
            if t >= win_start:
                area_n += n * dt
                area_busy += (1 if n > 0 else 0) * dt
                area_util += min(n, c) * dt
            t += dt
            if t >= H:
                break
            if next_arr <= next_dep:
                arr_w += 1 if t >= win_start else 0
                if n < cap:
                    n += 1
                    st = rng.expovariate(mu)
                    queue.append((t, st))
                    if n <= c:
                        next_dep = t + st
                else:
                    blk_w += 1 if t >= win_start else 0
                next_arr = t + rng.expovariate(lam)
            else:
                dep_w += 1 if t >= win_start else 0
                n -= 1
                queue.pop(0)
                if n >= c:
                    next_dep = t + queue[c - 1][1]
                else:
                    next_dep = float('inf')
        L = area_n / win_len if win_len > 0 else 0.0
        bf = area_busy / win_len if win_len > 0 else 0.0
        util = area_util / (c * win_len) if win_len > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waiters_w / served_w if served_w > 0 else 0.0
        W = wait_sum / served_w if served_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy_time += area_busy
        tot_util_area += area_util
        tot_wait += wait_sum
        tot_served += served_w
        tot_waiters += waiters_w
        win_total += win_len

    L = sum(per_L) / nseeds
    W = sum(per_W) / nseeds
    bf = sum(per_bf) / nseeds
    pl = sum(per_pl) / nseeds
    pw = sum(per_pw) / nseeds
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    busy_util = tot_util_area / (c * win_total) if win_total > 0 else 0.0
    dep_rate = dep / (win_total / nseeds) if win_total > 0 else 0.0
    lam_eff = arr / (win_total / nseeds) if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': nseeds,
        'time_unit': 'hour',
        'win': win_total / nseeds,
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
