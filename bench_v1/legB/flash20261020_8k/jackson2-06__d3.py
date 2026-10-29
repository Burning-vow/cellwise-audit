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
        n1 = 0
        n2 = 0
        b1 = 0.0
        b2 = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        wsum = 0.0
        wcnt = 0
        last = 0.0
        while True:
            if s1 is None:
                t1 = float('inf')
            else:
                t1 = s1
            if s2 is None:
                t2 = float('inf')
            else:
                t2 = s2
            ta = t + rng.expovariate(lam)
            tn = min(t1, t2, ta)
            if tn > H:
                dt = H - t
                if t >= warm:
                    area += (n1 + n2) * dt
                    b1 += (1.0 if s1 is not None else 0.0) * dt
                    b2 += (1.0 if s2 is not None else 0.0) * dt
                t = H
                break
            dt = tn - t
            if t >= warm:
                area += (n1 + n2) * dt
                b1 += (1.0 if s1 is not None else 0.0) * dt
                b2 += (1.0 if s2 is not None else 0.0) * dt
            t = tn
            if tn == ta:
                arr += 1
                svc = rng.expovariate(mu1)
                if s1 is None:
                    s1 = t + svc
                    n1 += 1
                    if t >= warm:
                        wsum += svc
                        wcnt += 1
                else:
                    q1.append((t, svc))
                    n1 += 1
            elif tn == t1:
                s1 = None
                n1 -= 1
                if q1:
                    at, svc = q1.pop(0)
                    s1 = t + svc
                    if t >= warm:
                        wsum += (t - at) + svc
                        wcnt += 1
                if s2 is None:
                    svc2 = rng.expovariate(mu2)
                    s2 = t + svc2
                    n2 += 1
                    if t >= warm:
                        wsum += svc2
                        wcnt += 1
                else:
                    q2.append((t, rng.expovariate(mu2)))
                    n2 += 1
            else:
                s2 = None
                n2 -= 1
                dep += 1
                if q2:
                    at, svc = q2.pop(0)
                    s2 = t + svc
                    if t >= warm:
                        wsum += (t - at) + svc
                        wcnt += 1
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = (b1 + b2) / (2.0 * win) if win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if wcnt > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    win = H - warm
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / win * 60.0 if win > 0 else 0.0
    lam_eff = arr_avg / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': 0.0,
        'p_wait': sum(per_pw) / ns,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
