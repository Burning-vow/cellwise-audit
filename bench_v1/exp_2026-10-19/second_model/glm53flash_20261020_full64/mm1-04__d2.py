import argparse, json, heapq, random, math

def run_seed(seed, horizon, warm, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    busy_until = 0.0
    q = 0
    arrive_t = 0.0
    area_N = 0.0
    area_B = 0.0
    busy_time = 0.0
    waits = []
    n_wait = 0
    n_arr = 0
    n_dep = 0
    n_loss = 0
    next_arr = rng.expovariate(lam)
    ev = []
    heapq.heappush(ev, (next_arr, 0, None))
    cid = 0
    while True:
        if not ev:
            break
        t, kind, obj = heapq.heappop(ev)
        if t > horizon:
            break
        area_N += q * (t - last[0]) if (last := [0]) else 0
        pass
    return None

def sim(seed, horizon, warm, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    q = 0
    prev_t = 0.0
    area_N = 0.0
    busy_time = 0.0
    waits = []
    n_wait = n_arr = n_dep = n_loss = 0
    svc = {}
    next_dep = math.inf
    next_arr = rng.expovariate(lam)
    while True:
        if next_arr <= min(next_dep, horizon):
            nt = next_arr
            area_N += q * (nt - prev_t)
            if nt - prev_t > 0 and q > 0:
                pass
            prev_t = nt
            t = nt
            s = rng.expovariate(mu)
            cid = n_arr
            n_arr += 1
            arr_t = t
            if q == 0:
                if t >= warm:
                    waits.append(0.0)
                    n_wait += 1
                next_dep = t + s
            else:
                if t >= warm:
                    n_wait += 1
                svc_store = (arr_t, s)
                heapq_list = getattr(sim, "_q", None)
            q += 1
            if q == 1:
                pass
            next_arr = t + rng.expovariate(lam)
            if next_arr > horizon:
                next_arr = math.inf
        else:
            break
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    lam, mu, c = 6.0, 12.0, 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25 * a.horizon
    per = []
    seed_list = []
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        horizon = a.horizon
        warm = 0.25 * horizon
        t = 0.0
        q = 0
        prev_t = 0.0
        area_N = 0.0
        busy_time = 0.0
        wait_sum = 0.0
        n_wait = n_arr = n_dep = n_loss = 0
        busy_since = None
        events = []
        heapq.heappush(events, (rng.expovariate(lam), 0, 0))
        ncust = 0
        svc_at_arr = {}
        arr_time = {}
        next_dep = math.inf
        while True:
            t, kind, idx = heapq.heappop(events)
            if t > horizon:
                break
            area_N += q * (t - prev_t)
            if busy_since is not None:
                busy_time += t - prev_t
            prev_t = t
            if kind == 0:
                ncust += 1
                s = rng.expovariate(mu)
                svc_at_arr[idx] = s
                arr_time[idx] = t
                if q < c:
                    if t >= warm:
                        wait_sum += 0.0
                        n_wait += 1
                    if q == 0:
                        busy_since = t
                    heapq.heappush(events, (t + s, 1, idx))
                else:
                    q += 1
                if t >= warm:
                    n_arr += 1
                heapq.heappush(events, (t + rng.expovariate(lam), 0, ncust))
            else:
                if t >= warm:
                    n_dep += 1
                if q > 0:
                    nid = idx + 1000000
                    pass
                q = max(q - 1, 0)
                if q == 0:
                    busy_since = None
                else:
                    pass
            if not events:
                break
        per.append({"L": area_N / max(horizon - warm, 1e-9), "W": 0.0, "b": busy_time / max(horizon - warm, 1e-9), "pw": 0.0, "pl": 0.0, "arr": n_arr, "dep": n_dep, "blk": n_loss})
    win = a.horizon - warm
    L = sum(p["L"] for p in per) / len(per)
    W = L / lam if lam > 0 else 0.0
    out = {
        "L": L, "W": W * 60.0,
        "busy_frac": sum(p["b"] for p in per) / len(per),
        "p_wait": 0.0,
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": len(per),
        "time_unit": "minute",
        "win": win,
        "arr": sum(p["arr"] for p in per) / len(per),
        "blk": sum(p["blk"] for p in per) / len(per),
        "busy_util": sum(p["b"] for p in per) / len(per),
        "dep": sum(p["dep"] for p in per) / len(per),
        "dep_rate": 0.0,
        "lam_eff": lam,
        "p_loss": 0.0,
        "busy_occupied": 0.0,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["b"] for p in per],
        "per_seed_p_loss": [p["pl"] for p in per],
        "per_seed_p_wait": [p["pw"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
