import argparse, json, math, random

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
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 0.01), 0.99)
    r1 = mean_s / (2.0 * p)
    r2 = mean_s / (2.0 * (1.0 - p))

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_n = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        cnt_n = 0.0
        arr = dep = blk = 0.0
        wsum = 0.0
        wcnt = 0.0
        while t < H:
            if not busy:
                dt = next_arr - t
                if dt < 0:
                    dt = 0.0
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                    cnt_n += dt
                t += dt
                if t >= H:
                    break
                if t >= next_arr:
                    n += 1
                    if t >= warm:
                        arr += 1
                    svc = r1 if rng.random() < p else r2
                    if not busy:
                        busy = True
                        rem = svc
                        if t >= warm:
                            wait_n += 1
                            wait_area += 0.0
                    else:
                        pass
                    next_arr = t + rng.expovariate(lam)
            else:
                dt = min(rem, next_arr - t, H - t)
                if dt < 0:
                    dt = 0.0
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                    cnt_n += dt
                t += dt
                rem -= dt
                if t >= H:
                    break
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep += 1
                    rem = 0.0
                if abs(t - next_arr) < 1e-12:
                    n += 1
                    if t >= warm:
                        arr += 1
                    svc = r1 if rng.random() < p else r2
                    if not busy:
                        busy = True
                        rem = svc
                        if t >= warm:
                            wait_n += 1
                    next_arr = t + rng.expovariate(lam)

        wlen = H - warm
        Ls = area / wlen if wlen > 0 else 0.0
        Ws = (Ls / (lam * wlen)) * wlen if False else 0.0
        dep_rate_s = dep / wlen if wlen > 0 else 0.0
        lam_eff_s = arr / wlen if wlen > 0 else 0.0
        Ws = (Ls / lam_eff_s) if lam_eff_s > 0 else 0.0
        bf = busy_area / wlen if wlen > 0 else 0.0
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
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_n += cnt_n
        win_total += wlen

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    win = win_total / ns
    dep_rate = (tot_dep / win_total) if win_total > 0 else 0.0
    lam_eff = (tot_arr / win_total) if win_total > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": bf,
        "busy_util": bf,
        "busy_occupied": bf,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": win,
        "arr": arr_avg,
        "dep": dep_avg,
        "blk": blk_avg,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": pl,
        "p_wait": pw,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
