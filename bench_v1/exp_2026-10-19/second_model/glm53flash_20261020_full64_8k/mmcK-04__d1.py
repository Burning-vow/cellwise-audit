import json, argparse, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=lambda x: float(x), default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 8.0, 10.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = a.horizon * 0.25
    win = a.horizon - warm
    per = {"L": [], "W": [], "busy_frac": [], "p_loss": [], "p_wait": []}
    agg = {"arr": 0, "dep": 0, "blk": 0, "area": 0.0, "busy_area": 0.0, "qarea": 0.0, "wait": 0.0, "waits": 0, "served": 0}
    seeds_used = 0
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        busy = []  # heap of departure times
        n = 0
        pend = []
        arr_n = dep_n = blk_n = 0
        area = busy_area = qarea = 0.0
        wait_sum = waits = served = 0.0
        last = 0.0
        while t < a.horizon:
            nxt_dep = busy[0] if busy else math.inf
            t2 = min(next_arr, nxt_dep)
            if t2 > a.horizon: t2 = a.horizon
            if t2 >= warm:
                dt = t2 - max(t, warm)
                area += n * dt
                busy_area += (1 if n > 0 else 0) * dt
                qarea += max(0, n - c) * dt
            t = t2
            if next_arr <= nxt_dep and t < a.horizon:
                st = rng.expovariate(mu)
                arr_n += 1
                if n < K:
                    if n >= c:
                        wait_sum += st; waits += 1
                    n += 1
                    heapq.heappush(busy, t + st)
                else:
                    blk_n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if busy and t >= busy[0]:
                    heapq.heappop(busy)
                    n -= 1
                    dep_n += 1
                    served += 1
                elif t >= a.horizon:
                    break
        seeds_used += 1
        L = area / win
        W = (wait_sum + L * win) / max(served, 1) * 60
        bf = busy_area / win
        pl = blk_n / max(arr_n, 1)
        pw = waits / max(served, 1)
        per["L"].append(L); per["W"].append(W); per["busy_frac"].append(bf)
        per["p_loss"].append(pl); per["p_wait"].append(pw)
        agg["arr"] += arr_n / win; agg["dep"] += dep_n / win; agg["blk"] += blk_n / win
        agg["area"] += area / win; agg["busy_area"] += bf; agg["qarea"] += qarea / win
        agg["wait"] += wait_sum; agg["waits"] += waits; agg["served"] += served
    S = seeds_used
    L = agg["area"] / S
    W = (agg["wait"] / agg["served"] + agg["qarea"] / S / max(agg["dep"] / S, 1e-9)) * 60
    busy_frac = agg["busy_area"] / S
    p_loss = agg["blk"] / max(agg["arr"], 1e-9)
    p_wait = agg["waits"] / max(agg["served"], 1)
    busy_util = L / c
    lam_eff = agg["dep"]
    out = {
        "L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
        "runtime_units": a.horizon, "seed_list": list(range(a.seed_start, a.seed_start + S)),
        "seeds_used": S, "time_unit": "hour", "win": win,
        "arr": agg["arr"] / S, "blk": agg["blk"] / S, "busy_util": busy_util,
        "busy_occupied": busy_frac, "dep": agg["dep"] / S, "dep_rate": agg["dep"] / S,
        "lam_eff": lam_eff, "p_wait": p_wait,
        "per_seed_L": per["L"], "per_seed_W": per["W"],
        "per_seed_busy_frac": per["busy_frac"], "per_seed_p_loss": per["p_loss"],
        "per_seed_p_wait": per["p_wait"],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
