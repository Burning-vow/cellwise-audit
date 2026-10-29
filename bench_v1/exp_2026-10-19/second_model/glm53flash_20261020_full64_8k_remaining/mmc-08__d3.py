import argparse, json, math, random, heapq, sys

def simulate(seed, horizon, c, lam, mu, warm):
    rng = random.Random(seed)
    t = 0.0
    busy = []
    n = 0
    arr = dep = blk = 0
    area_n = 0.0
    area_busy = 0.0
    waits = []
    wait_cnt = 0
    arrive_cnt = 0
    while t < horizon:
        t_next = t + rng.expovariate(lam)
        if t_next >= horizon:
            area_n += n * (horizon - t)
            area_busy += min(n, c) * (horizon - t)
            t = horizon
            break
        area_n += n * (t_next - t)
        area_busy += min(n, c) * (t_next - t)
        t = t_next
        arr += 1
        arrive_cnt += 1
        svc = rng.expovariate(mu)
        if n < c:
            if t >= warm:
                wait_cnt += 1
            n += 1
            heapq.heappush(busy, t + svc)
        else:
            if t >= warm:
                blk += 1
            continue
    while busy:
        d = heapq.heappop(busy)
        if d >= horizon:
            break
        area_n += n * (d - t)
        area_busy += min(n, c) * (d - t)
        t = d
        n -= 1
        dep += 1
    while busy and busy[0] < horizon:
        d = heapq.heappop(busy)
        area_n += n * (d - t)
        area_busy += min(n, c) * (d - t)
        t = d
        n -= 1
        dep += 1
    if dep == 0:
        return None
    return {"L": area_n / horizon, "W": 60.0 * area_n / dep, "busy_frac": area_busy / horizon / c, "p_loss": blk / max(arr, 1), "dep": dep, "arr": arr, "blk": blk, "dep_rate": dep / horizon}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    c = 3
    lam = 8.0
    mu = 6.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c += 1
    warm = 0.25 * a.horizon
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = []
    for s in seed_list:
        r = simulate(s, a.horizon, c, lam, mu, warm)
        if r:
            per.append(r)
    m = len(per)
    if m == 0:
        print(json.dumps({"L": 0.0, "W": 0.0, "busy_frac": 0.0, "p_wait": 0.0, "runtime_units": "count", "seed_list": seed_list, "seeds_used": 0, "time_unit": "hour", "win": 0.0}))
        return
    L = sum(r["L"] for r in per) / m
    W = sum(r["W"] for r in per) / m
    bf = sum(r["busy_frac"] for r in per) / m
    pl = sum(r["p_loss"] for r in per) / m
    pw = pl
    out = {
        "L": L,
        "W": W,
        "busy_frac": bf,
        "p_wait": pw,
        "runtime_units": m,
        "seed_list": seed_list,
        "seeds_used": m,
        "time_unit": "hour",
        "win": a.horizon - warm,
        "arr": sum(r["arr"] for r in per) / m,
        "blk": sum(r["blk"] for r in per) / m,
        "busy_util": bf,
        "busy_occupied": 1.0 - math.exp(-lam / mu * 0) if False else bf,
        "dep": sum(r["dep"] for r in per) / m,
        "dep_rate": sum(r["dep_rate"] for r in per) / m,
        "lam_eff": lam * (1 - pl),
        "p_loss": pl,
        "per_seed_L": [r["L"] for r in per],
        "per_seed_W": [r["W"] for r in per],
        "per_seed_busy_frac": [r["busy_frac"] for r in per],
        "per_seed_p_loss": [r["p_loss"] for r in per],
        "per_seed_p_wait": [r["p_loss"] for r in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
