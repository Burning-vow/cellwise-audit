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
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        wait = 0.0
        busy = 0.0
        last = 0.0
        nxt_arr = rng.expovariate(lam)
        s1 = None
        s2 = None
        while t < H:
            cand = [nxt_arr]
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
            if t == nxt_arr:
                arr += 1
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                cust = [t, svc1, svc2]
                if s1 is None:
                    s1 = t + svc1
                    n1 += 1
                    cust[0] = t
                    q1.append(cust)
                else:
                    q1.append(cust)
                    n1 += 1
                nxt_arr = t + rng.expovariate(lam)
            elif s1 is not None and t == s1:
                c = q1.pop(0)
                n1 -= 1
                if t >= warm:
                    wait += t - c[0]
                if s2 is None:
                    s2 = t + c[2]
                    n2 += 1
                    c[0] = t
                    q2.append(c)
                else:
                    q2.append(c)
                    n2 += 1
                if q1:
                    s1 = t + q1[0][1]
                else:
                    s1 = None
            elif s2 is not None and t == s2:
                c = q2.pop(0)
                n2 -= 1
                dep += 1
                if t >= warm:
                    wait += t - c[0]
                if q2:
                    s2 = t + q2[0][2]
                else:
                    s2 = None
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = wait / dep if dep > 0 else 0.0
        bf = busy / (2.0 * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = 1.0 if (n1 + n2) > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_wait += wait
        tot_busy += busy
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_dep if tot_dep > 0 else 0.0
    bf = tot_busy / (2.0 * tot_win) if tot_win > 0 else 0.0
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    pw = sum(per_pw) / ns if ns > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = lam * (1.0 - pl)

    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': tot_arr / ns if ns > 0 else 0.0,
        'blk': tot_blk / ns if ns > 0 else 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': tot_dep / ns if ns > 0 else 0.0,
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
