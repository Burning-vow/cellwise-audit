import argparse, heapq, json, math, random

def run_seed(seed, horizon, lam, mu1, mu2):
    rng = random.Random(seed)
    events = []
    t0 = rng.expovariate(lam)
    heapq.heappush(events, (t0, 0, 0))
    nid = 1
    t = 0.0
    warm = 0.25 * horizon
    area = 0.0
    n1 = n2 = 0
    q1 = []
    q2 = []
    arr = dep = 0
    sojourns = []
    busy1 = busy2 = 0.0
    while events:
        nt, kind, sid = events[0]
        if nt > horizon:
            break
        area += (n1 + n2) * (nt - t)
        dt = nt - t
        if n1 > 0: busy1 += dt
        if n2 > 0: busy2 += dt
        t = nt
        heapq.heappop(events)
        if t < warm:
            pass
        if kind == 0:
            if t >= warm: arr += 1
            s1 = rng.expovariate(mu1)
            s2 = rng.expovariate(mu2)
            heapq.heappush(events, (t + s1, 1, (t, s2)))
            heapq.heappush(events, (t + rng.expovariate(lam), 0, 0))
            n1 += 1
        elif kind == 1:
            arr_t, s2 = sid
            n1 -= 1
            n2 += 1
            heapq.heappush(events, (t + s2, 2, arr_t))
        else:
            arr_t = sid
            n2 -= 1
            if t >= warm:
                dep += 1
                sojourns.append(t - arr_t)
    return area / horizon, sojourns, arr, dep, busy1, busy2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    N = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 4.0; mu1 = 10.0; mu2 = 10.0
    if a.pert == "lam_up": lam = 4.4
    elif a.pert == "mu_up": mu1 = 11.0; mu2 = 11.0
    elif a.pert == "c_up": mu1 = 9.0; mu2 = 9.0
    seed_list = list(range(S, S + N))
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tarr = tdep = tbusy = 0.0
    wtot = 0.0; wcnt = 0
    for sd in seed_list:
        L, soj, arr, dep, b1, b2 = run_seed(sd, H, lam, mu1, mu2)
        win = 0.75 * H
        W = sum(soj) / len(soj) if soj else 0.0
        p_wait = len(soj) / arr if arr else 0.0
        per_L.append(L); per_W.append(W)
        per_bf.append((b1 + b2) / H); per_pl.append(0.0); per_pw.append(p_wait)
        tarr += arr; tdep += dep; tbusy += (b1 + b2)
        wtot += W * len(soj); wcnt += len(soj)
    m = len(seed_list)
    L = sum(per_L) / m
    W = wtot / wcnt if wcnt else 0.0
    busy_frac = tbusy / (m * H)
    out = {
        "L": L, "W": W, "runtime_units": H, "seed_list": seed_list,
        "seeds_used": m, "time_unit": "hour", "win": 0.75 * H,
        "arr": tarr / m, "dep": tdep / m, "blk": 0.0,
        "dep_rate": tdep / (m * 0.75 * H),
        "lam_eff": lam, "p_loss": 0.0,
        "p_wait": (tdep / tarr) if tarr else 0.0,
        "busy_frac": busy_frac, "busy_util": busy_frac,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
