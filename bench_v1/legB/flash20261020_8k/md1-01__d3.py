import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = 4.0 * 1.25
    elif a.pert == 'mu_up':
        mu = 10.0 * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_wait_n = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area = 0.0
        busy_area = 0.0
        win_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                break
            if t >= warm:
                area += n * (nt - t)
                busy_area += busy * (nt - t)
                win_area += (nt - t)
            t = nt
            if t >= warm:
                arr += 1
            if n < c:
                n += 1
                busy = 1
                svc = 1.0 / mu
                queue.append((t + svc, t))
            else:
                blk += 1
                if t >= warm:
                    pass
        while queue:
            d, at = queue.pop(0)
            if d > H:
                if t < H:
                    if t >= warm:
                        area += n * (H - t)
                        busy_area += busy * (H - t)
                        win_area += (H - t)
                break
            if d >= warm:
                area += n * (d - t) if d > t else 0.0
                busy_area += busy * (d - t) if d > t else 0.0
                win_area += (d - t) if d > t else 0.0
            t = d
            n -= 1
            busy = 1 if n >= c else 0
            if d >= warm:
                dep += 1
                wait_sum += (d - at - 1.0 / mu)
                wait_n += 1
        if t < H:
            if t < warm:
                t = warm
            if t < H:
                area += n * (H - t)
                busy_area += busy * (H - t)
                win_area += (H - t)
        w = win_area if win_area > 0 else 1e-9
        Ls = area / w
        Ws = Ls / (lam * (1 - blk / max(arr + blk, 1))) if (arr + blk) > 0 else 0.0
        if wait_n > 0:
            Ws = wait_sum / wait_n + 1.0 / mu
        bf = busy_area / w
        pl = blk / max(arr + blk, 1)
        pw = wait_n / max(dep, 1)
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
        tot_win += w
        tot_wait += wait_sum
        tot_wait_n += wait_n

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_wait / tot_wait_n + 1.0 / mu) if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = lam * (1 - (tot_blk / max(tot_arr + tot_blk, 1)))
    p_loss = tot_blk / max(tot_arr + tot_blk, 1)
    p_wait = tot_wait_n / max(tot_dep, 1)

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_frac / c,
        "busy_occupied": busy_frac,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": tot_win / ns if ns > 0 else 0.0,
        "arr": arr_avg,
        "dep": dep_avg,
        "blk": blk_avg,
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
