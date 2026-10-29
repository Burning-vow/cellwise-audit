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
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_areaN = 0.0
        win_areaB = 0.0
        win_wait = 0.0
        win_soj = 0.0
        win_wait_n = 0
        win_dep_n = 0
        win_start = warm
        win_end = H
        next_arr = rng.expovariate(lam)
        events = []
        while True:
            if next_arr <= t:
                pass
            nxt = next_arr
            if servers:
                nxt = min(nxt, min(servers))
            if nxt > H:
                break
            dt = nxt - t
            if t >= win_start:
                areaN += n * dt
                areaB += busy * dt
            t = nxt
            if t >= win_start:
                win_areaN += n * dt
                win_areaB += busy * dt
            if t == next_arr:
                arr_n += 1
                if t >= win_start:
                    win_arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    soj_sum += svc
                    if t >= win_start:
                        win_soj += svc
                else:
                    queue.append((t, svc))
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                servers.sort()
                servers.pop(0)
                busy -= 1
                n -= 1
                dep_n += 1
                if t >= win_start:
                    win_dep += 1
                if queue:
                    at, svc = queue.pop(0)
                    w = t - at
                    wait_sum += w
                    wait_n += 1
                    if t >= win_start:
                        win_wait += w
                        win_wait_n += 1
                    busy += 1
                    servers.append(t + svc)
                    soj_sum += svc
                    if t >= win_start:
                        win_soj += svc
                    n += 1
        win_len = win_end - win_start
        L = win_areaN / win_len if win_len > 0 else 0.0
        bf = win_areaB / (c * win_len) if win_len > 0 else 0.0
        W = (win_wait + win_soj) / win_dep if win_dep > 0 else 0.0
        pw = win_wait_n / win_arr if win_arr > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_areaN += win_areaN
        tot_areaB += win_areaB
        tot_wait += win_wait
        tot_soj += win_soj
        tot_dep_n += win_dep
        tot_arr_n += win_arr
        tot_wait_n += win_wait_n
        tot_win += win_len

    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    W = (tot_wait + tot_soj) / tot_dep_n if tot_dep_n > 0 else 0.0
    p_wait = tot_wait_n / tot_arr_n if tot_arr_n > 0 else 0.0
    p_loss = 0.0
    arr_rate = tot_arr_n / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep_n / tot_win if tot_win > 0 else 0.0
    lam_eff = arr_rate
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': tot_win / len(seeds) if seeds else 0.0,
        'arr': tot_arr_n / len(seeds) if seeds else 0.0,
        'dep': tot_dep_n / len(seeds) if seeds else 0.0,
        'blk': 0.0,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep_rate': dep_rate * 60.0,
        'lam_eff': lam_eff * 60.0,
        'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
