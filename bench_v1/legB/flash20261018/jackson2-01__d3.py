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
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        n1 = 0
        n2 = 0
        area = 0.0
        busy = 0.0
        arr = 0
        dep = 0
        blk = 0
        waitc = 0
        waitn = 0
        last = 0.0
        while True:
            if s1 is None and q1:
                s1 = q1.pop(0)
                s1[1] = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                s2[1] = t
            cand = []
            if s1 is not None:
                cand.append(s1[2])
            if s2 is not None:
                cand.append(s2[2])
            if t < H:
                cand.append(t + rng.expovariate(lam))
            if not cand:
                break
            tn = min(cand)
            if tn > H:
                tn = H
            dt = tn - t
            if t >= warm:
                area += (n1 + n2) * dt
                if s1 is not None:
                    busy += dt
                if s2 is not None:
                    busy += dt
            t = tn
            if t >= H:
                break
            if s1 is not None and abs(s1[2] - t) < 1e-12:
                n1 -= 1
                dep += 1
                if t >= warm:
                    waitc += 1
                    waitn += (t - s1[0])
                s2v = [s1[0], None, t + rng.expovariate(mu2)]
                s1 = None
                if s2 is None:
                    s2 = s2v
                    s2[1] = t
                else:
                    q2.append(s2v)
                n2 += 1
                continue
            if s2 is not None and abs(s2[2] - t) < 1e-12:
                n2 -= 1
                dep += 1
                s2 = None
                continue
            arr += 1
            sv = [t, None, t + rng.expovariate(mu1)]
            if s1 is None:
                s1 = sv
                s1[1] = t
            else:
                q1.append(sv)
            n1 += 1
        win = H - warm
        pL.append(area / win if win > 0 else 0.0)
        pW.append((waitn / waitc) if waitc > 0 else 0.0)
        pB.append(busy / (2.0 * win) if win > 0 else 0.0)
        pPL.append(blk / arr if arr > 0 else 0.0)
        pPW.append(waitc / arr if arr > 0 else 0.0)
        tarr += arr
        tdep += dep
        tblk += blk
    ns = len(seeds)
    L = sum(pL) / ns if ns else 0.0
    W = sum(pW) / ns if ns else 0.0
    bf = sum(pB) / ns if ns else 0.0
    pl = sum(pPL) / ns if ns else 0.0
    pw = sum(pPW) / ns if ns else 0.0
    win = H - warm
    dep_rate = (tdep / ns) / win * 60.0 if win > 0 else 0.0
    lam_eff = (tarr / ns) / win * 60.0 if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': 'minute',
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tarr / ns if ns else 0.0,
        'blk': tblk / ns if ns else 0.0,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': tdep / ns if ns else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
        'p_wait': pw,
        'per_seed_L': pL,
        'per_seed_W': pW,
        'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
