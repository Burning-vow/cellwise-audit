import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0
    mean_s = 0.1
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    r1 = mean_s / (2.0 * p)
    r2 = mean_s / (2.0 * (1.0 - p))

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr = dep = blk = 0
        win_arr = dep_w = blk_w = 0
        last = 0.0
        while t < H:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next_arr = t + dt
            t_next_dep = t + rem if busy else float('inf')
            t_next = min(t_next_arr, t_next_dep, H)
            dtw = t_next - t
            if t >= warm:
                area += n * dtw
                busy_area += (1 if busy else 0) * dtw
            if t_next >= H:
                t = H
                break
            if t_next_arr <= t_next_dep:
                t = t_next_arr
                arr += 1
                if t >= warm:
                    win_arr += 1
                if busy:
                    queue.append((t, r1 if rng.random() < p else r2))
                else:
                    s = r1 if rng.random() < p else r2
                    busy = True
                    rem = s
                    n += 1
                    if t >= warm:
                        wait_n += 1
            else:
                t = t_next_dep
                n -= 1
                dep += 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, s = queue.pop(0)
                    if t >= warm:
                        wait_area += (t - at)
                    busy = True
                    rem = s
                    n += 1
                else:
                    busy = False
                    rem = 0.0
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = (wait_area / wait_n) if wait_n > 0 else 0.0
        pl = blk_w / win_arr if win_arr > 0 else 0.0
        pw = (wait_n / win_arr) if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    p_wait = (tot_wait_n / tot_arr) if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': H - warm,
        'arr': arr,
        'dep': dep,
        'blk': blk,
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
