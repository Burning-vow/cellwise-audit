import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=str, default='100')
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    H = float(a.horizon)
    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pP = []; pPW = []
    tA = 0.0; tD = 0.0; tB = 0.0; tDep = 0.0; tArr = 0.0; tBlk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        areaN = 0.0; areaB = 0.0
        nArr = 0; nDep = 0; nBlk = 0; nWait = 0
        last = 0.0
        while t < H:
            if busy:
                dt = min(rem, H - t)
            else:
                dt = H - t
            if not busy:
                dt = rng.expovariate(lam) if lam > 0 else float('inf')
                dt = min(dt, H - t)
            if busy:
                areaN += n * dt
                areaB += dt
                rem -= dt
                t += dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    nDep += 1
                    if queue:
                        cust = queue.pop(0)
                        busy = True
                        rem = cust[1]
                        n += 1
                        nWait += 1
            else:
                areaN += n * dt
                t += dt
                if t >= H:
                    break
                nArr += 1
                svc = rng.expovariate(mu)
                if n < K:
                    if not busy:
                        busy = True
                        rem = svc
                        n += 1
                    else:
                        queue.append((t, svc))
                        n += 1
                else:
                    nBlk += 1
        wlen = H - warm
        if wlen <= 0:
            wlen = H
            warm = 0.0
        L = areaN / H if H > 0 else 0.0
        B = areaB / H if H > 0 else 0.0
        pL.append(L)
        pB.append(B)
        pP.append(nBlk / nArr if nArr > 0 else 0.0)
        pW.append(0.0)
        pPW.append(nWait / nArr if nArr > 0 else 0.0)
        tA += nArr; tD += nDep; tB += nBlk
        tDep += nDep
    ns = len(seeds)
    L = sum(pL) / ns
    busy_frac = sum(pB) / ns
    p_loss = sum(pP) / ns
    p_wait = sum(pPW) / ns
    W = L / (lam * (1 - p_loss)) if lam * (1 - p_loss) > 0 else 0.0
    arr = tA / ns
    dep = tD / ns
    blk = tB / ns
    dep_rate = dep / H if H > 0 else 0.0
    busy_util = busy_frac
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam * (1 - p_loss),
        'p_wait': p_wait,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
        'busy_occupied': busy_frac
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
