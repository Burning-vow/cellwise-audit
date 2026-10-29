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
    tot_wait_n = 0
    tot_pw_num = 0
    tot_pw_den = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        areaN = areaB = 0.0
        wait_sum = 0.0
        wait_n = 0
        soj_sum = 0.0
        arr_w = dep_w = blk_w = 0
        pw_num = pw_den = 0
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
            areaN += n * (nt - t)
            areaB += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                        soj_sum += svc
                        pw_den += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        pw_den += 1
                        pw_num += 1
            else:
                servers.sort()
                fin = servers.pop(0)
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, svc = queue.pop(0)
                    w = t - at
                    if t >= warm:
                        wait_sum += w
                        wait_n += 1
                        soj_sum += w + svc
                    busy += 1
                    servers.append(t + svc)
        win = H - warm
        win_total += win
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_wait_n += wait_n
        tot_pw_num += pw_num
        tot_pw_den += pw_den
        Ls = areaN / H if H > 0 else 0.0
        Ws = soj_sum / wait_n if wait_n > 0 else 0.0
        bfs = areaB / (c * H) if H > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = pw_num / pw_den if pw_den > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)

    L = tot_areaN / (H * len(seeds)) if H > 0 else 0.0
    W = tot_soj / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_areaB / (c * H * len(seeds)) if H > 0 else 0.0
    busy_util = busy_frac
    p_wait = tot_pw_num / tot_pw_den if tot_pw_den > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = dep / (win_total / len(seeds)) if win_total > 0 else 0.0
    lam_eff = arr / (win_total / len(seeds)) if win_total > 0 else 0.0
    busy_occupied = busy_frac

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_total / len(seeds),
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'busy_occupied': busy_occupied, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
