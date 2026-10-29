import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
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
    tot_served = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = 0.0
        areaB = 0.0
        win = 0.0
        arr_w = dep_w = blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        served_cnt = 0
        last_t = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                        win += dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                    win += dt
                t = next_arr
                if t > H:
                    break
                n += 1
                if t >= warm:
                    arr_w += 1
                if n <= cap:
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if busy < c:
                        busy += 1
                        at, sv = queue.pop(0)
                        queue.insert(0, (at, sv))
                        queue = queue[1:]
                        dep_t = t + sv
                        queue.append(('dep', dep_t, t, sv))
                else:
                    n -= 1
                    if t >= warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                item = queue[0]
                if item[0] == 'dep':
                    dep_t = item[1]
                    if dep_t > H:
                        dt = H - t
                        if t >= warm:
                            areaN += n * dt
                            areaB += busy * dt
                            win += dt
                        t = H
                        break
                    dt = dep_t - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                        win += dt
                    t = dep_t
                    queue.pop(0)
                    n -= 1
                    busy -= 1
                    if t >= warm:
                        dep_w += 1
                        served_cnt += 1
                        wait_sum += item[2] - item[3]
                        waited_cnt += 1
                    if queue:
                        nxt = queue[0]
                        if nxt[0] != 'dep':
                            at, sv = nxt
                            queue.pop(0)
                            busy += 1
                            queue.append(('dep', t + sv, at, sv))
                else:
                    if next_arr <= t:
                        next_arr = t + rng.expovariate(lam)
                    if next_arr > H:
                        dt = H - t
                        if t >= warm:
                            areaN += n * dt
                            areaB += busy * dt
                            win += dt
                        t = H
                        break
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                        win += dt
                    t = next_arr
                    n += 1
                    if t >= warm:
                        arr_w += 1
                    if n <= cap:
                        svc = rng.expovariate(mu)
                        queue.append((t, svc))
                        if busy < c:
                            at, sv = queue.pop(0)
                            busy += 1
                            queue.append(('dep', t + sv, at, sv))
                    else:
                        n -= 1
                        if t >= warm:
                            blk_w += 1
                    next_arr = t + rng.expovariate(lam)

        if win <= 0:
            win = 1e-9
        L = areaN / win
        bf = areaB / (c * win)
        W = (wait_sum / served_cnt) if served_cnt > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waited_cnt / arr_w if arr_w > 0 else 0.0
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
        tot_win += win
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_served += served_cnt

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0
    busy_util = L / c if c > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
