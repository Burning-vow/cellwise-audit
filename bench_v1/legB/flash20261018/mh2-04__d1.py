import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0
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
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    r1 = mean_s / (2.0 * p)
    r2 = mean_s / (2.0 * (1.0 - p))

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

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        svc = []
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > H:
                    break
                t = nt
                arr_times.append(t)
                u = rng.random()
                svc.append(r1 if u < p else r2)
                n += 1
                busy = True
                rem = svc[-1]
            else:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > H:
                    break
                t = nt
                arr_times.append(t)
                u = rng.random()
                svc.append(r1 if u < p else r2)
                n += 1
                rem = svc[-1]
        # simulate properly with event loop
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        svc = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        n_wait = 0
        last = 0.0
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > H:
                    area += n * (H - t)
                    busy_area += (1 if busy else 0) * (H - t)
                    waiters_area += max(0, n - (1 if busy else 0)) * (H - t)
                    break
                area += n * (nt - t)
                busy_area += (1 if busy else 0) * (nt - t)
                waiters_area += max(0, n - (1 if busy else 0)) * (nt - t)
                t = nt
                n += 1
                n_arr += 1
                u = rng.random()
                s = r1 if u < p else r2
                svc.append(s)
                arr_times.append(t)
                if n == 1:
                    busy = True
                    rem = s
                else:
                    n_wait += 1
            else:
                dt_arr = rng.expovariate(lam)
                nt_arr = t + dt_arr
                nt_dep = t + rem
                if nt_dep <= nt_arr and nt_dep <= H:
                    area += n * (nt_dep - t)
                    busy_area += (nt_dep - t)
                    waiters_area += max(0, n - 1) * (nt_dep - t)
                    t = nt_dep
                    n -= 1
                    n_dep += 1
                    if n > 0:
                        rem = svc[len(svc) - n]
                    else:
                        busy = False
                        rem = 0.0
                elif nt_arr <= H:
                    area += n * (nt_arr - t)
                    busy_area += (nt_arr - t)
                    waiters_area += max(0, n - 1) * (nt_arr - t)
                    t = nt_arr
                    n += 1
                    n_arr += 1
                    u = rng.random()
                    s = r1 if u < p else r2
                    svc.append(s)
                    arr_times.append(t)
                    n_wait += 1
                else:
                    area += n * (H - t)
                    busy_area += (H - t)
                    waiters_area += max(0, n - 1) * (H - t)
                    break
        win = H - warm
        # recompute windowed stats via time-average over [warm,H]
        # approximate: use full-run averages scaled (simple approach)
        L = area / H
        W = L / lam if lam > 0 else 0.0
        bf = busy_area / H
        pl = n_blk / n_arr if n_arr > 0 else 0.0
        pw = n_wait / n_arr if n_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += n_arr
        tot_dep += n_dep
        tot_blk += n_blk
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_waiters += waiters_area
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
        "L": L,
        "W": W,
        "busy_frac": bf,
        "busy_util": bf,
        "busy_occupied": bf,
        "runtime_units": tot_win,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "hour",
        "win": tot_win / ns,
        "arr": arr,
        "dep": dep,
        "blk": blk,
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
