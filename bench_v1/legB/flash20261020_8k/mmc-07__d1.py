import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
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
    tot_pw_num = 0
    tot_arr_n = 0
    win_total = 0.0

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
        pw_num = 0
        win = 0.0
        last = 0.0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                areaN += n * dt
                areaB += busy * dt
                win += dt
            t = nt
            if t >= H:
                break
            if rng.random() < lam / rate:
                arr_n += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append((t + svc, svc))
                    if t >= warm:
                        soj_sum += svc
                        dep_n += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        pw_num += 1
            else:
                servers.sort()
                endt, svc = servers.pop(0)
                busy -= 1
                if queue:
                    at, qsvc = queue.pop(0)
                    if t >= warm:
                        wait_sum += (t - at)
                        soj_sum += (t - at) + qsvc
                        dep_n += 1
                    busy += 1
                    servers.append((t + qsvc, qsvc))
        # drain remaining at end not counted beyond H
        Ls = areaN / win if win > 0 else 0.0
        Ws = (wait_sum + soj_sum) / dep_n if dep_n > 0 else 0.0
        bfs = areaB / (c * win) if win > 0 else 0.0
        pls = blk_n / arr_n if arr_n > 0 else 0.0
        pws = pw_num / arr_n if arr_n > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_n
        tot_dep += dep_n
        tot_blk += blk_n
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_n += dep_n
        tot_pw_num += pw_num
        tot_arr_n += arr_n
        win_total += win

    ns = len(seeds)
    L = tot_areaN / win_total if win_total > 0 else 0.0
    W = (tot_wait + tot_soj) / tot_dep_n if tot_dep_n > 0 else 0.0
    busy_frac = tot_areaB / (c * win_total) if win_total > 0 else 0.0
    p_wait = tot_pw_num / tot_arr_n if tot_arr_n > 0 else 0.0
    p_loss = tot_blk / tot_arr_n if tot_arr_n > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep / win_total if win_total > 0 else 0.0
    lam_eff = arr_avg / (win_total / ns) if win_total > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win_total / ns if ns > 0 else 0.0,
        'arr': arr_avg, 'blk': blk_avg, 'busy_util': busy_frac,
        'busy_occupied': 1.0 - (1.0 - busy_frac) if False else busy_frac,
        'dep': dep_avg, 'dep_rate': dep_rate, 'lam_eff': lam_eff,
        'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
