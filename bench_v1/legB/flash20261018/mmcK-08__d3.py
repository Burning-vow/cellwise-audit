import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaBusy = 0.0
    tot_win = 0.0
    tot_busyutil = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaBusy = areaUtil = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcount = 0
        wsum_win = 0.0
        wcount_win = 0
        last = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                        areaUtil += min(n, c) * dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if busy > 0 else 0) * dt
                    areaUtil += min(n, c) * dt
                t = next_arr
                if t > H:
                    break
                arr += 1
                svc = rng.expovariate(mu)
                if n < cap:
                    n += 1
                    queue.append((t, svc))
                    if busy < c:
                        busy += 1
                        st = t
                        _, sv = queue.pop(0)
                        next_dep = t + sv
                    else:
                        next_dep = float('inf')
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if next_arr < next_dep:
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                        areaUtil += min(n, c) * dt
                    t = next_arr
                    if t > H:
                        break
                    arr += 1
                    svc = rng.expovariate(mu)
                    if n < cap:
                        n += 1
                        queue.append((t, svc))
                        if busy < c:
                            busy += 1
                            st = t
                            _, sv = queue.pop(0)
                            next_dep = t + sv
                    else:
                        blk += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    dt = next_dep - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                        areaUtil += min(n, c) * dt
                    t = next_dep
                    if t > H:
                        break
                    dep += 1
                    n -= 1
                    busy -= 1
                    if queue:
                        busy += 1
                        st, sv = queue.pop(0)
                        next_dep = t + sv
                    else:
                        next_dep = float('inf')
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        bu = areaUtil / (c * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 1.0 - (dep / arr) if arr > 0 else 0.0
        W = L / (dep / win) if dep > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaBusy += areaBusy
        tot_busyutil += areaUtil
        tot_win += win

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    bf = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    bu = tot_busyutil / (c * tot_win) if tot_win > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    pw = 1.0 - (tot_dep / tot_arr) if tot_arr > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    lam_eff = arr_avg / (tot_win / ns) if tot_win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': tot_win / ns,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': bu,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
