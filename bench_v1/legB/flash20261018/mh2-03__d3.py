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

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 0.01), 0.99)
    m1 = mean_s * p
    m2 = mean_s * (1.0 - p)
    if m1 <= 0: m1 = mean_s * 0.5
    if m2 <= 0: m2 = mean_s * 0.5

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
    win_total = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_c = dep_c = blk_c = 0
        wsum = 0.0
        wcount = 0
        while t < H:
            if not busy:
                dt = next_arr - t
                if dt < 0: dt = 0.0
                if t + dt > H:
                    if t >= warm:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                t += dt
                n += 1
                if t >= warm:
                    arr_c += 1
                s = m1 if rng.random() < p else m2
                if not busy:
                    busy = True
                    rem = s
                    if t >= warm:
                        wait_n += 1
                        wait_area += 0.0
                next_arr = t + rng.expovariate(lam)
            else:
                dt = min(rem, next_arr - t)
                if dt < 0: dt = 0.0
                if t + dt > H:
                    if t >= warm:
                        area += n * (H - t)
                        busy_area += (H - t)
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep_c += 1
                    if next_arr <= t:
                        n += 1
                        if t >= warm:
                            arr_c += 1
                        s = m1 if rng.random() < p else m2
                        busy = True
                        rem = s
                        if t >= warm:
                            wait_n += 1
                        next_arr = t + rng.expovariate(lam)
        win = H - warm
        if win <= 0: win = H
        Lv = area / win
        bf = busy_area / win
        Wv = Lv / lam if lam > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / arr_c if arr_c > 0 else 0.0
        per_L.append(Lv)
        per_W.append(Wv)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        win_total += win

    ns = len(seeds)
    win_avg = win_total / ns if ns else 0.0
    L = tot_area / win_total if win_total > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / win_total if win_total > 0 else 0.0
    arr = tot_arr / ns if ns else 0.0
    dep = tot_dep / ns if ns else 0.0
    blk = tot_blk / ns if ns else 0.0
    dep_rate = dep / win_avg * 60.0 if win_avg > 0 else 0.0
    lam_eff = arr / win_avg * 60.0 if win_avg > 0 else 0.0
    p_loss = blk / arr if arr > 0 else 0.0
    p_wait = (tot_wait_n / ns) / arr if arr > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_frac,
        "busy_occupied": busy_frac,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": win_avg,
        "arr": arr,
        "dep": dep,
        "blk": blk,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
