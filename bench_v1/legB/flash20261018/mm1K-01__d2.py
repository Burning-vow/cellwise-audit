import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu = 1.0 / 6.0
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cap += 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    tarr = 0.0; tdep = 0.0; tblk = 0.0; tbusy = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        arr = 0; dep = 0; blk = 0
        area_n = 0.0; area_busy = 0.0; area_wait = 0.0
        wait_sum = 0.0; wait_cnt = 0
        last = warm
        while t < H:
            if busy:
                dt = rem
            else:
                dt = float('inf')
            if n < cap:
                dt2 = rng.expovariate(lam)
            else:
                dt2 = float('inf')
            dt = min(dt, dt2)
            if dt == float('inf'):
                break
            nt = t + dt
            if nt > H:
                nt = H
            if nt > warm:
                seg = nt - max(t, warm)
                area_n += n * seg
                if busy:
                    area_busy += seg
                area_wait += len(queue) * seg
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    rem = 0.0
                    if t > warm:
                        dep += 1
                    if queue:
                        w, svc = queue.pop(0)
                        if t > warm:
                            wait_sum += (t - w)
                            wait_cnt += 1
                        busy = True
                        rem = svc
            if n < cap and dt2 <= dt + 1e-12 and abs(t - (nt)) < 1e-9:
                pass
            if n < cap:
                if dt2 <= dt + 1e-12:
                    svc = rng.expovariate(mu)
                    if t > warm:
                        arr += 1
                    if busy:
                        queue.append((t, svc))
                        n += 1
                    else:
                        busy = True
                        rem = svc
                        n += 1
            else:
                if dt2 <= dt + 1e-12:
                    if t > warm:
                        blk += 1
            if not busy and queue:
                w, svc = queue.pop(0)
                if t > warm:
                    wait_sum += (t - w)
                    wait_cnt += 1
                busy = True
                rem = svc
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        pl = blk / (arr + blk) if (arr + blk) > 0 else 0.0
        pw = wait_cnt / arr if arr > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(pl); pPW.append(pw)
        tarr += arr; tdep += dep; tblk += blk; tbusy += area_busy
    ns = len(seeds)
    win = H - warm
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pl = sum(pPL) / ns
    pw = sum(pPW) / ns
    arr_avg = tarr / ns
    dep_avg = tdep / ns
    blk_avg = tblk / ns
    dep_rate = dep_avg / win if win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_util,
        'dep': dep_avg, 'dep_rate': dep_rate,
        'lam_eff': lam, 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW,
        'per_seed_busy_frac': pB, 'per_seed_p_loss': pPL,
        'per_seed_p_wait': pPW,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
