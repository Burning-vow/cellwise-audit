import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_area = tot_dep = tot_arr = tot_blk = tot_busy = tot_win = 0.0
    tot_wait = tot_waited = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        server_free = 0.0
        area = 0.0
        last = 0.0
        arr = dep = blk = 0
        busy_area = 0.0
        wait_sum = 0.0
        waited = 0
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait = 0.0
        win_waited = 0
        win_start = warm
        win_len = H - warm
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                break
            area += n * (nt - t)
            busy_area += busy * (nt - t)
            if nt >= win_start:
                win_area += n * (nt - t)
                win_busy += busy * (nt - t)
            t = nt
            arr += 1
            if nt >= win_start:
                win_arr += 1
            svc = 1.0 / mu
            if busy < c:
                busy += 1
                queue.append((nt, svc))
            else:
                blk += 1
                if nt >= win_start:
                    win_blk += 1
            while queue and busy > 0:
                st, sv = queue[0]
                if st + sv <= t:
                    queue.pop(0)
                    busy -= 1
                    dep += 1
                    w = st + sv - st
                    if st >= win_start:
                        win_dep += 1
                        win_wait += (st - st)
                        win_waited += 1
                else:
                    break
        area += n * (H - t)
        busy_area += busy * (H - t)
        if H >= win_start:
            win_area += n * (H - t)
            win_busy += busy * (H - t)
        L = area / H
        W = L / (lam * (1 - 0.0)) if lam > 0 else 0.0
        bf = busy_area / H / c
        pl = blk / arr if arr > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_area += win_area
        tot_dep += win_dep
        tot_arr += win_arr
        tot_blk += win_blk
        tot_busy += win_busy
        tot_win += win_len
        tot_wait += win_wait
        tot_waited += win_waited

    L = tot_area / tot_win if tot_win > 0 else 0.0
    lam_eff = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / lam_eff if lam_eff > 0 else 0.0
    busy_frac = tot_busy / tot_win / c if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / tot_win * 60.0 if tot_win > 0 else 0.0

    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "runtime_units": H, "seed_list": seeds, "seeds_used": len(seeds),
        "time_unit": "minute", "win": tot_win / len(seeds) if seeds else 0.0,
        "arr": tot_arr / len(seeds) if seeds else 0.0,
        "blk": tot_blk / len(seeds) if seeds else 0.0,
        "busy_util": busy_frac, "busy_occupied": busy_frac,
        "dep": tot_dep / len(seeds) if seeds else 0.0,
        "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
