import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
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
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        servers = []
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while t < H:
            if next_arr <= t:
                t = next_arr
                if t >= H:
                    break
                if t >= warm:
                    area += n * (t - last)
                    busy_area += min(n, c) * (t - last)
                last = t
                if n < c:
                    n += 1
                    svc = 1.0 / mu
                    servers.append((t + svc, t))
                    if t >= warm:
                        arr_w += 1
                        wait_sum += 0.0
                        wait_n += 1
                else:
                    if t >= warm:
                        arr_w += 1
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if not servers:
                    t = next_arr
                    continue
                servers.sort()
                dt, st = servers.pop(0)
                if dt > H:
                    if H >= warm:
                        area += n * (H - last)
                        busy_area += min(n, c) * (H - last)
                    last = H
                    t = H
                    break
                t = dt
                if t >= warm:
                    area += n * (t - last)
                    busy_area += min(n, c) * (t - last)
                last = t
                n -= 1
                if t >= warm:
                    dep_w += 1
                    wait_sum += (t - st)
                    wait_n += 1
                if next_arr < t:
                    continue
        if last < H and H >= warm:
            area += n * (H - last)
            busy_area += min(n, c) * (H - last)
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = (wait_sum / wait_n) if wait_n > 0 else 0.0
        bf = busy_area / (win * c) if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = (arr_w - blk_w) / arr_w if arr_w > 0 else 0.0
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
        tot_wait_n += wait_n
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / (tot_win * c) if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = tot_arr / (tot_win / 60.0) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = (tot_arr - tot_blk) / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
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
