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
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    tarr = 0.0; tdep = 0.0; tblk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        queue = []
        cur_end = 0.0
        cur_svc = 0.0
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wsum = 0.0; wcnt = 0
        arr = 0; dep = 0; blk = 0
        last = 0.0
        while True:
            if busy:
                dt = cur_end - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_occ += min(n, cap) * dt
                t += dt
                if t >= H:
                    break
                busy = False
                n -= 1
                dep += 1
                if queue:
                    svc, arr_t = queue.pop(0)
                    cur_svc = svc
                    cur_end = t + svc
                    busy = True
                    n += 1
                    w = t - arr_t
                    if t >= warm:
                        wsum += w; wcnt += 1
                continue
            dt = rng.expovariate(lam)
            if t + dt > H:
                if t >= warm:
                    area_n += n * (H - t)
                    area_busy += 0.0
                    area_occ += min(n, cap) * (H - t)
                t = H
                break
            if t >= warm:
                area_n += n * dt
                area_busy += 0.0
                area_occ += min(n, cap) * dt
            t += dt
            arr += 1
            svc = rng.expovariate(mu)
            if n < cap:
                n += 1
                cur_svc = svc
                cur_end = t + svc
                busy = True
            else:
                blk += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wsum / wcnt if wcnt > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_occ / (cap * win) if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = wcnt / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(pl); pPW.append(pw)
        tarr += arr; tdep += dep; tblk += blk
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pPL) / ns
    pw = sum(pPW) / ns
    win = H - warm
    arr_avg = tarr / ns
    dep_avg = tdep / ns
    blk_avg = tblk / ns
    dep_rate = dep_avg / win if win > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': bf,
        'dep': dep_avg, 'dep_rate': dep_rate,
        'lam_eff': arr_avg / win if win > 0 else 0.0,
        'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL, 'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
