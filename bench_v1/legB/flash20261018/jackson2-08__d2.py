import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu1 = 60.0/6.0
    mu2 = 60.0/5.0
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
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seed_list.append(s)
        rng = random.Random(s)
        t = 0.0
        nxt = rng.expovariate(lam)
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        s1end = 0.0
        s2end = 0.0
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        area1 = 0.0
        area2 = 0.0
        busy1 = 0.0
        busy2 = 0.0
        waitc = 0
        arrc = 0
        last = 0.0
        while True:
            cand = [nxt]
            if s1 is not None:
                cand.append(s1end)
            if s2 is not None:
                cand.append(s2end)
            tn = min(cand)
            if tn > H:
                dt = H - last
                area += (len(q1) + len(q2) + (1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
                if s1 is not None:
                    area1 += (len(q1) + 1) * dt
                    busy1 += dt
                else:
                    area1 += len(q1) * dt
                if s2 is not None:
                    area2 += (len(q2) + 1) * dt
                    busy2 += dt
                else:
                    area2 += len(q2) * dt
                break
            dt = tn - last
            if dt > 0:
                area += (len(q1) + len(q2) + (1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
                if s1 is not None:
                    area1 += (len(q1) + 1) * dt
                    busy1 += dt
                else:
                    area1 += len(q1) * dt
                if s2 is not None:
                    area2 += (len(q2) + 1) * dt
                    busy2 += dt
                else:
                    area2 += len(q2) * dt
            last = tn
            if tn == nxt:
                arr += 1
                svc = rng.expovariate(mu1)
                if s1 is None:
                    s1 = svc
                    s1end = tn + svc
                else:
                    q1.append(svc)
                nxt = tn + rng.expovariate(lam)
            elif s1 is not None and tn == s1end:
                dep1 = True
                if q1:
                    svc = q1.pop(0)
                    s1 = svc
                    s1end = tn + svc
                else:
                    s1 = None
                if s2 is None:
                    s2 = rng.expovariate(mu2)
                    s2end = tn + s2
                else:
                    q2.append(rng.expovariate(mu2))
            elif s2 is not None and tn == s2end:
                dep += 1
                if q2:
                    svc = q2.pop(0)
                    s2 = svc
                    s2end = tn + svc
                else:
                    s2 = None
        win = H - warm
        if win <= 0:
            win = H
        L = area / H
        W = area / max(arr, 1) * 60.0
        bf = (busy1 + busy2) / (2.0 * H)
        pl = blk / max(arr, 1)
        pw = waitc / max(arrc, 1) if arrc > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
    n = len(per_L)
    L = sum(per_L) / n
    W = sum(per_W) / n
    bf = sum(per_bf) / n
    pl = sum(per_pl) / n
    pw = sum(per_pw) / n
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': 0.0,
        'blk': 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': 0.0,
        'dep_rate': 0.0,
        'lam_eff': lam,
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
