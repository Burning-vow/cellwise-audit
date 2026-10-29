import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 14.0 / 60.0
    mu = 1.0 / 6.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3

    H = a.horizon
    warm = 0.25 * H
    win = H - warm

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_wait = 0.0
    tot_nwait = 0
    tot_waitcnt = 0
    seeds = []

    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_cnt = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if next_arr <= t:
                ev = 'a'
            elif queue and busy < c:
                ev = 's'
            else:
                ev = 'a' if next_arr < float('inf') else 's'
            if ev == 'a':
                nt = next_arr
            else:
                nt = t
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area_n += n * dt
                area_busy += busy * dt
            t = nt
            if t >= H:
                break
            if ev == 'a':
                n += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    queue.append((t, svc, t))
                else:
                    queue.append((t, svc, None))
                    if t >= warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if queue and busy < c:
                    arr_t, svc, st = queue.pop(0)
                    if st is None:
                        st = t
                        if arr_t >= warm:
                            wait_sum += st - arr_t
                            wait_cnt += 1
                    busy += 1
                    queue.insert(0, (arr_t, svc, st))
                    queue.pop(0)
                    dep_t = t + svc
                    queue.append(('dep', dep_t))
                else:
                    pass
            while queue and queue[0][0] == 'dep' and queue[0][1] <= t:
                queue.pop(0)
                busy -= 1
                n -= 1
                if t >= warm:
                    dep_w += 1
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / (win * c) if win > 0 else 0.0
        W = (wait_sum / wait_cnt + 1.0 / mu) if wait_cnt > 0 else 1.0 / mu
        per_L.append(L)
        per_W.append(W)
        per_busy.append(bf)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_wait += wait_sum
        tot_nwait += wait_cnt

    Lm = sum(per_L) / len(per_L)
    Wm = sum(per_W) / len(per_W)
    bfm = sum(per_busy) / len(per_busy)
    p_wait = tot_blk / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (win * a.seeds) * 60.0
    out = {
        'L': Lm,
        'W': Wm,
        'arr': tot_arr / a.seeds,
        'blk': tot_blk / a.seeds,
        'dep': tot_dep / a.seeds,
        'dep_rate': dep_rate,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': win,
    }
    print(json.dumps(out))

main()
