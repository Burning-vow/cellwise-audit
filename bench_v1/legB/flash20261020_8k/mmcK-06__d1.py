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
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
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
        while t < H:
            if next_arr <= t:
                t = next_arr
                if t >= H:
                    break
                if n < cap:
                    n += 1
                    arr += 1
                    svc = rng.expovariate(mu)
                    queue.append([t, svc])
                    if busy < c:
                        busy += 1
                        st = t
                        arr_t, sv = queue.pop(0)
                        wait_sum += st - arr_t
                        waited += 1
                        dep_t = st + sv
                        queue.insert(0, [arr_t, sv])
                        queue[0].append(dep_t)
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if queue and len(queue[0]) > 2:
                    dt = queue[0][2]
                else:
                    dt = next_arr
                if dt > H:
                    dt = H
                areaN += n * (dt - t)
                areaBusy += (1 if busy > 0 else 0) * (dt - t)
                areaOcc += min(n, c) * (dt - t)
                t = dt
                while queue and len(queue[0]) > 2 and queue[0][2] <= t + 1e-12:
                    queue.pop(0)
                    n -= 1
                    busy -= 1
                    dep += 1
                    if queue and busy < c:
                        busy += 1
                        arr_t, sv = queue[0][0], queue[0][1]
                        wait_sum += t - arr_t
                        waited += 1
                        queue[0].append(t + sv)
        win = H - warm
        if win <= 0:
            win = H
        per_L.append(areaN / H)
        per_W.append(wait_sum / waited if waited > 0 else 0.0)
        per_bf.append(areaBusy / H)
        per_pl.append(blk / (arr + blk) if (arr + blk) > 0 else 0.0)
        per_pw.append(waited / arr if arr > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaBusy += areaBusy
        tot_areaOcc += areaOcc
        tot_wait += wait_sum
        tot_waited += waited
        tot_win += H

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    busy_frac = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    busy_util = tot_areaOcc / (c * tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / (tot_arr + tot_blk) if (tot_arr + tot_blk) > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = tot_arr / (tot_win / 60.0) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': tot_arr / ns if ns > 0 else 0.0,
        'blk': tot_blk / ns if ns > 0 else 0.0,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': tot_dep / ns if ns > 0 else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
