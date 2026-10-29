import argparse, heapq, json, math, random

def run_seed(seed, H, lam, mu1, mu2):
    rng = random.Random(seed)
    tw = 0.25 * H
    t = 0.0
    t_next_arr = rng.expovariate(lam)
    events = []
    seq = 0
    heapq.heappush(events, (t_next_arr, seq, "arr", None)); seq += 1
    q1, q2 = [], []
    s1busy = False; s2busy = False
    s1cust = None; s2cust = None
    last = 0.0
    area_L = 0.0; area_busy = 0.0
    n_sys = 0
    arr = dep = waited = 0
    Wsum = 0.0
    while events:
        t, _, kind, cust = heapq.heappop(events)
        if t > H:
            break
        if t > tw:
            dt = t - last
            area_L += dt * n_sys
            area_busy += dt * ((1 if s1busy else 0) + (1 if s2busy else 0))
        last = t
        if kind == "arr":
            svc1 = rng.expovariate(mu1)
            svc2 = rng.expovariate(mu2)
            c = {"ta": t, "s1": svc1, "s2": svc2, "waited": False}
            if t >= tw:
                arr += 1
            if t_next_arr < H:
                na = t + rng.expovariate(lam)
                heapq.heappush(events, (na, seq, "arr", None)); seq += 1
                t_next_arr = na
            if not s1busy:
                s1busy = True; s1cust = c
                heapq.heappush(events, (t + c["s1"], seq, "d1", c)); seq += 1
            else:
                c["waited"] = True
                q1.append(c)
            if t >= tw:
                if c["waited"]:
                    waited += 1
        elif kind == "d1":
            s1cust = None; s1busy = False
            if q1:
                c = q1.pop(0)
                s1busy = True; s1cust = c
                heapq.heappush(events, (t + c["s1"], seq, "d1", c)); seq += 1
            c = cust
            n_sys_change = 0
            if not s2busy:
                s2busy = True; s2cust = c
                heapq.heappush(events, (t + c["s2"], seq, "d2", c)); seq += 1
            else:
                q2.append(c)
        else:
            s2cust = None; s2busy = False
            if q2:
                c = q2.pop(0)
                s2busy = True; s2cust = c
                heapq.heappush(events, (t + c["s2"], seq, "d2", c)); seq += 1
            c = cust
            n_sys -= 1
            if t >= tw:
                dep += 1
                Wsum += t - c["ta"]
        if kind == "arr":
            n_sys += 1
    win = H - tw
    if last < H:
        dt = H - last
        if H > tw:
            area_L += dt * n_sys
            area_busy += dt * ((1 if s1busy else 0) + (1 if s2busy else 0))
    W = (Wsum / dep) if dep > 0 else 0.0
    L = area_L / win
    busy_frac = area_busy / (2.0 * win)
    dep_rate = dep / win
    p_wait = (waited / arr) if arr > 0 else 0.0
    return L, W, busy_frac, dep_rate, arr, dep, p_wait

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 8.0, 10.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up":
        mu1 *= 0.9; mu2 *= 0.9
    H = a.horizon
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_bf, per_pw = [], [], [], []
    arrs, deps = [], []
    for s in seed_list:
        L, W, bf, dr, ar, dp, pw = run_seed(s, H, lam, mu1, mu2)
        per_L.append(L); per_W.append(W); per_bf.append(bf); per_pw.append(pw)
        arrs.append(ar); deps.append(dp)
    n = len(seed_list)
    out = {
        "L": sum(per_L) / n,
        "W": sum(per_W) / n,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": H - 0.25 * H,
        "arr": sum(arrs) / n,
        "blk": 0.0,
        "busy_frac": sum(per_bf) / n,
        "busy_util": sum(per_bf) / n,
        "dep": sum(deps) / n,
        "dep_rate": sum(deps) / n / (H - 0.25 * H),
        "lam_eff": sum(deps) / n / (H - 0.25 * H),
        "p_loss": 0.0,
        "p_wait": sum(per_pw) / n,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": [0.0] * n,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
