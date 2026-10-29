import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu1 = 1.0 / 7.5
    mu2 = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu1 *= 1.2
        mu2 *= 1.2
    elif a.pert == 'c_up':
        lam *= 1.2
        mu1 *= 1.2
        mu2 *= 1.2
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
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        busy1 = False
        busy2 = False
        rem1 = 0.0
        rem2 = 0.0
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        area_busy = 0.0
        area_wait = 0.0
        n_wait = 0
        last = 0.0
        while True:
            if not busy1:
                dt1 = float('inf')
            else:
                dt1 = rem1
            if not busy2:
                dt2 = float('inf')
            else:
                dt2 = rem2
            dt = min(dt1, dt2)
            if t + dt > H:
                dt = H - t
                if t >= warm:
                    area += (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)) * dt
                    area_busy += ((1 if busy1 else 0) + (1 if busy2 else 0)) * dt
                t = H
                break
            if t >= warm:
                area += (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)) * dt
                area_busy += ((1 if busy1 else 0) + (1 if busy2 else 0)) * dt
            t += dt
            if busy1:
                rem1 -= dt
                if rem1 <= 1e-12:
                    busy1 = False
                    svc2 = rng.expovariate(mu2)
                    if not busy2:
                        busy2 = True
                        rem2 = svc2
                    else:
                        q2.append(svc2)
            if busy2:
                rem2 -= dt
                if rem2 <= 1e-12:
                    busy2 = False
                    dep += 1
                    if q2:
                        busy2 = True
                        rem2 = q2.pop(0)
            while True:
                ia = rng.expovariate(lam)
                if t + ia > H:
                    break
                t += ia
                if t >= warm:
                    area += (len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)) * ia
                    area_busy += ((1 if busy1 else 0) + (1 if busy2 else 0)) * ia
                arr += 1
                svc1 = rng.expovariate(mu1)
                if not busy1:
                    busy1 = True
                    rem1 = svc1
                else:
                    q1.append(svc1)
                if t >= H:
                    break
            if t >= H:
                break
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = L / (dep / win) if dep > 0 else 0.0
        bf = area_busy / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 1.0 if (arr > 0 and dep < arr) else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    n = len(seeds)
    win = H - warm
    L = sum(per_L) / n
    W = sum(per_W) / n
    bf = sum(per_bf) / n
    pl = sum(per_pl) / n
    pw = sum(per_pw) / n
    arr_avg = tot_arr / n
    dep_avg = tot_dep / n
    blk_avg = tot_blk / n
    dep_rate = dep_avg / win * 60.0 if win > 0 else 0.0
    lam_eff = arr_avg / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
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
