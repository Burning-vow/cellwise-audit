import json, random, argparse, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 10.0 / 60.0
    mu = 1.0 / 10.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c += 1

    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_busy = [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area_n = tot_area_w = tot_area_b = 0.0
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
        events = []
        next_arr = rng.expovariate(lam)
        area_n = area_w = area_b = 0.0
        wait_sum = 0.0
        served = 0
        waiters = 0
        arr_c = dep_c = blk_c = 0
        last_t = 0.0
        while True:
            if next_arr <= t or not events:
                if next_arr > H and not events:
                    break
                if next_arr <= t:
                    dt = next_arr - last_t
                    if next_arr > warm:
                        area_n += n * dt
                        area_w += len(queue) * dt
                        area_b += busy * dt
                    last_t = next_arr
                    t = next_arr
                    n += 1
                    if t > warm:
                        arr_c += 1
                    if busy < c:
                        busy += 1
                        st = rng.expovariate(mu)
                        heapq.heappush(events, (t + st, st))
                    else:
                        queue.append(t)
                        if t > warm:
                            blk_c += 1
                    next_arr = t + rng.expovariate(lam)
                    continue
            if events:
                et, st = events[0]
                if et <= next_arr or next_arr > H:
                    heapq.heappop(events)
                    dt = et - last_t
                    if et > warm:
                        area_n += n * dt
                        area_w += len(queue) * dt
                        area_b += busy * dt
                    last_t = et
                    t = et
                    n -= 1
                    if t > warm:
                        dep_c += 1
                    if queue:
                        at = queue.pop(0)
                        w = t - at
                        if t > warm:
                            wait_sum += w
                            served += 1
                            waiters += 1
                        st2 = rng.expovariate(mu)
                        heapq.heappush(events, (t + st2, st2))
                    else:
                        busy -= 1
                    continue
            if next_arr > H and not events:
                break
            if next_arr > H and events:
                et, st = heapq.heappop(events)
                dt = et - last_t
                if et > warm:
                    area_n += n * dt
                    area_w += len(queue) * dt
                    area_b += busy * dt
                last_t = et
                t = et
                n -= 1
                if t > warm:
                    dep_c += 1
                if queue:
                    at = queue.pop(0)
                    w = t - at
                    if t > warm:
                        wait_sum += w
                        served += 1
                        waiters += 1
                    st2 = rng.expovariate(mu)
                    heapq.heappush(events, (t + st2, st2))
                else:
                    busy -= 1
                continue
            break

        win = H - warm
        Ls = area_n / win if win > 0 else 0.0
        Ws = (wait_sum / served) if served > 0 else 0.0
        Bs = area_b / (win * c) if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(Bs)
        tot_area_n += area_n
        tot_area_w += area_w
        tot_area_b += area_b
        tot_wait += wait_sum
        tot_served += served
        tot_waiters += waiters
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        win_total += win

    L = tot_area_n / win_total if win_total > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    p_wait = tot_waiters / tot_served if tot_served > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = tot_dep / (win_total / 60.0) if win_total > 0 else 0.0

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
