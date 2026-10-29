import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 3.0
    mean_s = 0.1
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        pass

    scv = cv * cv
    p2 = 0.5 * (1.0 + math.sqrt(max(0.0, (scv - 1.0) / (scv + 1.0))))
    p1 = 1.0 - p2
    m1 = mean_s * (1.0 - math.sqrt(max(0.0, (scv - 1.0) / (scv + 1.0)))) if scv > 1 else mean_s
    m2 = mean_s * (1.0 + math.sqrt(max(0.0, (scv - 1.0) / (scv + 1.0)))) if scv > 1 else mean_s
    if scv <= 1.0:
        p1, p2, m1, m2 = 1.0, 0.0, mean_s, mean_s

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_n = tot_wait_sum = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        area = 0.0
        busy_t = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait_n = 0
        win_wait_sum = 0.0
        last = 0.0
        while True:
            if busy:
                dt = rem
                nxt = t + dt
                if nxt > H:
                    if t < H:
                        area += n * (H - t)
                        busy_t += (H - t)
                    t = H
                    break
                area += n * dt
                busy_t += dt
                t = nxt
                n -= 1
                if n > 0:
                    rem = arr_times.pop(0)
                else:
                    busy = False
                    rem = 0.0
                if t >= warm:
                    win_dep += 1
            else:
                dt = rng.expovariate(lam)
                nxt = t + dt
                if nxt > H:
                    if t < H:
                        area += n * (H - t)
                    t = H
                    break
                t = nxt
                n += 1
                if t >= warm:
                    win_arr += 1
                if rng.random() < p1:
                    s = rng.expovariate(1.0 / m1)
                else:
                    s = rng.expovariate(1.0 / m2)
                if not busy:
                    busy = True
                    rem = s
                else:
                    arr_times.append(s)
        win = H - warm
        tot_win += win
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += area
        tot_busy += busy_t
        Lv = area / win if win > 0 else 0.0
        Wv = (area / win) / lam if lam > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        per_L.append(Lv)
        per_W.append(Wv)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if win_arr > 0 else 0.0)

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = dep / (tot_win / len(seeds)) if tot_win > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'hour', 'win': tot_win / len(seeds) if seeds else 0.0,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam, 'p_loss': 0.0, 'p_wait': 1.0 if arr > 0 else 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
