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
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    r1 = 1.0 / (2.0 * p * mean_s)
    r2 = 1.0 / (2.0 * (1.0 - p) * mean_s)

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = tot_area = tot_busy = 0.0
    tot_wait = tot_waitn = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr = dep = blk = 0.0
        area = busy_t = 0.0
        wait_sum = wait_n = 0.0
        last = 0.0
        while True:
            rate = lam if not busy else lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if busy:
                if nt >= t + rem:
                    nt = t + rem
                    dt = rem
            if nt > H:
                if busy:
                    seg = H - t
                    area += n * seg
                    busy_t += seg
                break
            area += n * dt
            if busy:
                busy_t += dt
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    rem = 0.0
                    if t >= warm:
                        dep += 1
                    if n > 0:
                        pass
            else:
                arr += 1
                if t >= warm:
                    pass
                s = rng.expovariate(r1) if rng.random() < p else rng.expovariate(r2)
                if n == 0:
                    busy = True
                    rem = s
                    n = 1
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                else:
                    n += 1
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
            if not busy and n > 0:
                busy = True
                rem = rng.expovariate(r1) if rng.random() < p else rng.expovariate(r2)
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = Ls / lam if lam > 0 else 0.0
        bfs = busy_t / win if win > 0 else 0.0
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
        tot_wait += wait_sum
        tot_waitn += wait_n
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (tot_win / ns) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waitn / tot_arr if tot_arr > 0 else 0.0
    lam_eff = dep_rate

    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "runtime_units": H, "seed_list": seeds, "seeds_used": ns,
        "time_unit": "hour", "win": tot_win / ns if ns > 0 else 0.0,
        "arr": arr_avg, "blk": blk_avg, "busy_util": busy_frac,
        "busy_occupied": busy_frac, "dep": dep_avg, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
