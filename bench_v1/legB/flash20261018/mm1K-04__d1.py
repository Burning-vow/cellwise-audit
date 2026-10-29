import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        cap = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL, pW, pB, pP, pPW = [], [], [], [], []
    tA = tD = tB = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        q = []
        wA = wD = wB = 0.0
        wT = 0.0
        wN = 0.0
        wBusy = 0.0
        wWait = 0.0
        wWaitN = 0.0
        wDep = 0
        wArr = 0
        wBlk = 0
        while t < H:
            rate = lam + (mu if busy else 0.0)
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if busy:
                    wBusy += (H - t) * (1 if busy else 0)
                    wN += (H - t) * n
                break
            if busy:
                wBusy += dt
                wN += dt * n
            t = nt
            if rng.random() < lam / rate:
                svc = rng.expovariate(mu)
                if n < cap:
                    n += 1
                    if t >= warm:
                        wArr += 1
                    if not busy:
                        busy = True
                        rem = svc
                    else:
                        q.append(svc)
                        if t >= warm:
                            wWait += 1
                else:
                    if t >= warm:
                        wBlk += 1
            else:
                if t >= warm:
                    wDep += 1
                if q:
                    rem = q.pop(0)
                else:
                    busy = False
                    rem = 0.0
                    n -= 1
                    if n < 0:
                        n = 0
        win = H - warm
        L = wN / win if win > 0 else 0.0
        W = (wN / wDep) if wDep > 0 else 0.0
        bf = wBusy / win if win > 0 else 0.0
        pl = wBlk / wArr if wArr > 0 else 0.0
        pw = wWait / wArr if wArr > 0 else 0.0
        pL.append(L)
        pW.append(W)
        pB.append(bf)
        pP.append(pl)
        pPW.append(pw)
        tA += wArr
        tD += wDep
        tB += wBlk
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
    busy_util = L / cap
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW,
        'per_seed_busy_frac': pB, 'per_seed_p_loss': pP,
        'per_seed_p_wait': pPW,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
