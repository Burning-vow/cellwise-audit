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

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
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
        dep_times = []
        wait_times = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        n_arr = n_dep = n_blk = 0
        n_wait = 0
        last = 0.0
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                nt = t + dt
                if nt > H:
                    area += n * (H - t)
                    busy_area += (1 if busy else 0) * (H - t)
                    waiters_area += max(n - (1 if busy else 0), 0) * (H - t)
                    break
                area += n * (nt - t)
                busy_area += (1 if busy else 0) * (nt - t)
                waiters_area += max(n - (1 if busy else 0), 0) * (nt - t)
                t = nt
                n += 1
                n_arr += 1
                arr_times.append(t)
                if rng.random() < p:
                    s = rng.expovariate(1.0 / r1)
                else:
                    s = rng.expovariate(1.0 / r2)
                rem = s
                busy = True
                if n > 1:
                    n_wait += 1
                    wait_times.append(t)
            else:
                nt = t + rem
                if nt > H:
                    area += n * (H - t)
                    busy_area += (H - t)
                    waiters_area += max(n - 1, 0) * (H - t)
                    break
                area += n * (nt - t)
                busy_area += (nt - t)
                waiters_area += max(n - 1, 0) * (nt - t)
                t = nt
                n -= 1
                n_dep += 1
                dep_times.append(t)
                if n > 0:
                    if rng.random() < p:
                        s = rng.expovariate(1.0 / r1)
                    else:
                        s = rng.expovariate(1.0 / r2)
                    rem = s
                    busy = True
                else:
                    busy = False
                    rem = 0.0

        win = H - warm
        if win <= 0:
            win = H
            warm_eff = 0.0
        else:
            warm_eff = warm

        def in_win(x):
            return x >= warm_eff

        arr_w = sum(1 for x in arr_times if in_win(x))
        dep_w = sum(1 for x in dep_times if in_win(x))
        blk_w = 0
        wait_w = sum(1 for x in wait_times if in_win(x))

        L = area / H if H > 0 else 0.0
        W = (area / max(n_dep, 1)) if n_dep > 0 else 0.0
        bf = busy_area / H if H > 0 else 0.0
        pl = blk_w / max(arr_w, 1)
        pw = wait_w / max(arr_w, 1)

        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)

        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_waiters += waiters_area
        tot_win += win

    ns = len(seeds)
    L = tot_area / (H * ns) if H > 0 else 0.0
    W = (tot_area / max(tot_dep, 1)) if tot_dep > 0 else 0.0
    busy_frac = tot_busy / (H * ns) if H > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / ns) / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0
    p_loss = tot_blk / max(tot_arr, 1)
    p_wait = sum(per_pw) / ns

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "hour",
        "win": tot_win / ns,
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
