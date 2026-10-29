import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    service_time = 6.0

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy_area = 0.0
    tot_wait_area = 0.0
    tot_waiters = 0.0
    tot_win = 0.0
    tot_busy_util = 0.0
    tot_busy_occ = 0.0
    tot_dep_rate = 0.0
    tot_lam_eff = 0.0

    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy_until = 0.0
        queue = []
        arr = dep = blk = 0
        area = busy_area = wait_area = 0.0
        waiters = 0.0
        win = 0.0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                break
            if t >= warm:
                area += n * (nt - t)
                busy_area += (1 if n >= 1 else 0) * (nt - t)
                wait_area += len(queue) * (nt - t)
                win += nt - t
            t = nt
            arr += 1
            svc = service_time
            if n < c:
                n += 1
                busy_until = t + svc
                if t >= warm:
                    waiters += 0
            else:
                blk += 1
                queue.append(svc)
            if t >= warm:
                pass
            # process departures
            while n > 0 and busy_until <= t:
                n -= 1
                dep += 1
                if queue:
                    svc2 = queue.pop(0)
                    n += 1
                    busy_until = t + svc2
                else:
                    busy_until = float('inf')
        # final window
        if t < H:
            if t >= warm:
                area += n * (H - t)
                busy_area += (1 if n >= 1 else 0) * (H - t)
                wait_area += len(queue) * (H - t)
                win += H - t
        # flush remaining departures within horizon
        while n > 0 and busy_until <= H:
            dep += 1
            n -= 1
            if queue:
                svc2 = queue.pop(0)
                n += 1
                busy_until = busy_until + svc2
            else:
                busy_until = float('inf')
        if win <= 0:
            win = 1e-9
        L = area / win
        W = wait_area / max(1, arr) if arr > 0 else 0.0
        bf = busy_area / win
        pl = blk / max(1, arr)
        pw = 1.0 - (1.0 - pl) if arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy_area += busy_area
        tot_wait_area += wait_area
        tot_waiters += waiters
        tot_win += win
        tot_busy_util += bf
        tot_busy_occ += bf
        tot_dep_rate += dep / (win / 60.0) if win > 0 else 0.0
        tot_lam_eff += (arr - blk) / (win / 60.0) if win > 0 else 0.0

    ns = a.seeds
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / max(1, tot_arr) if tot_arr > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac / c
    busy_occ = busy_frac
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = tot_dep_rate / ns
    lam_eff = tot_lam_eff / ns
    p_loss = tot_blk / max(1, tot_arr)
    p_wait = 1.0 - (1.0 - p_loss) if tot_arr > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": "minute",
        "seed_list": [a.seed_start + i for i in range(ns)],
        "seeds_used": ns,
        "time_unit": "minute",
        "win": tot_win / ns,
        "arr": arr_avg,
        "blk": blk_avg,
        "busy_util": busy_util,
        "busy_occupied": busy_occ,
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
