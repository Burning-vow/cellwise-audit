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
    r1 = 2.0 * p1 / mean_s
    r2 = 2.0 * p2 / mean_s

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
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr = 0
        dep = 0
        blk = 0
        area = 0.0
        busy_t = 0.0
        wait_area = 0.0
        wait_n = 0
        last = 0.0
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > H:
                    if t < H:
                        area += n * (H - t)
                        if busy:
                            busy_t += H - t
                    break
                area += n * (nt - t)
                if busy:
                    busy_t += nt - t
                t = nt
                arr += 1
                if rng.random() < p1:
                    s = rng.expovariate(r1)
                else:
                    s = rng.expovariate(r2)
                n += 1
                busy = True
                rem = s
                if t >= warm:
                    wait_n += 1
            else:
                nt = t + rem
                if nt > H:
                    area += n * (H - t)
                    busy_t += H - t
                    t = H
                    break
                area += n * (nt - t)
                busy_t += nt - t
                t = nt
                n -= 1
                dep += 1
                rem = 0.0
                busy = False
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (busy_t / win) / (dep / win) if dep > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = wait_n / arr if arr > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_win += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    win_avg = tot_win / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    p_wait = sum(per_pw) / ns

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win_avg,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
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
