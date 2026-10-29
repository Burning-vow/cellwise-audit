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
    tot_waitn = 0.0
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
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_wait = 0.0
        w_waitn = 0
        w_area_n = 0.0
        w_area_busy = 0.0
        w_area_util = 0.0
        w_start = warm
        w_end = H
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                break
            area_n += n * (t_next - t)
            area_busy += (1 if n > 0 else 0) * (t_next - t)
            area_util += min(n, c) * (t_next - t)
            if t_next >= w_start:
                w_area_n += n * (t_next - max(t, w_start))
                w_area_busy += (1 if n > 0 else 0) * (t_next - max(t, w_start))
                w_area_util += min(n, c) * (t_next - max(t, w_start))
            t = t_next
            if n < cap:
                n += 1
                svc = rng.expovariate(mu)
                queue.append((t, svc))
                if t >= w_start:
                    w_arr += 1
            else:
                if t >= w_start:
                    w_blk += 1
            while queue and queue[0][0] + queue[0][1] <= t:
                arr_t, svc = queue.pop(0)
                n -= 1
                if arr_t + svc >= w_start:
                    w_dep += 1
                    w_wait += (arr_t + svc) - arr_t
                    w_waitn += 1
        area_n += n * (H - t)
        area_busy += (1 if n > 0 else 0) * (H - t)
        area_util += min(n, c) * (H - t)
        if H >= w_start:
            w_area_n += n * (H - max(t, w_start))
            w_area_busy += (1 if n > 0 else 0) * (H - max(t, w_start))
            w_area_util += min(n, c) * (H - max(t, w_start))
        win = w_end - w_start
        L = w_area_n / win if win > 0 else 0.0
        bf = w_area_busy / win if win > 0 else 0.0
        util = w_area_util / (c * win) if win > 0 else 0.0
        W = w_wait / w_waitn if w_waitn > 0 else 0.0
        pl = w_blk / (w_arr + w_blk) if (w_arr + w_blk) > 0 else 0.0
        pw = w_waitn / w_arr if w_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += w_arr
        tot_dep += w_dep
        tot_blk += w_blk
        tot_busy += bf
        tot_util += util
        tot_wait += w_wait
        tot_waitn += w_waitn
        tot_win += win
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
