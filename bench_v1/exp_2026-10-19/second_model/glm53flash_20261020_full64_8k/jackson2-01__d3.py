import argparse, json, math, random

def run_seed(seed, horizon, lam, mu1, mu2, warm):
    rng = random.Random(seed)
    t = 0.0
    q1 = 0; s1 = 0; q2 = 0; s2 = 0
    next_arr = rng.expovariate(lam)
    next_c1 = math.inf; next_c2 = math.inf
    cur1 = None; cur2 = None
    sumL = 0.0; sumB = 0.0
    wt_sum = 0.0; wt_n = 0
    waited = 0; comp = 0
    arr_w = 0; dep_w = 0
    last = 0.0
    def integrate(a, b):
        nonlocal sumL, sumB
        dt = a - b
        n = q1 + s1 + q2 + s2
        sumL += n * dt
        sumB += (s1 + s2) * dt
    while True:
        nt = min(next_arr, next_c1, next_c2)
        if nt > horizon: break
        integrate(nt, last)
        last = nt
        t = nt
        if t == next_arr:
            arr_at = t
            if s1 == 0:
                s1 = 1; cur1 = (arr_at, t); next_c1 = t + rng.expovariate(mu1)
            else:
                q1 += 1
                q1list.append(arr_at) if False else None
            arr_stack.append(arr_at) if False else None
            next_arr = t + rng.expovariate(lam)
            # need queue storage
        # handled below
    return None

def sim(seed, horizon, lam, mu1, mu2):
    rng = random.Random(seed)
    warm = 0.25 * horizon
    t = 0.0
    q1 = []; q2 = []
    s1 = None; s2 = None
    next_arr = rng.expovariate(lam)
    next_c1 = math.inf; next_c2 = math.inf
    sumL = 0.0; sumB = 0.0; last = 0.0
    wt_sum = 0.0; wt_n = 0; waited = 0; comp = 0
    arr_w = 0; dep_w = 0
    while True:
        nt = min(next_arr, next_c1, next_c2)
        if nt > horizon: break
        dt = nt - last
        sumL += (len(q1) + (1 if s1 is not None else 0) + len(q2) + (1 if s2 is not None else 0)) * dt
        sumB += ((1 if s1 is not None else 0) + (1 if s2 is not None else 0)) * dt
        last = nt; t = nt
        if t == next_arr:
            a = t
            if s1 is None:
                s1 = a
                next_c1 = t + rng.expovariate(mu1)
            else:
                q1.append(a)
            arr_w += (t >= warm)
            next_arr = t + rng.expovariate(lam)
        elif t == next_c1:
            a = s1
            if s2 is None:
                s2 = a
                next_c2 = t + rng.expovariate(mu2)
            else:
                q2.append(a)
            if q1:
                s1 = q1.pop(0)
                if t >= warm and t - s1 > 0: pass
                if t - s1 > 1e-12 and t >= warm: waited += 1
                next_c1 = t + rng.expovariate(mu1)
            else:
                s1 = None; next_c1 = math.inf
        else:
            a = s2
            if t >= warm:
                wt_sum += (t - a) * 60.0; wt_n += 1; dep_w += 1
            if q2:
                s2 = q2.pop(0)
                if t - s2 > 1e-12 and t >= warm: waited += 1
                next_c2 = t + rng.expovariate(mu2)
            else:
                s2 = None; next_c2 = math.inf
    win = horizon - warm
    W = wt_sum / wt_n if wt_n else 0.0
    L = sumL / win
    busy = sumB / win
    pwait = waited / (wt_n + 1e-12)
    return L, W, busy, pwait, arr_w, dep_w, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu1, mu2 = 4.0, 8.0, 10.0
    if a.pert == "lam_up": lam *= 1.25
    elif a.pert == "mu_up": mu1 *= 1.25; mu2 *= 1.25
    elif a.pert == "c_up": mu1 /= 1.25; mu2 /= 1.25
    per_L = []; per_W = []; per_b = []; per_pw = []; seed_list = []
    arrs = []; deps = []
    win = None
    for k in range(a.seeds):
        sd = a.seed_start + k
        L, W, b, pw, ar, dp, win = sim(sd, a.horizon, lam, mu1, mu2)
        seed_list.append(sd); per_L.append(L); per_W.append(W)
        per_b.append(b); per_pw.append(pw); arrs.append(ar); deps.append(dp)
    n = len(seed_list)
    out = {
        "L": sum(per_L)/n, "W": sum(per_W)/n,
        "runtime_units": a.horizon, "seed_list": seed_list, "seeds_used": n,
        "time_unit": "hour", "win": win,
        "arr": sum(arrs)/n, "dep": sum(deps)/n,
        "blk": 0.0, "p_loss": 0.0,
        "busy_frac": sum(per_b)/n, "busy_util": sum(per_b)/n,
        "dep_rate": (sum(deps)/n)/win,
        "lam_eff": (sum(arrs)/n)/win,
        "p_wait": sum(per_pw)/n,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_b, "per_seed_p_loss": [0.0]*n,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
