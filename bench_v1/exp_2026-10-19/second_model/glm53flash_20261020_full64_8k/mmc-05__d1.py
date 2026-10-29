import argparse, json, random, math, heapq

def run_seed(seed, horizon, warm, lam, mu, c):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy = 0
    ev = []
    heapq.heappush(ev, (rng.expovariate(lam), 0))
    area_N = 0.0
    area_B = 0.0
    arr = dep = waits = 0.0
    nwait = 0
    nw = 0
    q = []
    sarea_N = 0.0
    sarea_B = 0.0
    sarr = sdep = swaits = 0.0
    snwait = 0
    nsnw = 0
    p_wait_num = 0
    p_wait_den = 0
    sp_wait_num = 0
    sp_wait_den = 0
    while ev:
        te, typ = heapq.heappop(ev)
        if te > horizon:
            break
        dt = te - t
        area_N += n * dt
        area_B += busy * dt
        if te >= warm:
            sarea_N += n * dt
            sarea_B += busy * dt
        t = te
        if typ == 0:
            st = rng.expovariate(mu)
            arr += 1
            if t >= warm:
                sarr += 1
                p_wait_den += 1
                sp_wait_den += 1
            delayed = n >= c
            if delayed:
                if t >= warm:
                    p_wait_num += 1
                    sp_wait_num += 1
            n += 1
            if n <= c:
                busy += 1
                heapq.heappush(ev, (t + st, 1))
                if t >= warm:
                    swaits += 0.0
                    nsnw += 0
                    waits += 0.0
                    nw += 1
                    dep += 1
                    if True:
                        sdep += 1
                n -= 1
            else:
                q.append((t, st))
            heapq.heappush(ev, (t + rng.expovariate(lam), 0))
        else:
            dep += 1
            if t >= warm:
                sdep += 1
            n -= 1
            busy -= 1
            if q:
                at, st = q.pop(0)
                w = t - at
                waits += w
                nw += 1
                if t >= warm:
                    swaits += w
                    nsnw += 1
                if n + 1 <= c:
                    pass
                heapq.heappush(ev, (t + st, 1))
                busy += 1
                n += 1
    if nsnw == 0:
        nsnw = 1
    if sp_wait_den == 0:
        sp_wait_den = 1
    W = swaits / nsnw * 60.0 if nsnw > 0 else 0.0
    L = sarea_N / max(horizon - warm, 1e-12)
    bf = sarea_B / max(horizon - warm, 1e-12) / c
    pw = sp_wait_num / sp_wait_den
    return L, W, bf, pw, sarr, sdep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 10.0, 10.0, 2
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c += 1
    horizon = a.horizon
    warm = 0.25 * horizon
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_bf, per_pw, per_pl = [], [], [], [], []
    tarr = tdep = 0.0
    for s in seeds:
        L, W, bf, pw, sarr, sdep = run_seed(s, horizon, warm, lam, mu, c)
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pw.append(pw); per_pl.append(0.0)
        tarr += sarr; tdep += sdep
    m = len(seeds)
    win = horizon - warm
    out = {
        "L": sum(per_L)/m, "W": sum(per_W)/m,
        "busy_frac": sum(per_bf)/m, "busy_util": sum(per_bf)/m,
        "busy_occupied": 1.0,
        "p_wait": sum(per_pw)/m, "p_loss": 0.0,
        "runtime_units": "hour", "time_unit": "hour",
        "seed_list": seeds, "seeds_used": m, "win": win,
        "arr": tarr/m, "dep": tdep/m, "blk": 0.0,
        "dep_rate": (tdep/m)/win, "lam_eff": (tarr/m)/win,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
