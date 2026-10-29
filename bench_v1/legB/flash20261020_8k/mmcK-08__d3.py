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
    win = H - warm

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaBusy = tot_areaOcc = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0

    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        arr = dep = blk = 0
        areaN = areaBusy = areaOcc = 0.0
        wait_sum = 0.0
        served = 0
        waited = 0
        last = 0.0
        while True:
            if next_arr <= t:
                ev = next_arr
            elif queue:
                ev = queue[0][0]
            else:
                ev = next_arr
            if ev > H:
                dt = H - last
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if n > 0 else 0) * dt
                    areaOcc += min(n, c) * dt
                break
            dt = ev - last
            if t >= warm:
                areaN += n * dt
                areaBusy += (1 if n > 0 else 0) * dt
                areaOcc += min(n, c) * dt
            last = ev
            t = ev
            if ev == next_arr:
                arr += 1
                if n < cap:
                    n += 1
                    st = rng.expovariate(mu)
                    if busy < c:
                        busy += 1
                        queue.append((t + st, st))
                    else:
                        queue.append((t + st, st))
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                queue.pop(0)
                busy -= 1
                n -= 1
                dep += 1
                if t >= warm:
                    served += 1
                if busy < c and queue:
                    pass
        if t >= warm:
            pass
        per_L.append(areaN / win if win > 0 else 0.0)
        per_bf.append(areaBusy / win if win > 0 else 0.0)
        per_pl.append(blk / arr if arr > 0 else 0.0)
        per_pw.append(0.0)
        per_W.append(0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaBusy += areaBusy
        tot_areaOcc += areaOcc

    seeds_used = a.seeds
    L = tot_areaN / (win * seeds_used) if win > 0 and seeds_used > 0 else 0.0
    busy_frac = tot_areaBusy / (win * seeds_used) if win > 0 and seeds_used > 0 else 0.0
    busy_util = tot_areaOcc / (win * seeds_used * c) if win > 0 and seeds_used > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr_avg = tot_arr / seeds_used if seeds_used > 0 else 0.0
    dep_avg = tot_dep / seeds_used if seeds_used > 0 else 0.0
    blk_avg = tot_blk / seeds_used if seeds_used > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    lam_eff = arr_avg / win if win > 0 else 0.0
    W = L / lam_eff if lam_eff > 0 else 0.0
    W = W * 60.0
    p_wait = 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'minute',
        'seed_list': [a.seed_start + i for i in range(seeds_used)],
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'dep': dep_avg,
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
