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

    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    m1 = mean_s * p
    m2 = mean_s * (1.0 - p)
    if m1 <= 0: m1 = 1e-12
    if m2 <= 0: m2 = 1e-12

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
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
        queue = []
        arr_c = dep_c = blk_c = 0
        area = 0.0
        busy_t = 0.0
        wait_area = 0.0
        waiters = 0
        last = 0.0
        while True:
            if busy:
                dt = rem
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area += n * seg
                        busy_t += (1 if busy else 0) * seg
                        wait_area += len(queue) * seg
                    elif nt > warm:
                        seg2 = H - warm
                        area += n * seg2
                        busy_t += (1 if busy else 0) * seg2
                        wait_area += len(queue) * seg2
                break
            if t >= warm:
                area += n * (nt - t)
                busy_t += (1 if busy else 0) * (nt - t)
                wait_area += len(queue) * (nt - t)
            elif nt > warm:
                seg2 = nt - warm
                area += n * seg2
                busy_t += (1 if busy else 0) * seg2
                wait_area += len(queue) * seg2
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    if t >= warm:
                        dep_c += 1
                    if queue:
                        cust = queue.pop(0)
                        if t >= warm:
                            waiters += 1
                            wait_area += 0
                        busy = True
                        rem = cust[1]
                        n += 1
            else:
                s = m1 if rng.random() < p else m2
                if t >= warm:
                    arr_c += 1
                if busy:
                    queue.append((t, s))
                    n += 1
                else:
                    busy = True
                    rem = s
                    n += 1
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (wait_area / win) / lam if win > 0 else 0.0
        bf = busy_t / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = waiters / arr_c if arr_c > 0 else 0.0
        per_L.append(Ls); per_W.append(Ws); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot_arr += arr_c; tot_dep += dep_c; tot_blk += blk_c
        tot_area += area; tot_busy += busy_t
        tot_wait_area += wait_area; tot_waiters += waiters
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_wait_area / tot_win) / lam if tot_win > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / ns) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waiters / tot_arr if tot_arr > 0 else 0.0

    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "busy_util": busy_frac, "busy_occupied": busy_frac,
        "runtime_units": H, "seed_list": seeds, "seeds_used": ns,
        "time_unit": "hour", "win": tot_win / ns if ns else 0.0,
        "arr": arr, "dep": dep, "blk": blk,
        "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
