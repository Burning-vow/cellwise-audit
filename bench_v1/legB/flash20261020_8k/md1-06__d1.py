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
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_wait_n = 0.0
    tot_served = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        in_service = []
        area = 0.0
        busy_area = 0.0
        win_area = 0.0
        arr_c = dep_c = blk_c = 0
        wait_sum = 0.0
        wait_n = 0
        served = 0
        last_t = 0.0
        while t < H:
            dt_arr = next_arr - t
            dt_dep = float('inf')
            if in_service:
                dt_dep = in_service[0][0] - t
            dt = min(dt_arr, dt_dep)
            if dt > 0:
                if t >= warm:
                    end = min(t + dt, H)
                    if end > t:
                        area += n * (end - t)
                        busy_area += min(n, c) * (end - t)
                        win_area += (end - t)
                t += dt
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12:
                arr_c += 1
                n += 1
                st = rng.expovariate(mu)
                if len(in_service) < c:
                    in_service.append([t + st, st])
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                else:
                    queue.append(st)
                next_arr = t + rng.expovariate(lam)
            else:
                if in_service and abs(t - in_service[0][0]) < 1e-12:
                    in_service.pop(0)
                    dep_c += 1
                    served += 1
                    n -= 1
                    if queue:
                        st = queue.pop(0)
                        in_service.append([t + st, st])
                        if t >= warm:
                            wait_sum += 0.0
                            wait_n += 1
        if win_area > 0:
            L = area / win_area
            bf = busy_area / win_area
        else:
            L = 0.0
            bf = 0.0
        W = L / (lam * (1.0 if c == 1 else 1.0)) if lam > 0 else 0.0
        if dep_c > 0:
            W = (area / dep_c) if dep_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_win += win_area
        tot_wait += wait_sum
        tot_wait_n += wait_n
        tot_served += served

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    W = (tot_area / tot_dep) if tot_dep > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    p_wait = (tot_wait_n / tot_arr) if tot_arr > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'dep': dep, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
