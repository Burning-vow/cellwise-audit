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
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    cs2 = cv * cv
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (cs2 - 1.0) / (cs2 + 1.0))))
    r1 = 2.0 * p * mean_s
    r2 = 2.0 * (1.0 - p) * mean_s

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = t + rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr_c = dep_c = blk_c = 0
        last = 0.0
        while True:
            nxt = arr_t
            if busy and t + rem < nxt:
                nxt = t + rem
            if nxt > H:
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                t = H
                break
            dt = nxt - t
            if t >= warm:
                area += n * dt
                busy_area += (1 if busy else 0) * dt
            t = nxt
            if busy and abs(t - (last + rem)) < 1e-12 and nxt == last + rem:
                pass
            if busy and t >= last + rem - 1e-12 and (not (arr_t < t - 1e-12)):
                busy = False
                n -= 1
                dep_c += 1
                if n > 0:
                    rem = rng.choice([r1, r2]) if False else 0.0
                continue
            if busy and t >= last + rem - 1e-12:
                busy = False
                n -= 1
                dep_c += 1
                if n > 0:
                    pass
                continue
            if abs(t - arr_t) < 1e-12:
                arr_c += 1
                svc = r1 if rng.random() < p else r2
                if busy:
                    n += 1
                    if t >= warm:
                        wait_n += 1
                else:
                    busy = True
                    n += 1
                    last = t
                    rem = svc
                arr_t = t + rng.expovariate(lam)
                continue
        win = H - warm
        tot_win += win
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        per_L.append(area / win if win > 0 else 0.0)
        per_W.append(area / max(1e-12, dep_c) if dep_c > 0 else 0.0)
        per_bf.append(busy_area / win if win > 0 else 0.0)
        per_pl.append(0.0)
        per_pw.append(wait_n / max(1e-12, arr_c) if arr_c > 0 else 0.0)

    W = tot_area / max(1e-12, tot_dep)
    L = tot_area / max(1e-12, tot_win)
    bf = tot_busy / max(1e-12, tot_win)
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': tot_win / len(seeds),
        'arr': tot_arr / len(seeds),
        'blk': tot_blk / len(seeds),
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': tot_dep / len(seeds),
        'dep_rate': (tot_dep / len(seeds)) / max(1e-12, tot_win / len(seeds)),
        'lam_eff': lam,
        'p_loss': 0.0,
        'p_wait': tot_wait_n / max(1e-12, tot_arr),
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
