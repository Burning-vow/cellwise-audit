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
        area_q = 0.0
        area_b = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        pw_cnt = 0
        arr_cnt = 0
        last = 0.0
        while True:
            if n == 0:
                t = t + rng.expovariate(lam)
            else:
                t = t + rng.expovariate(lam)
            if t > H:
                break
            dt = t - last
            if t > warm:
                area_n += n * dt
                area_q += len(queue) * dt
                area_b += busy * dt
            last = t
            n += 1
            svc = rng.expovariate(mu)
            if t > warm:
                arr_w += 1
                arr_cnt += 1
            if busy < c:
                busy += 1
                servers.append((t + svc, svc))
                if t > warm:
                    wait_sum += 0.0
                    wait_cnt += 1
            else:
                queue.append((t, svc))
                if t > warm:
                    pw_cnt += 1
            while servers and servers[0][0] <= t:
                servers.pop(0)
                busy -= 1
                if t > warm:
                    dep_w += 1
                if queue:
                    at, sv = queue.pop(0)
                    st = t
                    if st > warm:
                        wait_sum += st - at
                        wait_cnt += 1
                    busy += 1
                    servers.append((st + sv, sv))
                    servers.sort()
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        Lq = area_q / win if win > 0 else 0.0
        bf = area_b / (c * win) if win > 0 else 0.0
        W = (Lq / (arr_w / win) + 1.0 / mu) if arr_w > 0 else 0.0
        pwait = pw_cnt / arr_cnt if arr_cnt > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf)
        pPL.append(0.0); pPW.append(pwait)
        tarr += arr_w; tdep += dep_w; tblk += blk_w
    ns = len(seeds)
    L = sum(pL) / ns
    W = sum(pW) / ns
    bf = sum(pB) / ns
    pw = sum(pPW) / ns
    win = H - warm
    arr = tarr / ns
    dep = tdep / ns
    blk = tblk / ns
    dep_rate = dep / win if win > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_wait': pw,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': bf, 'dep': dep,
        'dep_rate': dep_rate, 'lam_eff': lam, 'p_loss': 0.0,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL, 'per_seed_p_wait': pPW,
        'busy_occupied': bf
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
