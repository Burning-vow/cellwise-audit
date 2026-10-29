import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 12.0
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
    tot_areaN = tot_areaBusy = tot_areaOcc = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        next_dep = [math.inf] * c
        areaN = areaBusy = areaOcc = 0.0
        win = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        served = 0
        waited = 0
        last = 0.0
        while True:
            tnext = min(next_arr, min(next_dep))
            if tnext > H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if busy > 0 else 0) * dt
                    areaOcc += min(n, c) * dt
                    win += dt
                t = H
                break
            dt = tnext - t
            if t >= warm:
                areaN += n * dt
                areaBusy += (1 if busy > 0 else 0) * dt
                areaOcc += min(n, c) * dt
                win += dt
            t = tnext
            if tnext == next_arr:
                if n < cap:
                    n += 1
                    arr += 1
                    st = rng.expovariate(mu)
                    queue.append((t, st))
                    if busy < c:
                        busy += 1
                        at, stt = queue.pop(0)
                        next_dep[busy - 1] = t + stt
                        wait_sum += t - at
                        served += 1
                        waited += 1
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                idx = next_dep.index(tnext)
                next_dep[idx] = math.inf
                busy -= 1
                n -= 1
                dep += 1
                if queue:
                    busy += 1
                    at, stt = queue.pop(0)
                    next_dep[busy - 1] = t + stt
                    wait_sum += t - at
                    served += 1
                    waited += 1
        L = areaN / win if win > 0 else 0.0
        W = wait_sum / served if served > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        pl = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        pw = waited / served if served > 0 else 0.0
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
        tot_areaOcc += areaOcc
        tot_win += win
        tot_wait += wait_sum
        tot_served += served
        tot_waited += waited

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    busy_util = (tot_areaOcc / tot_win) / c if tot_win > 0 else 0.0
    p_loss = tot_blk / (tot_arr + tot_blk) if (tot_arr + tot_blk) > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    lam_eff = (tot_arr + tot_blk) / tot_win if tot_win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': tot_win / ns,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'busy_occupied': busy_frac, 'dep': dep_avg, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
