import argparse, json, random, math, sys

def run_seed(seed, horizon, warm, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy_until = math.inf
    next_arr = rng.expovariate(lam)
    area_n = 0.0
    area_busy = 0.0
    last = 0.0
    arrivals = 0
    departures = 0
    waits_sum = 0.0
    waited = 0
    queue = []
    while t < horizon:
        t_next_dep = busy_until
        if next_arr <= t_next_dep and next_arr <= horizon:
            t = next_arr
            area_n += n * (t - last)
            area_busy += min(n, 1) * (t - last)
            last = t
            arrivals += 1
            st = rng.expovariate(mu)
            if n == 0:
                waits_sum += 0.0
                busy_until = t + st
            else:
                queue.append((t, st))
                waited += 1
            n += 1
            next_arr = t + rng.expovariate(lam)
        else:
            if t_next_dep > horizon:
                break
            t = t_next_dep
            area_n += n * (t - last)
            area_busy += min(n, 1) * (t - last)
            last = t
            n -= 1
            departures += 1
            if queue:
                at, st = queue.pop(0)
                waits_sum += t - at
                busy_until = t + st
            else:
                busy_until = math.inf
    if last < min(warm, horizon):
        return None
    t0 = warm
    area_n -= 0.0
    L = area_n / max(horizon - t0, 1e-12) if warm == 0 else None
    return (L, area_busy, arrivals, departures, waits_sum, waited)

def run_seed2(seed, horizon, warm, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy_until = math.inf
    next_arr = rng.expovariate(lam)
    area_n = 0.0
    area_busy = 0.0
    last = 0.0
    arrivals = 0
    departures = 0
    waits_sum = 0.0
    waited = 0
    queue = []
    start = warm
    while True:
        t_next = min(next_arr, busy_until)
        if t_next > horizon and n == 0:
            break
        if next_arr <= busy_until:
            if next_arr > horizon:
                break
            t = next_arr
            if t > start:
                area_n += n * (t - max(last, start))
                area_busy += min(n, 1) * (t - max(last, start))
            last = t
            arrivals += 1
            st = rng.expovariate(mu)
            if n == 0:
                busy_until = t + st
            else:
                queue.append((t, st))
                waited += 1
            n += 1
            next_arr = t + rng.expovariate(lam)
        else:
            t = busy_until
            if t > start:
                area_n += n * (t - max(last, start))
                area_busy += min(n, 1) * (t - max(last, start))
            last = t
            n -= 1
            departures += 1
            if queue:
                at, st = queue.pop(0)
                waits_sum += t - at
                busy_until = t + st
            else:
                busy_until = math.inf
    dur = horizon - warm
    L = area_n / dur if dur > 0 else 0.0
    busy = area_busy / dur if dur > 0 else 0.0
    p_wait = waited / arrivals if arrivals else 0.0
    W = (waits_sum + departures * 0) / departures if departures else 0.0
    return dict(L=L, busy=busy, arr=arrivals, dep=departures, p_wait=p_wait, W=W)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=1)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    lam, mu = 6.0, 12.0
    if a.pert == "lam_up": lam *= 1.05
    elif a.pert == "mu_up": mu *= 1.05
    n_seeds = max(1, int(round(a.seeds)))
    s0 = int(round(a.seed_start))
    horizon = a.horizon
    warm = 0.25 * horizon
    per = []
    for k in range(n_seeds):
        per.append(run_seed2(s0 + k, horizon, warm, lam, mu))
    L = sum(p["L"] for p in per) / n_seeds
    busy = sum(p["busy"] for p in per) / n_seeds
    p_wait = sum(p["p_wait"] for p in per) / n_seeds
    W = sum(p["W"] for p in per) / n_seeds
    arr = sum(p["arr"] for p in per) / n_seeds
    dep = sum(p["dep"] for p in per) / n_seeds
    out = {
        "L": L, "W": W, "busy_frac": busy, "p_wait": p_wait,
        "runtime_units": horizon, "seed_list": [s0 + k for k in range(n_seeds)],
        "seeds_used": n_seeds, "time_unit": "hour", "win": horizon - warm,
        "arr": arr, "blk": 0.0, "busy_util": busy, "busy_occupied": busy,
        "dep": dep, "dep_rate": dep / (horizon - warm) if horizon > warm else 0.0,
        "lam_eff": arr / (horizon - warm) if horizon > warm else 0.0,
        "p_loss": 0.0,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy"] for p in per],
        "per_seed_p_loss": [0.0] * n_seeds,
        "per_seed_p_wait": [p["p_wait"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
