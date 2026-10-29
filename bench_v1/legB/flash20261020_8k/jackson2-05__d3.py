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
    pLoss = []
    pWait = []
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
        waited = 0
        area1 = 0.0
        area2 = 0.0
        areaW = 0.0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                break
            if nt > last:
                area1 += n1 * (nt - last)
                area2 += n2 * (nt - last)
                areaW += (n1 + n2) * (nt - last)
                last = nt
            t = nt
            arr += 1
            svc1 = rng.expovariate(mu1)
            svc2 = rng.expovariate(mu2)
            if n1 == 0 and b1 <= t:
                b1 = t + svc1
                n1 = 1
                q1.append((t, svc1, svc2))
            else:
                q1.append((t, svc1, svc2))
                n1 += 1
            while q1 and b1 <= t:
                at, s1, s2 = q1.pop(0)
                if at < t:
                    waited += 1
                b1 = max(b1, at) + s1
                if n2 == 0 and b2 <= b1:
                    b2 = b1 + s2
                    n2 = 1
                else:
                    q2.append((b1, s2))
                    n2 += 1
                while q2 and b2 <= b1:
                    at2, s2b = q2.pop(0)
                    b2 = max(b2, at2) + s2b
                    n2 -= 1
                n1 -= 1
            while q2 and b2 <= t:
                at2, s2b = q2.pop(0)
                b2 = max(b2, at2) + s2b
                n2 -= 1
            if b1 <= t and q1:
                at, s1, s2 = q1.pop(0)
                b1 = t + s1
                if n2 == 0 and b2 <= b1:
                    b2 = b1 + s2
                    n2 = 1
                else:
                    q2.append((b1, s2))
                    n2 += 1
                n1 -= 1
            if b2 <= t and q2:
                at2, s2b = q2.pop(0)
                b2 = t + s2b
                n2 -= 1
        if H > last:
            area1 += n1 * (H - last)
            area2 += n2 * (H - last)
            areaW += (n1 + n2) * (H - last)
        win = H - warm
        L = areaW / win if win > 0 else 0.0
        W = L / (arr / win) if arr > 0 else 0.0
        bf = (area1 + area2) / win if win > 0 else 0.0
        pL.append(L)
        pW.append(W)
        pB.append(bf)
        pLoss.append(blk / arr if arr > 0 else 0.0)
        pWait.append(waited / arr if arr > 0 else 0.0)
    n = len(seeds)
    out = {
        'L': sum(pL) / n,
        'W': sum(pW) / n,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': sum(pB) / n,
        'busy_util': sum(pB) / n,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': lam,
        'p_loss': sum(pLoss) / n,
        'p_wait': sum(pWait) / n,
        'per_seed_L': pL,
        'per_seed_W': pW,
        'per_seed_busy_frac': pB,
        'per_seed_p_loss': pLoss,
        'per_seed_p_wait': pWait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
