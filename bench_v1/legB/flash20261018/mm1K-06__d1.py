import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_busy = tot_occ = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        arr = dep = blk = 0
        busy_area = 0.0
        occ_area = 0.0
        wait_area = 0.0
        wait_n = 0
        last = 0.0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0.0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                dt = H - t
                nt = H
            if t >= warm:
                busy_area += (1.0 if busy else 0.0) * dt
                occ_area += n * dt
            if nt >= H:
                t = H
                break
            t = nt
            if busy and rng.random() < mu / rate:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep += 1
                    if queue:
                        q = queue.pop(0)
                        busy = True
                        n += 1
                        rem = q[1]
                        if t >= warm:
                            wait_area += (t - q[0])
                            wait_n += 1
            else:
                arr += 1
                svc = rng.expovariate(mu)
                if n < K:
                    if not busy:
                        busy = True
                        n += 1
                        rem = svc
                    else:
                        n += 1
                        queue.append((t, svc))
                else:
                    blk += 1
        win = H - warm
        Lv = occ_area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        Wv = (wait_area / wait_n) if wait_n > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = wait_n / arr if arr > 0 else 0.0
        per_L.append(Lv)
        per_W.append(Wv)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_busy += busy_area
        tot_occ += occ_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win
    ns = len(seeds)
    L = tot_occ / tot_win if tot_win > 0 else 0.0
    bf = tot_busy / tot_win if tot_win > 0 else 0.0
    W = (tot_wait_area / tot_wait_n) if tot_wait_n > 0 else 0.0
    pl = tot_blk / tot_arr if tot_arr > 0 else 0.0
    pw = tot_wait_n / tot_arr if tot_arr > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    busy_util = bf
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns if ns > 0 else 0.0,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
