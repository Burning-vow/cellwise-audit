import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
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

    per_L = []
    per_W = []
    per_busy = []
    per_ploss = []
    per_pwait = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy_area = 0.0
    tot_wait = 0.0
    tot_wait_n = 0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_n = 0
        win_start = warm
        win_len = H - warm
        last_t = 0.0
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                area += n * (H - t)
                busy_area += busy * (H - t)
                t = H
                break
            area += n * (nt - t)
            busy_area += busy * (nt - t)
            t = nt
            svc = 1.0 / mu
            if c == 1:
                if busy == 0:
                    busy = 1
                    queue.append((t, svc))
                else:
                    queue.append((t, svc))
            else:
                if busy < c:
                    busy += 1
                    queue.append((t, svc))
                else:
                    queue.append((t, svc))
            n = len(queue)
            if t >= win_start:
                arr_w += 1
            while queue and queue[0][0] + queue[0][1] <= t:
                st, sv = queue.pop(0)
                if st + sv >= win_start:
                    dep_w += 1
                    wait_sum += (st + sv - st)
                    wait_n += 1
                busy -= 1
                n = len(queue)
            if t >= win_start:
                pass
        per_L.append(area / H if H > 0 else 0.0)
        per_W.append((area / H) / lam if lam > 0 else 0.0)
        per_busy.append(busy_area / H if H > 0 else 0.0)
        per_ploss.append(0.0)
        per_pwait.append(1.0 if arr_w > 0 else 0.0)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy_area += busy_area
        tot_wait += wait_sum
        tot_wait_n += wait_n
        tot_win += win_len

    L = tot_area / (H * len(seeds)) if H > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy_area / (H * len(seeds)) if H > 0 else 0.0
    dep_rate = (tot_dep / len(seeds)) / (tot_win / len(seeds)) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / len(seeds)) / (tot_win / len(seeds)) * 60.0 if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = (tot_wait_n / tot_arr) if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac / c,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': tot_win / len(seeds),
        'arr': tot_arr / len(seeds),
        'dep': tot_dep / len(seeds),
        'blk': tot_blk / len(seeds),
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
