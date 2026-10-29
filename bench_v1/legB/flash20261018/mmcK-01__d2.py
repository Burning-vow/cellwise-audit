import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 5.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 3
        cap = 5

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
    tot_busy_area = 0.0
    tot_util_area = 0.0
    tot_n_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        arr_w = 0
        dep_w = 0
        blk_w = 0
        busy_area = 0.0
        util_area = 0.0
        n_area = 0.0
        wait_area = 0.0
        wait_n = 0
        win_start = warm
        win_len = H - warm
        while t < H:
            if next_arr <= t:
                dt = next_arr - t
                if t >= win_start:
                    busy_area += (1 if busy > 0 else 0) * dt
                    util_area += min(busy, c) * dt
                    n_area += (busy + len(queue)) * dt
                t = next_arr
                if busy + len(queue) < cap:
                    svc = rng.expovariate(mu)
                    if busy < c:
                        busy += 1
                        queue.append((t, svc))
                    else:
                        queue.append((t, svc))
                    if t >= win_start:
                        arr_w += 1
                else:
                    if t >= win_start:
                        arr_w += 1
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if not queue:
                    dt = min(next_arr, H) - t
                    if t >= win_start:
                        busy_area += (1 if busy > 0 else 0) * dt
                        util_area += min(busy, c) * dt
                        n_area += (busy + len(queue)) * dt
                    t = min(next_arr, H)
                    continue
                queue.sort(key=lambda x: x[0] + x[1])
                start, svc = queue[0]
                end = start + svc
                if end <= t:
                    queue.pop(0)
                    busy -= 1
                    if t >= win_start:
                        dep_w += 1
                        wait_area += (start - (start - svc)) if False else 0
                    continue
                dt = min(end, next_arr, H) - t
                if t >= win_start:
                    busy_area += (1 if busy > 0 else 0) * dt
                    util_area += min(busy, c) * dt
                    n_area += (busy + len(queue)) * dt
                t = min(end, next_arr, H)
                if t == end:
                    queue.pop(0)
                    busy -= 1
                    if t >= win_start:
                        dep_w += 1
        L = n_area / win_len if win_len > 0 else 0.0
        bf = busy_area / win_len if win_len > 0 else 0.0
        util = util_area / win_len if win_len > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 0.0
        W = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy_area += busy_area
        tot_util_area += util_area
        tot_n_area += n_area
        tot_win += win_len

    ns = len(seeds)
    L = tot_n_area / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    busy_util = tot_util_area / (tot_win * c) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0
    W = L / lam_eff * 60.0 if lam_eff > 0 else 0.0
    p_wait = 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': tot_win / ns,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
