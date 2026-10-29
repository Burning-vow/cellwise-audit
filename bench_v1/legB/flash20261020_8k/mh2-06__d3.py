import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0 / 60.0
    mean_s = 6.0
    cv = 3.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        pass

    var_s = (cv * mean_s) ** 2
    p1 = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    m1 = mean_s * p1
    m2 = mean_s * (1.0 - p1) if p1 < 1.0 else mean_s
    if p1 >= 1.0:
        p1 = 1.0
        m1 = mean_s
        m2 = mean_s

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
    tot_waiters = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_t = 0.0
        wait_area = 0.0
        arr_c = dep_c = blk_c = 0
        wait_c = 0
        while t < H:
            if not busy:
                dt = next_arr - t
                if t + dt > H:
                    dt = H - t
                area += n * dt
                t += dt
                if t >= H:
                    break
                n += 1
                arr_c += 1
                if n == 1:
                    busy = True
                    u = rng.random()
                    rem = m1 if u < p1 else m2
                    busy_t += 0.0
                next_arr = t + rng.expovariate(lam)
            else:
                dt = min(rem, next_arr - t, H - t)
                area += n * dt
                if n >= 1:
                    busy_t += dt
                if n >= 2:
                    wait_area += (n - 1) * dt
                t += dt
                rem -= dt
                if t >= H:
                    break
                if rem <= 1e-12:
                    n -= 1
                    dep_c += 1
                    if n >= 1:
                        u = rng.random()
                        rem = m1 if u < p1 else m2
                    else:
                        busy = False
                        rem = 0.0
                if abs(t - next_arr) < 1e-12:
                    n += 1
                    arr_c += 1
                    next_arr = t + rng.expovariate(lam)
        win = H - warm
        if win <= 0:
            win = H
        Lv = area / H if H > 0 else 0.0
        Wv = (wait_area / max(1e-12, dep_c)) if dep_c > 0 else 0.0
        bf = busy_t / H if H > 0 else 0.0
        pl = blk_c / max(1, arr_c)
        pw = wait_c / max(1, arr_c)
        per_L.append(Lv)
        per_W.append(Wv)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_t
        tot_wait_area += wait_area
        tot_win += H

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'runtime_units': tot_win,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': tot_win / ns,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
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
