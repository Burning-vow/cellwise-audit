import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
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
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_wait = 0.0
    tot_nwait = 0
    tot_area = 0.0
    tot_busy_area = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        events = []
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wsum = 0.0
        wcnt = 0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        last_t = 0.0
        win_start = warm
        win_len = H - warm
        while True:
            if next_arr <= t:
                ev_t = next_arr
            else:
                ev_t = None
                for sv in servers:
                    if sv is not None and (ev_t is None or sv[0] < ev_t):
                        ev_t = sv[0]
                if ev_t is None:
                    ev_t = next_arr
            if ev_t > H:
                break
            dt = ev_t - t
            if t >= win_start:
                area += n * dt
                busy_area += busy * dt
            elif ev_t > win_start:
                area += n * (ev_t - win_start)
                busy_area += busy * (ev_t - win_start)
            t = ev_t
            if t == next_arr:
                n += 1
                if t >= win_start:
                    arr_cnt += 1
                svc = rng.expovariate(mu)
                cust = [svc, t]
                if busy < c:
                    for i in range(c):
                        if servers[i] is None:
                            servers[i] = [t + svc, t, svc]
                            busy += 1
                            break
                    if t >= win_start:
                        wsum += 0.0
                        wcnt += 1
                else:
                    queue.append(cust)
                    if t >= win_start:
                        blk_cnt += 1
                next_arr = t + rng.expovariate(lam)
            else:
                for i in range(c):
                    if servers[i] is not None and servers[i][0] == t:
                        servers[i] = None
                        busy -= 1
                        if t >= win_start:
                            dep_cnt += 1
                        if queue:
                            cust = queue.pop(0)
                            svc, at = cust
                            servers[i] = [t + svc, at, svc]
                            busy += 1
                            if t >= win_start:
                                wsum += (t - at) + svc
                                wcnt += 1
                        break
        per_L.append(area / win_len if win_len > 0 else 0.0)
        per_W.append(wsum / wcnt if wcnt > 0 else 0.0)
        per_busy.append(busy_area / (win_len * c) if win_len > 0 else 0.0)
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk_cnt
        tot_wait += wsum
        tot_nwait += wcnt
        tot_area += area
        tot_busy_area += busy_area
        win_total += win_len

    L = tot_area / win_total if win_total > 0 else 0.0
    W = tot_wait / tot_nwait if tot_nwait > 0 else 0.0
    p_wait = tot_blk / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (win_total / 60.0) if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'arr': tot_arr / len(seeds),
        'blk': tot_blk / len(seeds),
        'dep': tot_dep / len(seeds),
        'dep_rate': dep_rate,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': win_total / len(seeds)
    }
    print(json.dumps(out))

main()
