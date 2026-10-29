import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cap = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pP = []; pPW = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaBusy = 0.0
    tot_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        arr = dep = blk = 0
        areaN = 0.0
        areaBusy = 0.0
        wsum = 0.0
        wcnt = 0
        waitcnt = 0
        last = 0.0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    areaN += n * (H - t)
                    areaBusy += (1.0 if busy else 0.0) * (H - t)
                break
            if t >= warm:
                areaN += n * (nt - t)
                areaBusy += (1.0 if busy else 0.0) * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                if n < cap:
                    svc = rng.expovariate(mu)
                    if n == 0 and not busy:
                        busy = True
                        rem = svc
                        n = 1
                        if t >= warm:
                            waitcnt += 1
                    else:
                        queue.append(svc)
                        n += 1
                else:
                    blk += 1
            else:
                dep += 1
                if t >= warm:
                    wsum += rem
                    wcnt += 1
                if queue:
                    svc = queue.pop(0)
                    rem = svc
                    busy = True
                    if t >= warm:
                        waitcnt += 1
                else:
                    busy = False
                    rem = 0.0
                    n = 0
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaBusy / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waitcnt / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pP.append(pl); pPW.append(pw)
        tot_arr += arr; tot_dep += dep; tot_blk += blk
        tot_areaN += areaN; tot_areaBusy += areaBusy
        tot_win += win
    nseeds = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    W = sum(pW) / nseeds if nseeds > 0 else 0.0
    p_loss = sum(pP) / nseeds if nseeds > 0 else 0.0
    p_wait = sum(pPW) / nseeds if nseeds > 0 else 0.0
    arr_avg = tot_arr / nseeds if nseeds > 0 else 0.0
    dep_avg = tot_dep / nseeds if nseeds > 0 else 0.0
    blk_avg = tot_blk / nseeds if nseeds > 0 else 0.0
    win_avg = tot_win / nseeds if nseeds > 0 else 0.0
    dep_rate = dep_avg / win_avg if win_avg > 0 else 0.0
    busy_util = L / cap if cap > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_loss': p_loss,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': nseeds,
        'time_unit': 'minute', 'win': win_avg,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': arr_avg / win_avg if win_avg > 0 else 0.0,
        'p_wait': p_wait,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
        'busy_occupied': busy_frac
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
