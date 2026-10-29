import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_waited = 0.0
    tot_dep_win = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        servers = []
        queue = []
        areaN = 0.0
        areaB = 0.0
        arr_w = dep_w = blk_w = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_cnt_w = 0
        last = 0.0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                dt = H - t
                nt = H
            areaN += n * dt
            areaB += busy * dt
            t = nt
            if t >= H:
                break
            if rng.random() < lam / rate:
                arr_w += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    if busy < c:
                        busy += 1
                        servers.append((t + svc, svc))
                    else:
                        queue.append((t, svc))
                else:
                    blk_w += 1
            else:
                busy -= 1
                dep_w += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append((t + svc, svc))
                    wait_sum += t - at
                    waited_cnt += 1
                n -= 1
        # recompute window stats properly: we integrated over whole horizon; approximate window by scaling
        # Better: redo with window tracking
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        areaN = 0.0
        areaB = 0.0
        arr_w = dep_w = blk_w = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = H - t
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                dt = H - t
                nt = H
            if t >= warm:
                areaN += n * dt
                areaB += busy * dt
            t = nt
            if t >= H:
                break
            if rng.random() < lam / rate:
                if t >= warm:
                    arr_w += 1
                if n < cap:
                    n += 1
                    svc = rng.expovariate(mu)
                    if busy < c:
                        busy += 1
                        servers.append((t + svc, svc))
                    else:
                        queue.append((t, svc))
                else:
                    if t >= warm:
                        blk_w += 1
            else:
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append((t + svc, svc))
                    if t >= warm:
                        wait_sum += t - at
                        waited_cnt += 1
                n -= 1
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        bf = areaB / (c * win) if win > 0 else 0.0
        occ = areaB / win if win > 0 else 0.0
        W = wait_sum / waited_cnt if waited_cnt > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waited_cnt / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(occ)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_waited += waited_cnt
        win_total += win

    ns = len(seeds)
    L = tot_areaN / win_total if win_total > 0 else 0.0
    busy_frac = tot_areaB / win_total if win_total > 0 else 0.0
    busy_util = busy_frac / c
    W = tot_wait / tot_waited if tot_waited > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep / win_total if win_total > 0 else 0.0
    lam_eff = arr / (win_total / ns) if win_total > 0 else 0.0

    out = {
        "L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
        "runtime_units": H, "seed_list": seeds, "seeds_used": ns,
        "time_unit": "minute", "win": win_total / ns,
        "arr": arr, "blk": blk, "busy_util": busy_util,
        "busy_occupied": busy_frac, "dep": dep, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
