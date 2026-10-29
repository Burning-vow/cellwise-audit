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
        lam *= 1.5
    elif a.pert == 'mu_up':
        mu *= 1.5
    elif a.pert == 'c_up':
        c = 4
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_busy_time = 0.0
    tot_util_area = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        busy_time = 0.0
        util_area = 0.0
        arr_w = dep_w = blk_w = 0.0
        wsum = 0.0
        wcount = 0
        waiters = 0
        last = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                        busy_time += dt if n > 0 else 0.0
                        util_area += min(n, c) * dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                    busy_time += dt if n > 0 else 0.0
                    util_area += min(n, c) * dt
                t = next_arr
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t, svc))
                    if t >= warm:
                        arr_w += 1
                    if busy < c:
                        busy += 1
                        st = t
                        at, sv = queue.pop(0)
                        dep_t = st + sv
                        if t >= warm:
                            wsum += st - at
                            wcount += 1
                        next_arr = t + rng.expovariate(lam)
                        while True:
                            if dep_t <= next_arr and dep_t <= H:
                                if dep_t >= warm:
                                    areaN += n * (dep_t - t)
                                    areaB += busy * (dep_t - t)
                                    busy_time += (dep_t - t) if n > 0 else 0.0
                                    util_area += min(n, c) * (dep_t - t)
                                t = dep_t
                                n -= 1
                                busy -= 1
                                if t >= warm:
                                    dep_w += 1
                                if queue and busy < c:
                                    busy += 1
                                    at2, sv2 = queue.pop(0)
                                    dep_t = t + sv2
                                    if t >= warm:
                                        wsum += t - at2
                                        wcount += 1
                                else:
                                    break
                            else:
                                break
                        if dep_t > H:
                            if H >= warm:
                                areaN += n * (H - t)
                                areaB += busy * (H - t)
                                busy_time += (H - t) if n > 0 else 0.0
                                util_area += min(n, c) * (H - t)
                            t = H
                            break
                    else:
                        next_arr = t + rng.expovariate(lam)
                else:
                    if t >= warm:
                        blk_w += 1
                    next_arr = t + rng.expovariate(lam)
            else:
                if busy < c:
                    busy += 1
                    at, sv = queue.pop(0)
                    dep_t = t + sv
                    if t >= warm:
                        wsum += t - at
                        wcount += 1
                    while True:
                        if dep_t <= next_arr and dep_t <= H:
                            if dep_t >= warm:
                                areaN += n * (dep_t - t)
                                areaB += busy * (dep_t - t)
                                busy_time += (dep_t - t) if n > 0 else 0.0
                                util_area += min(n, c) * (dep_t - t)
                            t = dep_t
                            n -= 1
                            busy -= 1
                            if t >= warm:
                                dep_w += 1
                            if queue and busy < c:
                                busy += 1
                                at2, sv2 = queue.pop(0)
                                dep_t = t + sv2
                                if t >= warm:
                                    wsum += t - at2
                                    wcount += 1
                            else:
                                break
                        else:
                            break
                    if dep_t > H:
                        if H >= warm:
                            areaN += n * (H - t)
                            areaB += busy * (H - t)
                            busy_time += (H - t) if n > 0 else 0.0
                            util_area += min(n, c) * (H - t)
                        t = H
                        break
                else:
                    if next_arr > H:
                        dt = H - t
                        if t >= warm:
                            areaN += n * dt
                            areaB += busy * dt
                            busy_time += dt if n > 0 else 0.0
                            util_area += min(n, c) * dt
                        t = H
                        break
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaB += busy * dt
                        busy_time += dt if n > 0 else 0.0
                        util_area += min(n, c) * dt
                    t = next_arr
                    if n < cap:
                        n += 1
                        svc = rng.expovariate(mu)
                        queue.append((t, svc))
                        if t >= warm:
                            arr_w += 1
                    else:
                        if t >= warm:
                            blk_w += 1
                    next_arr = t + rng.expovariate(lam)

        win = H - warm
        Ls = areaN / win if win > 0 else 0.0
        Ws = wsum / wcount if wcount > 0 else 0.0
        bfs = busy_time / win if win > 0 else 0.0
        pls = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
        pws = wcount / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_win += win
        tot_busy_time += busy_time
        tot_util_area += util_area

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = sum(per_W) / ns if ns > 0 else 0.0
    busy_frac = tot_busy_time / tot_win if tot_win > 0 else 0.0
    p_loss = tot_blk / (tot_arr + tot_blk) if (tot_arr + tot_blk) > 0 else 0.0
    busy_util = tot_util_area / (tot_win * c) if tot_win > 0 else 0.0
    arr = tot_arr / ns if ns > 0 else 0.0
    dep = tot_dep / ns if ns > 0 else 0.0
    blk = tot_blk / ns if ns > 0 else 0.0
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = (tot_arr + tot_blk) / (tot_win / ns) if tot_win > 0 else 0.0
    p_wait = sum(per_pw) / ns if ns > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
