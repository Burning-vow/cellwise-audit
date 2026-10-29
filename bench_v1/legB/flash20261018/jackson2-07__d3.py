import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu1 = 10.0
    mu2 = 10.0
    if a.pert == 'lam_up':
        lam = 7.2
    elif a.pert == 'mu_up':
        mu1 = 12.0
        mu2 = 12.0
    elif a.pert == 'c_up':
        mu1 = 10.0
        mu2 = 10.0

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
    tot_area = 0.0
    tot_wait = 0.0
    tot_busy = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n1 = 0
        n2 = 0
        b1 = 0.0
        b2 = 0.0
        q1 = []
        q2 = []
        arr_c = 0
        dep_c = 0
        blk_c = 0
        area = 0.0
        wait_sum = 0.0
        busy = 0.0
        last = 0.0
        next_arr = rng.expovariate(lam)
        s1 = None
        s2 = None
        while t < H:
            cand = [next_arr]
            if s1 is not None:
                cand.append(s1)
            if s2 is not None:
                cand.append(s2)
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy += ((1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
            t = nt
            if t >= H:
                break
            if s1 is not None and abs(t - s1) < 1e-12:
                n1 -= 1
                svc = q1.pop(0)
                q2.append(svc)
                n2 += 1
                s1 = None
                if q1:
                    s1 = t + q1[0][1]
                if s2 is None and q2:
                    job = q2.pop(0)
                    s2 = t + job[1]
            if s2 is not None and abs(t - s2) < 1e-12:
                n2 -= 1
                dep_c += 1
                s2 = None
                if q2:
                    job = q2.pop(0)
                    s2 = t + job[1]
            if abs(t - next_arr) < 1e-12:
                arr_c += 1
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                job = (t, svc1, svc2)
                if s1 is None:
                    s1 = t + svc1
                    n1 += 1
                else:
                    q1.append((t, svc1, svc2))
                    n1 += 1
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = (area / dep_c * 60.0) if dep_c > 0 else 0.0
        bf = busy / (2.0 * win) if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy
        tot_win += win

    n = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_area / tot_dep * 60.0) if tot_dep > 0 else 0.0
    bf = tot_busy / (2.0 * tot_win) if tot_win > 0 else 0.0
    arr = tot_arr / n
    dep = tot_dep / n
    blk = tot_blk / n
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = dep_rate
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 0.0

    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': H - warm,
        'arr': arr,
        'blk': blk,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
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
