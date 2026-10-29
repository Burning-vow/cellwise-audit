import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 12.0
    K = 6
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pP = []; pPW = []
    tarr = 0.0; tdep = 0.0; tblk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        q = []
        arr = 0; dep = 0; blk = 0
        area_n = 0.0; area_busy = 0.0; area_wait = 0.0
        wait_sum = 0.0; wait_cnt = 0
        last = 0.0
        while True:
            if n > 0:
                dt = rng.expovariate(lam + mu)
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                    area_wait += len(q) * (H - t)
                break
            if t < H:
                area_n += n * (nt - t)
                area_busy += busy * (nt - t)
                area_wait += len(q) * (nt - t)
            t = nt
            if n > 0 and rng.random() < mu / (lam + mu):
                n -= 1
                busy = 1 if n > 0 else 0
                if n > 0:
                    q.pop(0)
                if t >= warm:
                    dep += 1
                    tdep += 1
            else:
                if n < K:
                    n += 1
                    busy = 1
                    svc = rng.expovariate(mu)
                    if n > 1:
                        q.append(svc)
                    if t >= warm:
                        arr += 1
                        tarr += 1
                else:
                    if t >= warm:
                        blk += 1
                        tblk += 1
        win = H - warm
        L = area_n / win
        bf = area_busy / win
        pw = area_wait / win
        pl = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        W = L / (arr / win) if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pP.append(pl); pPW.append(pw)
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pP) / ns
    pw = sum(pPW) / ns
    win = H - warm
    arr_avg = tarr / ns
    dep_avg = tdep / ns
    blk_avg = tblk / ns
    dep_rate = dep_avg / win
    busy_util = bf
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': arr_avg / win,
        'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
