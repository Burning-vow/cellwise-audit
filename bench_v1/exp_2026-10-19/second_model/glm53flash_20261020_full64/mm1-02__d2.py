import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, c = 4.0, 12.0, 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 2

    H = float(a.horizon)
    win_start = 0.25 * H
    win = H - win_start
    INF = float("inf")

    seed_list, per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], [], []
    tot_arr = tot_dep = tot_blk = tot_wait = 0.0
    tot_busy_area = 0.0
    seeds_used = 0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        N = 0
        queue = []
        next_arr = rng.expovariate(lam)
        dep_time = INF
        area_N = 0.0
        area_min = 0.0
        arr_w = dep_w = waited_w = 0
        soj = 0.0
        busy_area = 0.0

        def acc(t0, t1, Nv):
            nonlocal area_N, area_min, busy_area
            lo = max(t0, win_start)
            hi = min(t1, H)
            if hi > lo:
                dt = hi - lo
                area_N += Nv * dt
                area_min += min(Nv, c) * dt
                if Nv > 0:
                    busy_area += dt

        while t < H:
            nt = next_arr if next_arr <= dep_time else dep_time
            if nt >= H:
                acc(t, H, N)
                t = H
                break
            acc(t, nt, N)
            t = nt
            if next_arr <= dep_time:
                d = rng.expovariate(mu)
                if N < c:
                    if t >= win_start:
                        arr_w += 1
                    dep_time = t + d
                    head = (t, d)
                    N += 1
                else:
                    if t >= win_start:
                        arr_w += 1
                        if N >= 1 and N >= c:
                            waited_w += 1
                    queue.append((t, d))
                next_arr = t + rng.expovariate(lam)
            else:
                at, d = head
                if t >= win_start:
                    soj += t - at
                    dep_w += 1
                N -= 1
                if queue:
                    head = queue.pop(0)
                    dep_time = t + head[1]
                    N += 1
                else:
                    dep_time = INF
                    head = None
                if N == 0:
                    head = None

        if dep_w > 0:
            W = soj / dep_w
        else:
            W = float("nan")
        L = area_N / win
        bf = area_min / win
        pw = (waited_w / arr_w) if arr_w > 0 else 0.0
        seed_list.append(s)
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += 0
        tot_wait += pw
        tot_busy_area += bf
        seeds_used += 1

    n = seeds_used
    Lm = sum(per_L) / n
    Wm = sum(per_W) / n
    bfm = sum(per_bf) / n
    pwait = sum(per_pw) / n
    out = {
        "L": Lm,
        "W": Wm,
        "busy_frac": bfm,
        "p_wait": pwait,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win,
        "arr": tot_arr / n,
        "blk": tot_blk / n,
        "busy_util": bfm,
        "busy_occupied": bfm,
        "dep": tot_dep / n,
        "dep_rate": tot_dep / n / win,
        "lam_eff": tot_arr / n / win,
        "p_loss": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
