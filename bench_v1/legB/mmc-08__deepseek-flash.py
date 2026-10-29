import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c += 1

    seeds = [a.seed_start + i for i in range(a.seeds)]
    H = a.horizon
    warm = 0.25 * H

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_wait = 0.0
    tot_soj = 0.0
    tot_win = 0.0
    tot_dep_win = 0.0
    tot_wait_n = 0
    tot_waiters = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        nxt = rng.expovariate(lam)
        servers = [0.0] * c
        queue = []
        area = 0.0
        last = 0.0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        wait_sum = 0.0
        wait_n = 0
        waiters = 0
        busy_area = 0.0
        while True:
            busy = sum(1 for x in servers if x > 0)
            if nxt <= t:
                ev = nxt
            else:
                ev = t
            if ev > H:
                break
            if ev > last:
                area += (ev - last) * (len(queue) + busy)
                busy_area += (ev - last) * busy
                last = ev
            if nxt <= t:
                t = nxt
                nxt = t + rng.expovariate(lam)
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_win += 1
                if busy < c:
                    for i in range(c):
                        if servers[i] <= 0:
                            servers[i] = t + svc
                            break
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        waiters += 1
            else:
                t = ev
                for i in range(c):
                    if servers[i] > 0 and abs(servers[i] - t) < 1e-12:
                        servers[i] = 0.0
                        if t >= warm:
                            dep_win += 1
                        if queue:
                            at, svc = queue.pop(0)
                            w = t - at
                            if t >= warm:
                                wait_sum += w
                                wait_n += 1
                            servers[i] = t + svc
                        break
        win = H - warm
        L = area / H
        W = (wait_sum / wait_n) if wait_n > 0 else 0.0
        busy_frac = busy_area / H
        per_L.append(L)
        per_W.append(W)
        per_busy.append(busy_frac)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += waiters
        tot_wait += wait_sum
        tot_wait_n += wait_n
        tot_soj += area
        tot_win += win
        tot_dep_win += dep_win

    n = len(seeds)
    L = sum(per_L) / n
    W = (tot_wait / tot_wait_n) if tot_wait_n > 0 else 0.0
    p_wait = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'arr': tot_arr / n,
        'blk': tot_blk / n,
        'dep': tot_dep / n,
        'dep_rate': dep_rate,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': tot_win / n,
    }
    print(json.dumps(out))

main()
