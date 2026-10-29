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
    tot_areaN = tot_areaBusy = tot_areaOcc = 0.0
    tot_wait = tot_waited = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaBusy = areaOcc = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        waited = 0
        last = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if n > 0 else 0) * dt
                        areaOcc += min(n, c) * dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if n > 0 else 0) * dt
                    areaOcc += min(n, c) * dt
                t = next_arr
                if t > H:
                    break
                arr += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append([t, svc])
                    if busy < c:
                        busy += 1
                        st = t
                        sv = queue.pop(0)[1]
                        next_dep = t + sv
                        dep_t = next_dep
                        dep_sv = sv
                        dep_st = st
                    else:
                        next_dep = float('inf')
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if next_dep <= next_arr or next_arr > H:
                    dt = next_dep - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if n > 0 else 0) * dt
                        areaOcc += min(n, c) * dt
                    t = next_dep
                    if t > H:
                        break
                    n -= 1
                    dep += 1
                    w = dep_t - dep_st
                    wait_sum += w
                    waited += 1
                    busy -= 1
                    if queue:
                        busy += 1
                        st = t
                        sv = queue.pop(0)[1]
                        dep_t = t + sv
                        dep_sv = sv
                        dep_st = st
                        next_dep = dep_t
                    else:
                        next_dep = float('inf')
                else:
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if n > 0 else 0) * dt
                        areaOcc += min(n, c) * dt
                    t = next_arr
                    if t > H:
                        break
                    arr += 1
                    if n < cap:
                        n += 1
                        svc = rng.expovariate(mu)
                        queue.append([t, svc])
                        if busy < c:
                            busy += 1
                            st = t
                            sv = queue.pop(0)[1]
                            dep_t = t + sv
                            dep_sv = sv
                            dep_st = st
                            next_dep = dep_t
                    else:
                        blk += 1
                    next_arr = t + rng.expovariate(lam)

        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        bu = areaOcc / (c * win) if win > 0 else 0.0
        W = wait_sum / waited if waited > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / arr if arr > 0 else 0.0
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
        tot_wait += wait_sum
        tot_waited += waited
        tot_win += win

    ns = len(seeds)
    win = tot_win / ns if ns else 0.0
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    bf = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    bu = tot_areaOcc / (c * tot_win) if tot_win > 0 else 0.0
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    arr = tot_arr / ns if ns else 0.0
    dep = tot_dep / ns if ns else 0.0
    blk = tot_blk / ns if ns else 0.0
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    pw = tot_waited / tot_arr if tot_arr > 0 else 0.0
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': bu, 'dep': dep,
        'dep_rate': dep_rate, 'lam_eff': lam_eff, 'p_wait': pw,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
