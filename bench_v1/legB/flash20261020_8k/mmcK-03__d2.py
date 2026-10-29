import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
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
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = 0.0
        areaB = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_waited = 0
        win_dep_w = 0.0
        last_t = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                t = next_arr
                if t > H:
                    break
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if t >= warm:
                        win_arr += 1
                    if busy < c:
                        busy += 1
                        st = t
                        arr_t, sv = queue.pop(0)
                        if t >= warm:
                            win_wait += st - arr_t
                            win_waited += 1
                        queue.insert(0, (arr_t, sv))
                        queue[0] = (arr_t, sv, st)
                else:
                    if t >= warm:
                        win_blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                arr_t, sv, st = queue[0]
                end = st + sv
                if next_arr < end and next_arr <= H:
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                    t = next_arr
                    if n < cap:
                        n += 1
                        svc = rng.expovariate(mu)
                        if t >= warm:
                            win_arr += 1
                        if busy < c:
                            busy += 1
                            if t >= warm:
                                win_wait += t - t
                                win_waited += 1
                            queue.append((t, svc, t))
                        else:
                            queue.append((t, svc, None))
                    else:
                        if t >= warm:
                            win_blk += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    if end > H:
                        dt = H - t
                        if t >= warm:
                            areaN += n * dt
                            areaB += busy * dt
                        t = H
                        break
                    dt = end - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                    t = end
                    queue.pop(0)
                    n -= 1
                    busy -= 1
                    if t >= warm:
                        win_dep += 1
                        win_dep_w += t - arr_t
                    if queue:
                        nxt = queue[0]
                        if nxt[2] is None:
                            busy += 1
                            queue[0] = (nxt[0], nxt[1], t)
                            if t >= warm:
                                win_wait += t - nxt[0]
                                win_waited += 1
        w = H - warm
        tot_win += w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_wait += win_wait
        tot_waited += win_waited
        tot_dep_w += win_dep_w
        L = areaN / w if w > 0 else 0.0
        W = (win_wait / win_waited) if win_waited > 0 else 0.0
        bf = areaB / (c * w) if w > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_waited / win_arr if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)

    w = tot_win / len(seeds) if seeds else 0.0
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / len(seeds) if seeds else 0.0
    dep = tot_dep / len(seeds) if seeds else 0.0
    blk = tot_blk / len(seeds) if seeds else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': w,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'busy_occupied': busy_occupied,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
