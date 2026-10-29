import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu1 = 1.0 / 7.5
    mu2 = 1.0 / 6.0
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
    pL = []
    pW = []
    pB = []
    pPL = []
    pPW = []
    tarr = 0.0
    tdep = 0.0
    tblk = 0.0
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
        while True:
            if s1 is None and q1:
                s1 = q1.pop(0)
                b1 = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                b2 = t
            tn = t + rng.expovariate(lam)
            td = math.inf
            if s1 is not None:
                td = min(td, b1 + s1[1])
            if s2 is not None:
                td = min(td, b2 + s2[1])
            if tn <= td:
                dt = tn - t
                if t >= warm:
                    area += (n1 + n2) * dt
                t = tn
                if t > H:
                    break
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                if t >= warm:
                    arr += 1
                if n1 >= 1000:
                    if t >= warm:
                        blk += 1
                    continue
                n1 += 1
                q1.append((t, svc1, svc2))
            else:
                dt = td - t
                if t >= warm:
                    area += (n1 + n2) * dt
                t = td
                if t > H:
                    break
                if s1 is not None and abs(t - (b1 + s1[1])) < 1e-12:
                    n1 -= 1
                    item = s1
                    s1 = None
                    n2 += 1
                    q2.append(item)
                elif s2 is not None:
                    n2 -= 1
                    item = s2
                    s2 = None
                    if t >= warm:
                        dep += 1
                        wsum += t - item[0]
                        wcnt += 1
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = (b1 + b2) / (2.0 * H) if H > 0 else 0.0
        pL.append(L)
        pW.append(W)
        pB.append(bf)
        pPL.append(blk / arr if arr > 0 else 0.0)
        pPW.append(1.0 - (dep / arr) if arr > 0 else 0.0)
        tarr += arr
        tdep += dep
        tblk += blk
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    win = H - warm
    arr_avg = tarr / ns
    dep_avg = tdep / ns
    blk_avg = tblk / ns
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
        'p_loss': blk_avg / arr_avg if arr_avg > 0 else 0.0,
        'p_wait': 1.0 - (dep_avg / arr_avg) if arr_avg > 0 else 0.0,
        'per_seed_L': pL,
        'per_seed_W': pW,
        'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
