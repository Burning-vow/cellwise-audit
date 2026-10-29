import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 12.0
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        cap = cap + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pP = []; pQ = []
    tarr = 0.0; tdep = 0.0; tblk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        q = []
        arr = 0; dep = 0; blk = 0
        area_n = 0.0; area_busy = 0.0; area_q = 0.0
        wsum = 0.0; wcnt = 0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                area_n += n * (H - t)
                area_busy += (1 if busy else 0) * (H - t)
                area_q += len(q) * (H - t)
                t = H
                break
            area_n += n * (nt - t)
            area_busy += (1 if busy else 0) * (nt - t)
            area_q += len(q) * (nt - t)
            t = nt
            svc = rng.expovariate(mu)
            if n >= cap:
                blk += 1
                if t >= warm:
                    tblk += 1
                continue
            n += 1
            arr += 1
            if t >= warm:
                tarr += 1
            if busy == 0:
                busy = 1
                endt = t + svc
                q.append((endt, t, svc))
            else:
                q.append((None, t, svc))
            while q and q[0][0] is not None and q[0][0] <= t:
                pass
            while q and q[0][0] is not None and q[0][0] <= t:
                e, at, sv = q.pop(0)
                n -= 1
                dep += 1
                if t >= warm:
                    tdep += 1
                wsum += e - at
                wcnt += 1
                if q:
                    nxt = q[0]
                    q[0] = (t + nxt[2], nxt[1], nxt[2])
                else:
                    busy = 0
            while q and q[0][0] is not None and q[0][0] <= t:
                e, at, sv = q.pop(0)
                n -= 1
                dep += 1
                if t >= warm:
                    tdep += 1
                wsum += e - at
                wcnt += 1
                if q:
                    nxt = q[0]
                    q[0] = (t + nxt[2], nxt[1], nxt[2])
                else:
                    busy = 0
        win = H - warm
        Lv = area_n / win
        Bv = area_busy / win
        Qv = area_q / win
        Wv = (wsum / wcnt) if wcnt > 0 else 0.0
        Pl = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        Pw = (wcnt / arr) if arr > 0 else 0.0
        pL.append(Lv); pW.append(Wv); pB.append(Bv); pP.append(Pl); pQ.append(Pw)
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    B = sum(pB) / ns
    Pl = sum(pP) / ns
    Pw = sum(pQ) / ns
    win = H - warm
    arr_avg = tarr / ns
    dep_avg = tdep / ns
    blk_avg = tblk / ns
    dep_rate = dep_avg / win
    out = {
        'L': L, 'W': W, 'busy_frac': B, 'p_loss': Pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': win,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': L / cap,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': arr_avg / win,
        'p_wait': Pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pQ,
        'busy_occupied': B
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
