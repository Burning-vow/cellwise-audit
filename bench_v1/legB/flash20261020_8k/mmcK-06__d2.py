import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 3
    cap = 4
    lam = 6.0
    mu = 10.0
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 4
        cap = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = 0
        q = []
        areaN = 0.0
        areaBusy = 0.0
        areaOcc = 0.0
        areaQ = 0.0
        arr = 0; dep = 0; blk = 0
        waitSum = 0.0; waitCnt = 0
        winStart = warm
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                dt = H - t
                nt = H
            if dt > 0:
                lo = max(t, winStart)
                hi = nt
                if hi > lo:
                    areaN += (hi - lo) * n
                    areaBusy += (hi - lo) * (1 if busy > 0 else 0)
                    areaOcc += (hi - lo) * busy
                    areaQ += (hi - lo) * len(q)
            t = nt
            if t >= H:
                break
            if n < cap:
                n += 1
                arr += 1
                svc = rng.expovariate(mu)
                q.append((t, svc))
                if busy < c:
                    busy += 1
                    st, s = q.pop(0)
                    if st >= winStart:
                        waitSum += 0.0
                        waitCnt += 1
                    dep_t = t + s
                    q.append((dep_t, -1))
                    q.sort(key=lambda x: x[0])
            else:
                blk += 1
            while q and q[0][1] == -1 and q[0][0] <= t:
                q.pop(0)
                busy -= 1
                n -= 1
                dep += 1
                if busy > 0 and q:
                    st, s = q.pop(0)
                    if st >= winStart:
                        waitSum += t - st
                        waitCnt += 1
                    dep_t = t + s
                    q.append((dep_t, -1))
                    q.sort(key=lambda x: x[0])
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        bu = areaOcc / (c * win) if win > 0 else 0.0
        W = waitSum / waitCnt if waitCnt > 0 else 0.0
        loss = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        pw = waitCnt / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pLoss.append(loss); pWait.append(pw)
        tot_arr += arr; tot_dep += dep; tot_blk += blk
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    loss = sum(pLoss) / ns
    pw = sum(pWait) / ns
    arr_m = tot_arr / ns
    dep_m = tot_dep / ns
    blk_m = tot_blk / ns
    win = H - warm
    dep_rate = dep_m / win if win > 0 else 0.0
    lam_eff = arr_m / win if win > 0 else 0.0
    busy_util = bf * c / c if c > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': win,
        'arr': arr_m, 'blk': blk_m, 'busy_util': busy_util,
        'dep': dep_m, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pLoss, 'per_seed_p_wait': pWait,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
