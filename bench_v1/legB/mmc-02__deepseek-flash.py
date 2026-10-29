import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
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

    per_L, per_W, per_busy = [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area_L = tot_area_busy = 0.0
    tot_wait = 0.0
    tot_served = 0
    tot_waiters = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        area_L = 0.0
        area_busy = 0.0
        wait_sum = 0.0
        served = 0
        waiters = 0
        arr_cnt = dep_cnt = blk_cnt = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            tnext = next_arr
            for sv in servers:
                if sv is not None and sv[0] < tnext:
                    tnext = sv[0]
            if tnext > H:
                break
            dt = tnext - last
            if t > warm:
                area_L += n * dt
                area_busy += busy * dt
            last = tnext
            t = tnext
            if t == next_arr:
                n += 1
                if t > warm:
                    arr_cnt += 1
                if busy < c:
                    busy += 1
                    st = t + rng.expovariate(mu)
                    servers[busy - 1] = (st, t)
                else:
                    if t > warm:
                        blk_cnt += 1
                    queue.append(t)
                next_arr = t + rng.expovariate(lam)
            else:
                for i in range(c):
                    if servers[i] is not None and servers[i][0] == t:
                        _, at = servers[i]
                        if t > warm:
                            dep_cnt += 1
                            wait_sum += t - at
                            served += 1
                        n -= 1
                        if queue:
                            qt = queue.pop(0)
                            if t > warm:
                                waiters += 1
                            st = t + rng.expovariate(mu)
                            servers[i] = (st, qt)
                        else:
                            busy -= 1
                            servers[i] = None
                        break
        win = H - warm
        win_total += win
        tot_area_L += area_L
        tot_area_busy += area_busy
        tot_wait += wait_sum
        tot_served += served
        tot_waiters += waiters
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk_cnt
        per_L.append(area_L / win if win > 0 else 0.0)
        per_W.append(wait_sum / served if served > 0 else 0.0)
        per_busy.append(area_busy / (win * c) if win > 0 else 0.0)

    L = tot_area_L / win_total if win_total > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    p_wait = tot_waiters / tot_dep if tot_dep > 0 else 0.0
    dep_rate = tot_dep / (win_total / 60.0) if win_total > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)

    out = {
        'L': L, 'W': W, 'arr': arr, 'blk': blk, 'dep': dep,
        'dep_rate': dep_rate, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_total / len(seeds)
    }
    print(json.dumps(out))

main()
