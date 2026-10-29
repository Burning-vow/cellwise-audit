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
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    tarr = 0.0; tdep = 0.0; tblk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        areaN = 0.0
        areaBusy = 0.0
        areaOcc = 0.0
        arr = 0; dep = 0; blk = 0
        waitSum = 0.0; waitCnt = 0
        queue = []
        serverFree = True
        nextArr = rng.expovariate(lam)
        while t < H:
            if serverFree:
                if queue:
                    tnext = queue[0][0]
                else:
                    tnext = nextArr
            else:
                tnext = min(queue[0][0] if queue else float('inf'), nextArr)
            if tnext > H:
                dt = H - t
                areaN += n * dt
                areaBusy += (1 if n > 0 else 0) * dt
                areaOcc += min(n, K) * dt
                t = H
                break
            dt = tnext - t
            areaN += n * dt
            areaBusy += (1 if n > 0 else 0) * dt
            areaOcc += min(n, K) * dt
            t = tnext
            if t == nextArr:
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    queue.append((t + svc, t))
                    if t >= warm:
                        arr += 1
                else:
                    if t >= warm:
                        blk += 1
                nextArr = t + rng.expovariate(lam)
            else:
                dept, at = queue.pop(0)
                if t >= warm:
                    dep += 1
                    waitSum += (t - at)
                    waitCnt += 1
                n -= 1
                if not queue:
                    serverFree = True
                else:
                    serverFree = False
        win = H - warm
        L = areaN / win
        W = (waitSum / waitCnt) if waitCnt > 0 else 0.0
        bf = areaBusy / win
        bu = areaOcc / win / K
        pl = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        pw = waitCnt / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pLoss.append(pl); pWait.append(pw)
        tarr += arr; tdep += dep; tblk += blk
    ns = len(seeds)
    win = H - warm
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pLoss) / ns
    pw = sum(pWait) / ns
    arr_avg = tarr / ns
    dep_avg = tdep / ns
    blk_avg = tblk / ns
    dep_rate = dep_avg / win
    lam_eff = arr_avg / win
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': bu if False else sum(pB)/ns,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pLoss, 'per_seed_p_wait': pWait,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
