import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 10.0 / 60.0
    mu = 1.0 / 10.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    tL = 0.0; tW = 0.0; tB = 0.0; tArr = 0.0; tDep = 0.0; tBlk = 0.0
    tWin = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_q = 0.0
        area_b = 0.0
        wsum = 0.0
        wcnt = 0
        arr = 0; dep = 0; blk = 0
        waitcnt = 0
        last = 0.0
        while True:
            if servers:
                nt = min(servers)
            else:
                nt = float('inf')
            if queue:
                nq = queue[0][0]
            else:
                nq = float('inf')
            if nq < nt:
                tn = nq
            else:
                tn = nt
            if tn > H:
                tn = H
            dt = tn - t
            if dt > 0:
                if t >= warm:
                    e = min(tn, H) - max(t, warm)
                    if e > 0:
                        area_n += n * e
                        area_q += len(queue) * e
                        area_b += busy * e
                t = tn
            if t >= H:
                break
            if nq <= nt:
                at, st = queue.pop(0)
                servers.append(t + st)
                busy += 1
                if t >= warm:
                    wsum += t - at
                    wcnt += 1
            else:
                servers.remove(nt)
                busy -= 1
                if t >= warm:
                    dep += 1
            if not servers and not queue:
                pass
            if t >= H:
                break
            if rng.random() < lam * 1.0:
                pass
            if True:
                if not servers and not queue:
                    gap = rng.expovariate(lam)
                    if t + gap > H:
                        if t >= warm:
                            e = H - max(t, warm)
                            if e > 0:
                                area_n += n * e
                                area_q += len(queue) * e
                                area_b += busy * e
                        t = H
                        break
                    t = t + gap
                    if t >= H:
                        break
                if t >= warm:
                    arr += 1
                st = rng.expovariate(mu)
                if len(servers) < c:
                    servers.append(t + st)
                    busy += 1
                    if t >= warm:
                        wsum += 0.0
                        wcnt += 1
                else:
                    if t >= warm:
                        blk += 1
                        waitcnt += 1
                    queue.append((t, st))
                n = len(servers) + len(queue)
                if t >= H:
                    break
        win = H - warm
        if win <= 0:
            win = H
        Lv = area_n / win if win > 0 else 0.0
        Wv = wsum / wcnt if wcnt > 0 else 0.0
        Bv = area_b / (c * win) if win > 0 else 0.0
        PLv = blk / arr if arr > 0 else 0.0
        PWv = waitcnt / arr if arr > 0 else 0.0
        pL.append(Lv); pW.append(Wv); pB.append(Bv); pPL.append(PLv); pPW.append(PWv)
        tL += Lv; tW += Wv; tB += Bv; tArr += arr; tDep += dep; tBlk += blk
        tWin += win
    ns = len(seeds)
    L = tL / ns
    W = tW / ns
    busy_frac = tB / ns
    p_wait = sum(pPW) / ns
    p_loss = sum(pPL) / ns
    arr_avg = tArr / ns
    dep_avg = tDep / ns
    blk_avg = tBlk / ns
    win_avg = tWin / ns
    dep_rate = dep_avg / win_avg if win_avg > 0 else 0.0
    lam_eff = arr_avg / win_avg if win_avg > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win_avg,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep_avg, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL, 'per_seed_p_wait': pPW
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
