import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
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
    tot_n = 0
    tot_waiters = 0
    tot_arr_win = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        areaN = areaB = 0.0
        wait_sum = 0.0
        soj_sum = 0.0
        cnt = 0
        waiters = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        last = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                nt = t + dt
            else:
                dt = rng.expovariate(lam + busy * mu)
                nt = t + dt
            if nt > H:
                areaN += n * (H - t)
                areaB += busy * (H - t)
                break
            areaN += n * (nt - t)
            areaB += busy * (nt - t)
            t = nt
            if rng.random() < lam / (lam + busy * mu):
                svc = rng.expovariate(mu)
                n += 1
                if t >= warm:
                    arr_win += 1
                if busy < c:
                    busy += 1
                    servers.append((t + svc, svc))
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        waiters += 1
            else:
                busy -= 1
                servers.sort()
                servers.pop(0)
                if t >= warm:
                    dep_win += 1
                if queue:
                    at, svc = queue.pop(0)
                    if t >= warm:
                        wait_sum += (t - at)
                        soj_sum += (t - at) + svc
                        cnt += 1
                    busy += 1
                    servers.append((t + svc, svc))
        wl = H - warm
        Ls = areaN / H
        bf = areaB / (H * c)
        Ws = (soj_sum / cnt) if cnt > 0 else 0.0
        pw = (waiters / arr_win) if arr_win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += blk_win
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_n += cnt
        tot_waiters += waiters
        tot_arr_win += arr_win
        win_total += wl

    ns = len(seeds)
    L = tot_areaN / (H * ns)
    busy_frac = tot_areaB / (H * c * ns)
    W = (tot_soj / tot_n) if tot_n > 0 else 0.0
    p_wait = (tot_waiters / tot_arr_win) if tot_arr_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = H - warm
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
