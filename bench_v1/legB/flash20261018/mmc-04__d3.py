import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    c = 2
    lam = 10.0 / 60.0
    mu = 1.0 / 10.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_served = 0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        q = []
        servers = []
        areaN = areaB = 0.0
        wait_sum = soj_sum = 0.0
        served = 0
        arr = dep = blk = 0
        win_start = warm
        win_len = H - warm
        last = 0.0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    areaN += n * (H - t)
                    areaB += busy * (H - t)
                break
            if t >= win_start:
                areaN += n * (nt - t)
                areaB += busy * (nt - t)
            elif nt > win_start:
                areaN += n * (nt - win_start)
                areaB += busy * (nt - win_start)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= win_start:
                        soj_sum += svc
                        served += 1
                else:
                    q.append((t, svc))
                    if t >= win_start:
                        blk += 1
                n += 1
            else:
                busy -= 1
                servers.remove(min(servers))
                if t >= win_start:
                    dep += 1
                n -= 1
                while q and busy < c:
                    at, svc = q.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    if t >= win_start:
                        wait_sum += (t - at)
                        soj_sum += (t - at) + svc
                        served += 1
        L = areaN / win_len if win_len > 0 else 0.0
        bf = areaB / (c * win_len) if win_len > 0 else 0.0
        W = soj_sum / served if served > 0 else 0.0
        pw = blk / arr if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pw)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_served += served
        tot_win += win_len

    ns = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / (c * tot_win) if tot_win > 0 else 0.0
    W = tot_soj / tot_served if tot_served > 0 else 0.0
    p_wait = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = arr_avg / (tot_win / ns / 60.0) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_wait,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
