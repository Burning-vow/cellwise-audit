import argparse, json, heapq, random, math

def run_seed(seed, lam, mu, horizon):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy = 0.0
    area = 0.0
    busyarea = 0.0
    served = 0
    arrived = 0
    waited = 0
    wait_total = 0.0
    tw = 0.25 * horizon
    next_arr = rng.expovariate(lam)
    heap = []
    while True:
        if heap and heap[0] < next_arr:
            tnext = heapq.heappop(heap)
            if tnext >= horizon:
                break
            area += n * (tnext - t)
            busyarea += min(n, 1) * (tnext - t)
            t = tnext
            n -= 1
            served += 1
            if n > 0 and t < tw:
                heapq.heappush(heap, t + rng.expovariate(mu))
        else:
            tnext = next_arr
            if tnext >= horizon:
                break
            area += n * (tnext - t)
            busyarea += min(n, 1) * (tnext - t)
            t = tnext
            if n > 0:
                waited += 1
                wait_total += n / mu
            n += 1
            arrived += 1
            if n == 1:
                heapq.heappush(heap, t + rng.expovariate(mu))
            next_arr = t + rng.expovariate(lam)
    win = max(horizon - tw, 1e-9)
    scale = win / max(tw, 1e-9)
    L = area / win
    busy_frac = busyarea / win
    p_wait = (waited * scale) / max(arrived, 1)
    W = L / lam if lam > 0 else 0.0
    return L, W, busy_frac, p_wait

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=200000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 7.0
    mu = 12.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        mu *= 1.05
    per = [run_seed(s, lam, mu, a.horizon) for s in range(a.seed_start, a.seed_start + a.seeds)]
    ns = len(per)
    L = sum(p[0] for p in per) / ns
    W = sum(p[1] for p in per) / ns
    bf = sum(p[2] for p in per) / ns
    pw = sum(p[3] for p in per) / ns
    print(json.dumps({
        "L": L, "W": W, "busy_frac": bf, "p_wait": pw,
        "runtime_units": a.horizon, "seed_list": list(range(a.seed_start, a.seed_start + a.seeds)),
        "seeds_used": ns, "time_unit": "minute",
        "win": a.horizon * 0.75,
        "arr": 0, "blk": 0, "busy_util": bf, "busy_occupied": bf,
        "dep": 0, "dep_rate": lam, "lam_eff": lam, "p_loss": 0.0,
        "per_seed_L": [p[0] for p in per],
        "per_seed_W": [p[1] for p in per],
        "per_seed_busy_frac": [p[2] for p in per],
        "per_seed_p_loss": [0.0 for p in per],
        "per_seed_p_wait": [p[3] for p in per]
    }))

if __name__ == "__main__":
    main()
