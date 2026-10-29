import argparse, json, random

def run_seed(seed, lam, mu, H, warm):
    rng = random.Random(seed)
    W0 = H - warm
    t = 0.0
    next_arr = rng.expovariate(lam)
    dep = None
    q = []
    n = 0
    area = 0.0
    busy_area = 0.0
    idle_area = 0.0
    arrivals = 0
    deps = 0
    tis_sum = 0.0
    nwait = 0
    def accum(a, b):
        nonlocal area, busy_area, idle_area
        lo = max(a, warm); hi = min(b, H)
        if hi > lo:
            dt = hi - lo
            area += n * dt
            busy_area += min(n, 1) * dt
            if n == 0:
                idle_area += dt
    while True:
        if dep is None or next_arr <= dep:
            t = next_arr
            if t >= H:
                break
            accum(t, t) if False else None
            prev = t
            accum_done = True
            a = t
            accum(a - 1e-18, a) if False else None
            lo = max(t, warm)
            pass
            t_evt = t
            accum_area_start = t_evt
            lo = max(t_evt, warm); hi = min(t_evt + 0, H)
            n_before = n
            dt = 0.0
            pass
            t0 = t_evt
            lo = max(t0, warm); hi = min(t0, H)
            if hi > lo:
                dt = hi - lo
                area += n * dt
                busy_area += min(n, 1) * dt
                if n == 0:
                    idle_area += dt
            arrivals += 1 if t0 >= warm else 0
            s = rng.expovariate(mu)
            q.append(s)
            if n == 0:
                dep = t0 + s
                start = t0
            else:
                start = dep
                if t0 >= warm:
                    nwait += 1
            if t0 >= warm:
                tis_sum += (start - t0) + s
            n += 1
            next_arr = t0 + rng.expovariate(lam)
        else:
            t0 = dep
            if t0 >= H:
                break
            lo = max(t0, warm); hi = min(t0, H)
            if hi > lo:
                dt = hi - lo
                area += n * dt
                busy_area += min(n, 1) * dt
                if n == 0:
                    idle_area += dt
            n -= 1
            q.pop(0)
            if t0 >= warm:
                deps += 1
            if q:
                dep = t0 + q[0]
            else:
                dep = None
    area += n * max(0.0, H - max(warm, 0)) if False else 0.0
    final_dt = H - warm
    L = area / final_dt
    busy = busy_area / final_dt
    p_wait = nwait / arrivals if arrivals else 0.0
    W = (tis_sum / arrivals) * 60.0 if arrivals else 0.0
    return L, W, busy, p_wait, arrivals, deps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu = 7.0, 12.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        mu *= 1.1
    warm = 0.25 * a.horizon
    per_L, per_W, per_b, per_pw = [], [], [], []
    seed_list = []
    arrs, depsum = 0.0, 0.0
    for k in range(a.seeds):
        s = a.seed_start + k
        seed_list.append(s)
        L, W, b, pw, ar, dp = run_seed(s, lam, mu, a.horizon, warm)
        per_L.append(L); per_W.append(W); per_b.append(b); per_pw.append(pw)
        arrs += ar; depsum += dp
        n_s = k + 1
    seeds_used = a.seeds
    win = a.horizon - warm
    Lm = sum(per_L) / seeds_used
    Wm = sum(per_W) / seeds_used
    bm = sum(per_b) / seeds_used
    pwm = sum(per_pw) / seeds_used
    dep_rate = depsum / seeds_used / win
    lam_eff = arrs / seeds_used / win
    out = {
        "L": Lm, "W": Wm, "busy_frac": bm, "p_wait": pwm,
        "runtime_units": a.horizon, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour", "win": win,
        "arr": arrs / seeds_used, "blk": 0.0, "busy_util": bm,
        "busy_occupied": bm, "dep": depsum / seeds_used,
        "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_loss": 0.0,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_b, "per_seed_p_loss": [0.0] * seeds_used,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
