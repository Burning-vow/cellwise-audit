import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0
    tot_waiters = 0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        area = 0.0
        busy_area = 0.0
        wait_sum = 0.0
        served = 0
        waiters = 0
        arr_c = dep_c = blk_c = 0
        last = 0.0
        win_start = warm
        win_area = 0.0
        win_busy = 0.0
        win_wait = 0.0
        win_served = 0
        win_waiters = 0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_len = 0.0
        prev_t = 0.0
        while t < H:
            dt = next_arr - t
            if dt > 0:
                nt = t + dt
                if nt > H:
                    nt = H
                seg = nt - t
                if nt > win_start:
                    s0 = max(t, win_start)
                    win_area += n * (nt - s0)
                    win_busy += (1 if busy > 0 else 0) * (nt - s0)
                t = nt
            if t >= H:
                break
            if t >= next_arr:
                arr_c += 1
                if t >= win_start:
                    win_arr += 1
                if busy < c:
                    busy += 1
                    st = rng.expovariate(mu)
                    queue.append((t, st))
                else:
                    blk_c += 1
                    if t >= win_start:
                        win_blk += 1
                next_arr = t + rng.expovariate(lam)
            while queue and queue[0][0] + queue[0][1] <= t:
                at, st = queue.pop(0)
                busy -= 1
                dep_c += 1
                served += 1
                w = (at + st) - at
                wait_sum += w
                waiters += 1
                if t >= win_start:
                    win_dep += 1
                    win_served += 1
                    win_wait += w
                    win_waiters += 1
                if queue:
                    at2, st2 = queue[0]
                    queue[0] = (t, st2)
        win_len = H - win_start
        if win_len <= 0:
            win_len = H
        L = win_area / win_len if win_len > 0 else 0.0
        W = win_wait / win_served if win_served > 0 else 0.0
        bf = win_busy / win_len if win_len > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_waiters / win_arr if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_wait += win_wait
        tot_served += win_served
        tot_waiters += win_waiters
        tot_win += win_len

    nseeds = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waiters / tot_arr if tot_arr > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "runtime_units": H, "seed_list": seeds, "seeds_used": nseeds,
        "time_unit": "hour", "win": tot_win / nseeds,
        "arr": arr, "blk": blk, "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "dep": dep, "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
