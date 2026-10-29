import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam = 6.0
    mu = 12.0
    c = 1
    if a.pert == "lam_up":
        lam = lam * 1.2
    elif a.pert == "mu_up":
        mu = mu * 1.2
    elif a.pert == "c_up":
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    svc = 60.0 / mu

    per_L = []
    per_W = []
    per_busy = []
    per_ploss = []
    per_pwait = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy_area = 0.0
    tot_wait = tot_waited = 0.0
    tot_dep_wait = 0.0
    win_total = 0.0

    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        area = 0.0
        busy_area = 0.0
        arr_w = dep_w = blk_w = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_wait_sum = 0.0
        last = 0.0
        win_start = warm
        win_len = H - warm
        while True:
            if n == 0:
                nt = next_arr
            else:
                nt = min(next_arr, queue[0][1])
            if nt > H:
                dt = H - last
                if last >= win_start:
                    area += n * dt
                    busy_area += (1 if busy > 0 else 0) * dt
                elif nt > win_start:
                    dt2 = H - win_start
                    area += n * dt2
                    busy_area += (1 if busy > 0 else 0) * dt2
                break
            dt = nt - last
            if last >= win_start:
                area += n * dt
                busy_area += (1 if busy > 0 else 0) * dt
            elif nt > win_start:
                dt2 = nt - win_start
                area += n * dt2
                busy_area += (1 if busy > 0 else 0) * dt2
            last = nt
            t = nt
            if t == next_arr:
                svc_time = svc
                if busy < c:
                    busy += 1
                    queue.append((t, t + svc_time))
                    if t >= win_start:
                        arr_w += 1
                        wait_sum += 0.0
                        waited_cnt += 0
                else:
                    if t >= win_start:
                        arr_w += 1
                        blk_w += 1
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                st, et = queue.pop(0)
                busy -= 1
                n -= 1
                if t >= win_start:
                    dep_w += 1
                    dep_wait_sum += (t - st)
                if busy < c and queue:
                    pass
        if win_len <= 0:
            win_len = 1e-9
        Ls = area / win_len
        Ws = (dep_wait_sum / dep_w) if dep_w > 0 else 0.0
        bs = busy_area / win_len
        pl = (blk_w / arr_w) if arr_w > 0 else 0.0
        pw = ((arr_w - blk_w) / arr_w) if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        per_ploss.append(pl)
        per_pwait.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy_area += busy_area
        tot_dep_wait += dep_wait_sum
        win_total += win_len

    ns = max(1, a.seeds)
    L = tot_area / win_total if win_total > 0 else 0.0
    W = tot_dep_wait / tot_dep if tot_dep > 0 else 0.0
    busy_frac = tot_busy_area / win_total if win_total > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / win_total) * 60.0 if win_total > 0 else 0.0
    lam_eff = (tot_arr / win_total) * 60.0 if win_total > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    p_wait = ((tot_arr - tot_blk) / tot_arr) if tot_arr > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_frac / c,
        "busy_occupied": busy_frac,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": a.seeds,
        "time_unit": "minute",
        "win": win_total / ns,
        "arr": arr,
        "blk": blk,
        "dep": dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
