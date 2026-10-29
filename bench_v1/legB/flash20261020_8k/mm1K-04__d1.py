import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pP = []; pPW = []
    tA = 0.0; tD = 0.0; tB = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        q = []
        areaN = 0.0; areaB = 0.0
        arr = 0; dep = 0; blk = 0; waitc = 0; waitT = 0.0
        last = 0.0
        while t < H:
            if busy:
                dt = min(rem, H - t)
                if t < warm:
                    d = min(dt, max(0.0, warm - t))
                    areaN += n * d
                    areaB += (1 if n > 0 else 0) * d
                else:
                    areaN += n * dt
                    areaB += (1 if n > 0 else 0) * dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep += 1
                    if t >= warm:
                        tD += 1
                    if q:
                        q2 = []
                        for (ta, sv) in q:
                            if not busy:
                                busy = True
                                rem = sv
                                waitT += t - ta
                                waitc += 1
                            else:
                                q2.append((ta, sv))
                        q = q2
                continue
            dt = rng.expovariate(lam)
            if t + dt >= H:
                if t < warm:
                    d = min(dt, max(0.0, warm - t))
                    areaN += n * d
                    areaB += (1 if n > 0 else 0) * d
                else:
                    areaN += n * dt
                    areaB += (1 if n > 0 else 0) * dt
                t = H
                break
            if t < warm:
                d = min(dt, max(0.0, warm - t))
                areaN += n * d
                areaB += (1 if n > 0 else 0) * d
            else:
                areaN += n * dt
                areaB += (1 if n > 0 else 0) * dt
            t += dt
            sv = rng.expovariate(mu)
            if t >= warm:
                arr += 1
                tA += 1
            if n < K:
                if not busy:
                    busy = True
                    rem = sv
                    n += 1
                    if t >= warm:
                        waitc += 1
                        waitT += 0.0
                else:
                    q.append((t, sv))
                    n += 1
            else:
                if t >= warm:
                    blk += 1
                    tB += 1
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        W = (waitT / waitc) if waitc > 0 else 0.0
        bf = areaB / win if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waitc / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pP.append(pl); pPW.append(pw)
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pP) / ns
    pw = sum(pPW) / ns
    win = H - warm
    arr = tA / ns
    dep = tD / ns
    blk = tB / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
