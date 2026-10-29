import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep_n = 0
    tot_arr_n = 0
    tot_wait_n = 0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        areaN = 0.0
        areaB = 0.0
        wait_sum = 0.0
        soj_sum = 0.0
        dep_n = 0
        arr_n = 0
        blk_n = 0
        wait_n = 0
        win_start = warm
        win_len = H - warm
        last = 0.0
        next_arr = rng.expovariate(lam)
        while t < H:
            if next_arr <= t:
                pass
            cand = next_arr
            if servers:
                cand = min(cand, min(servers))
            if cand > H:
                dt = H - t
                if t >= win_start:
                    areaN += n * dt
                    areaB += busy * dt
                t = H
                break
            dt = cand - t
            if t >= win_start:
                areaN += n * dt
                areaB += busy * dt
            t = cand
            if t >= next_arr:
                arr_n += 1
                n += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= win_start:
                        wait_n += 1
                        wait_sum += 0.0
                        soj_sum += svc
                else:
                    queue.append((t, svc))
                next_arr = t + rng.expovariate(lam)
            else:
                servers.sort()
                fin = servers.pop(0)
                busy -= 1
                dep_n += 1
                if queue:
                    at, svc = queue.pop(0)
                    w = t - at
                    if t >= win_start:
                        wait_n += 1
                        wait_sum += w
                        soj_sum += w + svc
                    busy += 1
                    servers.append(t + svc)
        if win_len <= 0:
            win_len = 1e-9
        L = areaN / win_len
        W = (soj_sum / wait_n) if wait_n > 0 else 0.0
        bf = areaB / win_len / c
        pw = (wait_n / arr_n) if arr_n > 0 else 0.0
        pl = (blk_n / arr_n) if arr_n > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_n += dep_n
        tot_arr_n += arr_n
        tot_blk += blk_n
        tot_wait_n += wait_n
        tot_win += win_len

    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = tot_soj / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_areaB / tot_win / c if tot_win > 0 else 0.0
    p_wait = tot_wait_n / tot_arr_n if tot_arr_n > 0 else 0.0
    p_loss = tot_blk / tot_arr_n if tot_arr_n > 0 else 0.0
    arr = tot_arr_n / len(seeds)
    dep = tot_dep_n / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = dep / (tot_win / len(seeds)) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / len(seeds)) if tot_win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': tot_win / len(seeds),
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
