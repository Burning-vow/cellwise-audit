import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep_t = 0.0
    tot_n = 0
    tot_waiters = 0
    tot_arrivals = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        areaN = areaB = 0.0
        wait_sum = soj_sum = 0.0
        dep_cnt = 0
        dep_t_sum = 0.0
        arr_cnt = 0
        blk_cnt = 0
        waiters = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            cand = next_arr
            for sv in servers:
                if sv is not None and sv[0] < cand:
                    cand = sv[0]
            if cand > H:
                dt = H - last
                areaN += n * dt
                areaB += busy * dt
                last = H
                break
            dt = cand - last
            areaN += n * dt
            areaB += busy * dt
            last = cand
            t = cand
            if t == next_arr:
                arr_cnt += 1
                n += 1
                svc = rng.expovariate(mu)
                cust = [svc, t]
                free = -1
                for i in range(c):
                    if servers[i] is None:
                        free = i
                        break
                if free >= 0:
                    servers[free] = [t + svc, t, svc]
                    busy += 1
                else:
                    queue.append(cust)
                    waiters += 1
                next_arr = t + rng.expovariate(lam)
            else:
                for i in range(c):
                    if servers[i] is not None and servers[i][0] == t:
                        _, at, svc = servers[i]
                        servers[i] = None
                        busy -= 1
                        n -= 1
                        dep_cnt += 1
                        dep_t_sum += t
                        if t >= warm:
                            soj_sum += t - at
                        if queue:
                            q = queue.pop(0)
                            servers[i] = [t + q[0], q[1], q[0]]
                            busy += 1
                            if t >= warm:
                                wait_sum += t - q[1]
                        break
        if t < H:
            dt = H - t
            areaN += n * dt
            areaB += busy * dt
        win = H - warm
        L = areaN / H
        W = (soj_sum / dep_cnt) if dep_cnt > 0 else 0.0
        bf = (areaB / H) / c
        pl = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
        pw = waiters / arr_cnt if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_t += dep_t_sum
        tot_n += dep_cnt
        tot_arrivals += arr_cnt
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk_cnt
        tot_waiters += waiters

    L = tot_areaN / (H * len(seeds))
    W = (tot_soj / tot_n) if tot_n > 0 else 0.0
    busy_frac = (tot_areaB / (H * len(seeds))) / c
    p_wait = tot_waiters / tot_arrivals if tot_arrivals > 0 else 0.0
    p_loss = tot_blk / tot_arrivals if tot_arrivals > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = (tot_dep / (H * len(seeds))) * 60.0
    lam_eff = (tot_arr / (H * len(seeds))) * 60.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': H - warm,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': 1.0 - math.exp(-lam * H) if False else busy_frac,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
