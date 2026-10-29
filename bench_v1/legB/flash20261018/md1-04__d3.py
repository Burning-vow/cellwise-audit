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
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = tot_waited = 0.0
    tot_served = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        area = 0.0
        busy_area = 0.0
        win_area = 0.0
        win_busy = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_waited = 0
        win_served = 0
        last = 0.0
        while t < H:
            if next_arr <= t:
                dt = next_arr - last
                if next_arr > warm:
                    area += n * dt
                    busy_area += busy * dt
                    win_area += n * dt
                    win_busy += busy * dt
                last = next_arr
                t = next_arr
                if t >= H:
                    break
                svc = 1.0 / mu
                if n < c:
                    n += 1
                    busy = 1
                    queue.append((t, svc, t))
                    if t >= warm:
                        win_arr += 1
                        win_served += 1
                        win_wait += 0.0
                        win_waited += 1
                else:
                    if t >= warm:
                        win_arr += 1
                        win_blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if queue:
                    st, svc, at = queue[0]
                    end = st + svc
                    if end <= t:
                        queue.pop(0)
                        n -= 1
                        if n == 0:
                            busy = 0
                        if end >= warm:
                            win_dep += 1
                        continue
                dt = min(next_arr, H) - last
                if last >= warm:
                    area += n * dt
                    busy_area += busy * dt
                    win_area += n * dt
                    win_busy += busy * dt
                last = min(next_arr, H)
                t = last
                if queue:
                    st, svc, at = queue[0]
                    end = st + svc
                    if end <= t:
                        queue.pop(0)
                        n -= 1
                        if n == 0:
                            busy = 0
                        if end >= warm:
                            win_dep += 1
        dt = H - last
        if last >= warm and dt > 0:
            area += n * dt
            busy_area += busy * dt
            win_area += n * dt
            win_busy += busy * dt
        wl = H - warm
        L = win_area / wl if wl > 0 else 0.0
        bf = win_busy / wl if wl > 0 else 0.0
        W = (win_wait / win_served) if win_served > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_waited / win_arr if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_win += wl
        tot_wait += win_wait
        tot_waited += win_waited
        tot_served += win_served

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': bf,
        'busy_util': bf, 'busy_occupied': bf,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': tot_win / ns,
        'arr': arr, 'blk': blk, 'busy_util': bf, 'dep': dep,
        'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
