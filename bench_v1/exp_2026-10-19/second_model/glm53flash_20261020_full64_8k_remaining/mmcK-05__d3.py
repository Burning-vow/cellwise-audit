import argparse, heapq, json, math, random

def run(seed, horizon, warm, lam, mu, c, K):
    rng = random.Random(seed)
    t = 0.0
    dep_heap = []
    arrivals = 0; blocked = 0; departures = 0; waits = []
    n = 0
    area_L = 0.0; area_busy = 0.0; area_occ = 0.0
    next_arr = rng.expovariate(lam)
    last_t = 0.0
    def integrate(t0, t1):
        nonlocal area_L, area_busy, area_occ
        dt = t1 - t0
        if dt > 0:
            area_L += n * dt
            area_busy += n * dt
            if n > 0: area_occ += dt
    while t < horizon:
        t_dep = dep_heap[0][0] if dep_heap else math.inf
        t_nxt = min(next_arr, t_dep)
        if t_nxt >= horizon: t_nxt = horizon
        integrate(last_t, min(t_nxt, horizon))
        if t_nxt >= horizon:
            last_t = horizon
            break
        t = t_nxt; last_t = t
        if next_arr <= t_dep:
            arrivals += 1
            if n < K:
                if n < c:
                    wait = 0.0; n += 1
                    s = rng.expovariate(mu)
                    heapq.heappush(dep_heap, (t + s, t, 0.0))
                else:
                    wait = t_dep - t; n += 1
                    s = rng.expovariate(mu)
                    heapq.heappush(dep_heap, (t_dep + s, t, wait))
                waits.append(wait)
            else:
                blocked += 1
            next_arr = t + rng.expovariate(lam)
        else:
            _, _, w = heapq.heappop(dep_heap)
            departures += 1; n -= 1
    win = horizon - warm
    if win <= 0: win = horizon; w0 = 0.0
    else: w0 = warm
    return arrivals, blocked, departures, area_L, area_busy, area_occ, waits, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 6.0, 5.0, 3, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1; K = c + 1
    warm = a.horizon * 0.25
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per = {"L": [], "W": [], "busy_frac": [], "p_loss": [], "p_wait": []}
    agg = {"arr": 0, "blk": 0, "dep": 0, "aL": 0.0, "aB": 0.0, "aO": 0.0, "w": []}
    win = a.horizon - warm
    for s in seeds:
        arr, blk, dep, aL, aB, aO, waits, w = run(s, a.horizon, warm, lam, mu, c, K)
        acc = arr - blk
        L = aL / w
        W = (sum(waits) / acc) * 60.0 if acc > 0 else 0.0
        p_loss = blk / arr if arr > 0 else 0.0
        occ = aO / w
        p_wait = sum(1 for x in waits if x > 0) / acc if acc > 0 else 0.0
        per["L"].append(L); per["W"].append(W)
        per["busy_frac"].append(occ); per["p_loss"].append(p_loss)
        per["p_wait"].append(p_wait)
        agg["arr"] += arr / w; agg["blk"] += blk / w; agg["dep"] += dep / w
        agg["aL"] += aL / w; agg["aB"] += aB / w; agg["aO"] += aO / w
        agg["w"].extend(waits)
    m = len(seeds)
    L = agg["aL"] / m
    acc_rate = agg["arr"] - agg["blk"]
    W = (sum(agg["w"]) / (acc_rate * win * m)) * 60.0 if acc_rate > 0 else 0.0
    busy_frac = agg["aO"] / m
    p_loss = (agg["blk"] / agg["arr"]) if agg["arr"] > 0 else 0.0
    busy_util = L / c
    busy_occupied = busy_frac
    p_wait = sum(1 for x in agg["w"] if x > 0) / len(agg["w"]) if agg["w"] else 0.0
    dep_rate = agg["dep"] / m
    out = {"L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
           "runtime_units": a.horizon, "seed_list": seeds, "seeds_used": m,
           "time_unit": "hour", "win": win,
           "arr": agg["arr"] / m, "blk": agg["blk"] / m, "dep": agg["dep"] / m,
           "busy_util": busy_util, "busy_occupied": busy_occupied,
           "dep_rate": dep_rate, "lam_eff": acc_rate, "p_wait": p_wait,
           "per_seed_L": per["L"], "per_seed_W": per["W"],
           "per_seed_busy_frac": per["busy_frac"],
           "per_seed_p_loss": per["p_loss"], "per_seed_p_wait": per["p_wait"]}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
