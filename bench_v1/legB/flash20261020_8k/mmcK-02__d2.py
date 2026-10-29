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

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        win_start = warm
        arr_w = dep_w = blk_w = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_cnt_w = 0
        last_t = 0.0
        while True:
            if not queue:
                t_next = next_arr
            else:
                t_next = min(next_arr, queue[0][0])
            if t_next > H:
                dt = H - t
                if t >= win_start:
                    areaN += n * dt
                    areaB += busy * dt
                elif t + dt > win_start:
                    d1 = win_start - t
                    d2 = t + dt - win_start
                    areaN += n * d2
                    areaB += busy * d2
                t = H
                break
            dt = t_next - t
            if t >= win_start:
                areaN += n * dt
                areaB += busy * dt
            elif t + dt > win_start:
                d2 = t + dt - win_start
                areaN += n * d2
                areaB += busy * d2
            t = t_next
            if t == next_arr:
                if t >= win_start:
                    arr_w += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t + svc, t))
                    if busy < c:
                        busy += 1
                else:
                    if t >= win_start:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep_t, arr_t = queue.pop(0)
                busy -= 1
                n -= 1
                if t >= win_start:
                    dep_w += 1
                    dep_cnt_w += 1
                    wait_sum += t - arr_t
                    waited_cnt += 1
                if queue and busy < c:
                    busy += 1
        win_len = H - win_start
        L = areaN / win_len if win_len > 0 else 0.0
        bf = areaB / (c * win_len) if win_len > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        W = wait_sum / dep_cnt_w if dep_cnt_w > 0 else 0.0
        pw = waited_cnt / dep_cnt_w if dep_cnt_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_win += win_len
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_dep_win += dep_cnt_w

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    W = tot_wait / tot_dep_win if tot_dep_win > 0 else 0.0
    p_wait = tot_waited / tot_dep_win if tot_dep_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'busy_occupied': busy_occupied,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
