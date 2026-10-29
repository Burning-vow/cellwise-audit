import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 14.0 / 60.0
    mu = 1.0 / 6.0
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
    tot_arr = tot_dep = tot_blk = 0.0
    tot_L = tot_W = tot_bf = tot_pl = tot_pw = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        dep_times = []
        blk = 0
        area_n = 0.0
        area_q = 0.0
        area_busy = 0.0
        wsum = 0.0
        wcnt = 0
        waitcnt = 0
        arrcnt = 0
        last = 0.0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                area_n += n * (H - t)
                area_q += len(queue) * (H - t)
                area_busy += busy * (H - t)
                t = H
                break
            area_n += n * (nt - t)
            area_q += len(queue) * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                svc = rng.expovariate(mu)
                arrcnt += 1
                if t >= warm:
                    arr_times.append(t)
                if busy < c:
                    busy += 1
                    servers.append((t + svc, svc))
                    if t >= warm:
                        wsum += svc
                        wcnt += 1
                else:
                    if t >= warm:
                        blk += 1
                    else:
                        pass
                    queue.append((t, svc))
            else:
                servers.sort()
                endt, svc = servers.pop(0)
                busy -= 1
                if queue:
                    at, qsvc = queue.pop(0)
                    if at >= warm:
                        wsum += (t - at) + qsvc
                        wcnt += 1
                        waitcnt += 1
                    busy += 1
                    servers.append((t + qsvc, qsvc))
                if t >= warm:
                    dep_times.append(t)
        win = H - warm
        L = area_n / win
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_busy / (c * win)
        pl = blk / arrcnt if arrcnt > 0 else 0.0
        pw = waitcnt / wcnt if wcnt > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(pl); pPW.append(pw)
        tot_L += L; tot_W += W; tot_bf += bf; tot_pl += pl; tot_pw += pw
        tot_arr += len(arr_times)
        tot_dep += len(dep_times)
        tot_blk += blk
    ns = len(seeds)
    L = tot_L / ns
    W = tot_W / ns
    bf = tot_bf / ns
    pl = tot_pl / ns
    pw = tot_pw / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (H - warm) * 60.0
    lam_eff = lam * 60.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_wait': pw,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H - warm,
        'arr': arr, 'blk': blk, 'busy_util': bf, 'dep': dep,
        'dep_rate': dep_rate, 'lam_eff': lam_eff, 'p_loss': pl,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL, 'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
