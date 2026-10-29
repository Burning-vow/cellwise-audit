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
        cv *= 1.2

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
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        nxt = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr = dep = blk = 0
        win_arr = dep_w = 0
        while t < H:
            if not busy:
                dt = nxt - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += 0.0 * dt
                t += dt
                if t >= H:
                    break
                n += 1
                if t >= warm:
                    arr += 1
                if not busy:
                    busy = True
                    rem = rng.expovariate(r1) if rng.random() < p1 else rng.expovariate(r2)
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1.0
                nxt = t + rng.expovariate(lam)
            else:
                dt = min(rem, nxt - t)
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += 1.0 * dt
                t += dt
                rem -= dt
                if t >= H:
                    break
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep += 1
                else:
                    n += 1
                    if t >= warm:
                        arr += 1
                    if not busy:
                        busy = True
                        rem = rng.expovariate(r1) if rng.random() < p1 else rng.expovariate(r2)
                        if t >= warm:
                            wait_n += 1.0
                    nxt = t + rng.expovariate(lam)
        wlen = H - warm
        Ls = area / wlen if wlen > 0 else 0.0
        bf = busy_area / wlen if wlen > 0 else 0.0
        Ws = (Ls / (lam * bf)) if bf > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if arr > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += wlen

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    lam_eff = lam
    W = L / (lam_eff * busy_frac) if busy_frac > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) if tot_win > 0 else 0.0
    p_loss = blk_avg / arr_avg if arr_avg > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "hour",
        "win": tot_win / ns if ns > 0 else 0.0,
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
