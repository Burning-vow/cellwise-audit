import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=str, default='200')
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
    tA = 0.0; tD = 0.0; tBlk = 0.0; tDep = 0.0
    tBusy = 0.0; tOcc = 0.0; tWait = 0.0; tArrW = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        queue = []
        cur_end = 0.0
        arr = 0; blk = 0; dep = 0; waitc = 0
        areaL = 0.0; areaBusy = 0.0; areaOcc = 0.0; areaWait = 0.0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            tnext = t + dt
            if tnext > H:
                break
            if busy and cur_end <= tnext:
                te = cur_end
                if te > last:
                    seg = te - last
                    if last >= warm:
                        areaL += n * seg
                        areaBusy += (1 if busy else 0) * seg
                        areaOcc += min(n, K) * seg
                        areaWait += len(queue) * seg
                    last = te
                t = te
                n -= 1
                dep += 1
                if queue:
                    svc = queue.pop(0)
                    cur_end = t + svc
                    busy = True
                else:
                    busy = False
                continue
            if tnext > last:
                seg = tnext - last
                if last >= warm:
                    areaL += n * seg
                    areaBusy += (1 if busy else 0) * seg
                    areaOcc += min(n, K) * seg
                    areaWait += len(queue) * seg
                last = tnext
            t = tnext
            arr += 1
            svc = rng.expovariate(mu)
            if n < K:
                n += 1
                if not busy:
                    busy = True
                    cur_end = t + svc
                else:
                    queue.append(svc)
                    waitc += 1
            else:
                blk += 1
        if last < H:
            seg = H - last
            if last >= warm:
                areaL += n * seg
                areaBusy += (1 if busy else 0) * seg
                areaOcc += min(n, K) * seg
                areaWait += len(queue) * seg
        win = H - warm
        L = areaL / win
        W = (areaWait / win) / max(lam * (1 - blk / max(arr, 1)), 1e-12) if arr > 0 else 0.0
        bf = areaBusy / win
        pl = blk / max(arr, 1)
        pw = waitc / max(arr - blk, 1)
        pL.append(L); pW.append(W); pB.append(bf); pP.append(pl); pPW.append(pw)
        tA += arr; tD += dep; tBlk += blk
        tBusy += areaBusy; tOcc += areaOcc; tWait += areaWait; tArrW += arr
    ns = len(seeds)
    win = H - warm
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pP) / ns
    pw = sum(pPW) / ns
    arr_m = tA / ns
    dep_m = tD / ns
    blk_m = tBlk / ns
    dep_rate = dep_m / win
    busy_util = (tOcc / ns) / win / K
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr_m, 'blk': blk_m, 'busy_util': busy_util,
        'busy_occupied': bf, 'dep': dep_m, 'dep_rate': dep_rate,
        'lam_eff': lam * (1 - pl), 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
