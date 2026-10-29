import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
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
    tot_busy = 0.0
    tot_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        n1 = 0
        n2 = 0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        area = 0.0
        wait_area = 0.0
        wait_n = 0
        last = 0.0
        while True:
            if s1 is None:
                t1 = math.inf
            else:
                t1 = s1
            if s2 is None:
                t2 = math.inf
            else:
                t2 = s2
            tn = t + rng.expovariate(lam)
            te = min(t1, t2, tn)
            if te > H:
                dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy += (1 if s1 is not None else 0) * dt + (1 if s2 is not None else 0) * dt
                t = H
                break
            dt = te - t
            if t >= warm:
                area += (n1 + n2) * dt
                busy += (1 if s1 is not None else 0) * dt + (1 if s2 is not None else 0) * dt
            t = te
            if te == tn:
                arr += 1
                svc = rng.expovariate(mu1)
                if s1 is None:
                    s1 = t + svc
                    n1 += 1
                else:
                    q1.append(svc)
                    n1 += 1
            elif te == t1:
                s1 = None
                n1 -= 1
                dep1 = True
                svc2 = rng.expovariate(mu2)
                if s2 is None:
                    s2 = t + svc2
                    n2 += 1
                else:
                    q2.append(svc2)
                    n2 += 1
                if q1:
                    s1 = t + q1.pop(0)
            else:
                s2 = None
                n2 -= 1
                dep += 1
                if t >= warm:
                    wait_n += 1
                if q2:
                    s2 = t + q2.pop(0)
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = (area / dep) if dep > 0 else 0.0
        bf = busy / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = (wait_n / dep) if dep > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_busy += busy
        tot_area += area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
    n = len(seeds)
    win = H - warm
    L = (tot_area / n) / win if win > 0 else 0.0
    W = (tot_area / tot_dep) if tot_dep > 0 else 0.0
    bf = (tot_busy / n) / (2.0 * win) if win > 0 else 0.0
    arr_avg = tot_arr / n
    dep_avg = tot_dep / n
    blk_avg = tot_blk / n
    dep_rate = dep_avg / win if win > 0 else 0.0
    lam_eff = arr_avg / win if win > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = (tot_wait_n / tot_dep) if tot_dep > 0 else 0.0
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
