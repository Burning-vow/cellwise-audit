import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 8.0 / 60.0
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
    tarr = 0.0; tdep = 0.0; tblk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_b = 0.0
        area_q = 0.0
        wsum = 0.0
        wcnt = 0
        arr = 0; dep = 0; blk = 0
        waitcnt = 0
        last = 0.0
        while True:
            if servers:
                nxt_dep = min(servers)
            else:
                nxt_dep = float('inf')
            dt = rng.expovariate(lam) if lam > 0 else float('inf')
            nxt_arr = t + dt
            tn = min(nxt_arr, nxt_dep)
            if tn > H:
                if t < H:
                    area_n += n * (H - t)
                    area_b += busy * (H - t)
                    area_q += len(queue) * (H - t)
                break
            area_n += n * (tn - t)
            area_b += busy * (tn - t)
            area_q += len(queue) * (tn - t)
            t = tn
            if nxt_arr <= nxt_dep:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    n += 1
                    if t >= warm:
                        wsum += svc
                        wcnt += 1
                else:
                    if t >= warm:
                        blk += 1
                    queue.append((t, svc))
                    n += 1
            else:
                servers.remove(nxt_dep)
                busy -= 1
                n -= 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    n += 1
                    if t >= warm:
                        wsum += (t - at) + svc
                        wcnt += 1
                        waitcnt += 1
                if t >= warm:
                    dep += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_b / (c * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waitcnt / wcnt if wcnt > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(pl); pPW.append(pw)
        tarr += arr; tdep += dep; tblk += blk
    ns = len(seeds)
    out = {
        'L': sum(pL)/ns,
        'W': sum(pW)/ns,
        'busy_frac': sum(pB)/ns,
        'busy_util': sum(pB)/ns,
        'busy_occupied': sum(pB)/ns,
        'p_wait': sum(pPW)/ns,
        'p_loss': sum(pPL)/ns,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': tarr/ns,
        'dep': tdep/ns,
        'blk': tblk/ns,
        'dep_rate': (tdep/ns)/(H-warm)*60.0 if H > warm else 0.0,
        'lam_eff': lam*60.0,
        'per_seed_L': pL,
        'per_seed_W': pW,
        'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
