import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 3.0
    mean_s = 0.1
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p2 = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p2 = min(max(p2, 0.0), 1.0)
    m1 = mean_s * (1.0 - math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2)))) if var_s > mean_s**2 else mean_s
    m1 = max(m1, 1e-9)
    m2 = max(2.0 * mean_s - m1, 1e-9)

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

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr = dep = blk = 0
        area = busy_t = wait_area = wait_n = 0.0
        ncount = 0.0
        last = 0.0
        while t < H:
            if busy:
                dt = min(rem, H - t)
                if t >= warm:
                    area += n * dt
                    busy_t += dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep += 1
                continue
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt >= H:
                if t >= warm:
                    area += n * (H - t)
                t = H
                break
            if t >= warm:
                area += n * (nt - t)
            t = nt
            arr += 1
            n += 1
            if rng.random() < p2:
                s = rng.expovariate(1.0 / m2)
            else:
                s = rng.expovariate(1.0 / m1)
            if not busy:
                busy = True
                rem = s
                if t >= warm:
                    wait_n += 1
            else:
                if t >= warm:
                    wait_area += 0.0
                    wait_n += 1
        wlen = H - warm
        Ls = area / wlen if wlen > 0 else 0.0
        Ws = (Ls / lam) * 60.0 if lam > 0 else 0.0
        bfs = busy_t / wlen if wlen > 0 else 0.0
        pls = blk / arr if arr > 0 else 0.0
        pws = wait_n / arr if arr > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_wait_n += wait_n
        tot_n += arr
        win_total += wlen

    ns = len(seeds)
    L = tot_area / win_total if win_total > 0 else 0.0
    W = (L / lam) * 60.0 if lam > 0 else 0.0
    busy_frac = tot_busy / win_total if win_total > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = (tot_dep / win_total) * 60.0 if win_total > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0
    lam_eff = lam * (1.0 - p_loss)

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": "minute",
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": win_total / ns if ns > 0 else 0.0,
        "arr": arr_avg,
        "blk": blk_avg,
        "busy_util": busy_frac,
        "busy_occupied": busy_frac,
        "dep": dep_avg,
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
