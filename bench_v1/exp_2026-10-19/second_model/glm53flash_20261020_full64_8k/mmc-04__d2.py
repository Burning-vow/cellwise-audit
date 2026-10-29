import argparse, json, math, random, heapq, sys

def run(seed, lam, mu, c, horizon):
    rng = random.Random(seed)
    t = 0.0
    warm = 0.25 * horizon
    win_len = horizon - warm
    n = 0
    busy = 0.0
    area_n = 0.0
    waits = 0.0
    served = 0
    arrivals = 0
    waited = 0
    t_next_arr = rng.expovariate(lam)
    busy_servers = 0
    deps = []
    while True:
        t_dep = deps[0] if deps else float('inf')
        if t_next_arr <= t_dep and t_next_arr <= horizon:
            t, tn = t_next_arr, t_next_arr
            area_n += n * (tn - t) if False else 0.0
            prev = t
            t = tn
            if t >= warm:
                area_n += n * (t - prev)
                busy += min(n, c) * (t - prev)
            arrivals += 1
            svc = rng.expovariate(mu)
            if n < c:
                if t >= warm:
                    pass
                n += 1
                heapq.heappush(deps, t + svc)
            else:
                if t >= warm:
                    waited += 1
                n += 1
                heapq.heappush(deps, t + svc)
                waited_not_needed = None
            t_next_arr = t + rng.expovariate(lam)
        elif t_dep <= horizon:
            prev = t
            t = t_dep
            if t >= warm:
                area_n += n * (t - prev)
                busy += min(n, c) * (t - prev)
            heapq.heappop(deps)
            n -= 1
            served += 1
        else:
            break
    p_wait = waited / arrivals if arrivals else 0.0
    L = area_n / win_len
    busy_frac = busy / win_len / c
    W = L * 60.0 / (arrivals / win_len) if arrivals else 0.0
    dep_rate = served / win_len
    return {"L": L, "W": W, "busy_frac": busy_frac, "p_wait": p_wait,
            "arr": arrivals / win_len, "dep": served / win_len,
            "blk": 0.0, "busy_util": busy_frac, "busy_occupied": 1.0 if served else 0.0,
            "dep_rate": dep_rate, "lam_eff": arrivals / win_len, "p_loss": 0.0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 10.0, 6.0, 2
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run(s, lam, mu, c, a.horizon) for s in seed_list]
    k = len(per)
    out = {
        "L": sum(p["L"] for p in per) / k,
        "W": sum(p["W"] for p in per) / k,
        "busy_frac": sum(p["busy_frac"] for p in per) / k,
        "p_wait": sum(p["p_wait"] for p in per) / k,
        "busy_util": sum(p["busy_util"] for p in per) / k,
        "busy_occupied": sum(p["busy_occupied"] for p in per) / k,
        "arr": sum(p["arr"] for p in per) / k,
        "dep": sum(p["dep"] for p in per) / k,
        "blk": sum(p["blk"] for p in per) / k,
        "dep_rate": sum(p["dep_rate"] for p in per) / k,
        "lam_eff": sum(p["lam_eff"] for p in per) / k,
        "p_loss": sum(p["p_loss"] for p in per) / k,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy_frac"] for p in per],
        "per_seed_p_wait": [p["p_wait"] for p in per],
        "per_seed_p_loss": [p["p_loss"] for p in per],
        "runtime_units": a.horizon,
        "win": 0.75 * a.horizon,
        "time_unit": "hour",
        "seed_list": seed_list,
        "seeds_used": k,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
