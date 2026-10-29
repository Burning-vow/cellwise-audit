import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_served = 0.0
    win_total = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        served_cnt = 0
        last_t = 0.0
        while t < H:
            if next_arr <= t:
                dt = next_arr - last_t
                if next_arr >= warm:
                    area += n * dt
                    busy_area += (1 if busy > 0 else 0) * dt
                last_t = next_arr
                t = next_arr
                if t >= warm:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    st = rng.expovariate(mu)
                    queue.append((t, st, t))
                else:
                    queue.append((t, None, None))
                next_arr = t + rng.expovariate(lam)
            else:
                if not queue:
                    dt = min(next_arr, H) - last_t
                    if t >= warm or (t < warm and t + dt > warm):
                        lo = max(t, warm)
                        hi = min(t + dt, H)
                        if hi > lo:
                            area += n * (hi - lo)
                            busy_area += (1 if busy > 0 else 0) * (hi - lo)
                    last_t = min(next_arr, H)
                    t = last_t
                    continue
                arr_t, st, start_t = queue[0]
                if st is None:
                    st = rng.expovariate(mu)
                    queue[0] = (arr_t, st, t)
                    start_t = t
                end_t = start_t + st
                dt = min(end_t, next_arr, H) - last_t
                if dt > 0:
                    lo = max(last_t, warm)
                    hi = min(last_t + dt, H)
                    if hi > lo:
                        area += n * (hi - lo)
                        busy_area += (1 if busy > 0 else 0) * (hi - lo)
                    last_t += dt
                    t = last_t
                if t >= end_t - 1e-12:
                    queue.pop(0)
                    busy -= 1
                    n -= 1
                    if t >= warm:
                        dep_w += 1
                        served_cnt += 1
                        wait_sum += start_t - arr_t
                        if start_t > arr_t:
                            waited_cnt += 1
                if t >= H:
                    break
        win = H - warm
        win_total += win
        L = area / win if win > 0 else 0.0
        W = (wait_sum + served_cnt * (1.0 / mu)) / served_cnt if served_cnt > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waited_cnt / served_cnt if served_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_served += served_cnt
    nseeds = len(seeds)
    win = win_total / nseeds if nseeds > 0 else 0.0
    L = sum(per_L) / nseeds if nseeds > 0 else 0.0
    W = sum(per_W) / nseeds if nseeds > 0 else 0.0
    bf = sum(per_bf) / nseeds if nseeds > 0 else 0.0
    arr = tot_arr / nseeds if nseeds > 0 else 0.0
    dep = tot_dep / nseeds if nseeds > 0 else 0.0
    blk = tot_blk / nseeds if nseeds > 0 else 0.0
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    p_loss = sum(per_pl) / nseeds if nseeds > 0 else 0.0
    p_wait = sum(per_pw) / nseeds if nseeds > 0 else 0.0
    busy_util = bf
    busy_occupied = bf
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': nseeds,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
