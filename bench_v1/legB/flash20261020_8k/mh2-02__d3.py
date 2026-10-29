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
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    r1 = 2.0 * p * mean_s
    r2 = 2.0 * (1.0 - p) * mean_s

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = tot_waitn = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        nxt = rng.expovariate(lam)
        area = 0.0
        busy_t = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while True:
            if not busy:
                dt = nxt - t
                if t + dt > H:
                    if t < H:
                        area += n * (H - t)
                        busy_t += (H - t) if busy else 0.0
                    break
                area += n * dt
                t = nxt
                arr += 1
                n += 1
                s = r1 if rng.random() < p else r2
                if not busy:
                    busy = True
                    rem = s
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                else:
                    pass
                nxt = t + rng.expovariate(lam)
            else:
                dt = min(rem, nxt - t)
                if t + dt > H:
                    area += n * (H - t)
                    busy_t += (H - t)
                    break
                area += n * dt
                busy_t += dt
                t += dt
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep += 1
                    if nxt - t < 1e-12:
                        pass
                if abs(nxt - t) < 1e-12:
                    arr += 1
                    n += 1
                    s = r1 if rng.random() < p else r2
                    if not busy:
                        busy = True
                        rem = s
                    nxt = t + rng.expovariate(lam)
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        W = L / (lam * (1.0 - 0.0)) if lam > 0 else 0.0
        W = L / lam if lam > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(1.0 if bf > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = lam
    p_loss = 0.0
    p_wait = 1.0 if busy_frac > 0 else 0.0

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
