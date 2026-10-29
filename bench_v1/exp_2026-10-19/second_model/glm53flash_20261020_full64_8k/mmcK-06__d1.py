import argparse, heapq, json, random, sys

def run_seed(seed, H, warm, lam, mu, c, K):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    fin = []
    queue = []
    next_arr = rng.expovariate(lam)
    dep_t = None
    aN = aBusy = aUtil = 0.0
    arr = blk = dep = waits = acc = 0
    sumW = 0.0
    nW = 0

    def integrate(a, b):
        nonlocal aN, aBusy, aUtil
        lo = max(a, warm); hi = min(b, H)
        if hi > lo:
            d = hi - lo
            aN += n * d
            if n > 0:
                aBusy += d
                aUtil += min(n, c) * d

    while True:
        nxt_arr = next_arr
        nxt_dep = fin[0] if fin else None
        if nxt_dep is not None and nxt_dep <= nxt_arr:
            ev = nxt_dep; is_dep = True
        else:
            ev = nxt_arr; is_dep = False
        if ev > H:
            integrate(t, H)
            break
        integrate(t, ev)
        t = ev
        if is_dep:
            heapq.heappop(fin)
            dep += (t >= warm)
            n -= 1
            if queue:
                s = queue.pop(0)
                heapq.heappush(fin, t + s)
        else:
            ta = next_arr
            s = rng.expovariate(mu)
            next_arr = ta + rng.expovariate(lam)
            if ta >= warm:
                arr += 1
            if n >= K:
                if ta >= warm:
                    blk += 1
            else:
                if ta >= warm:
                    acc += 1
                if n >= c:
                    if ta >= warm:
                        waits += 1
                    queue.append(s)
                    n += 1
                else:
                    heapq.heappush(fin, t + s)
                    n += 1
                    if ta >= warm and not fin[:-1]:
                        pass
    win = H - warm
    L = aN / win
    busy_frac = aBusy / win
    busy_util = aUtil / win / c
    p_loss = blk / arr if arr else 0.0
    W = (aN / win) / (dep / win) if dep else 0.0
    p_wait = waits / acc if acc else 0.0
    dep_rate = dep / win
    lam_eff = (arr - blk) / win
    return dict(L=L, W=W, busy_frac=busy_frac, busy_util=busy_util,
                p_loss=p_loss, p_wait=p_wait, arr=arr, blk=blk, dep=dep,
                dep_rate=dep_rate, lam_eff=lam_eff)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    H = float(a.horizon)
    warm = 0.25 * H
    lam, mu, c, K = 6.0, 10.0, 3, 4
    if a.pert == "lam_up": lam *= 1.25
    elif a.pert == "mu_up": mu *= 1.25
    elif a.pert == "c_up": c += 1
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    results = [run_seed(s, H, warm, lam, mu, c, K) for s in seed_list]
    m = len(results)
    def avg(k): return sum(r[k] for r in results) / m
    out = {
        "L": avg("L"), "W": avg("W") * 60.0, "busy_frac": avg("busy_frac"),
        "p_loss": avg("p_loss"),
        "runtime_units": "hour", "time_unit": "hour",
        "seed_list": seed_list, "seeds_used": m,
        "win": H - warm,
        "arr": avg("arr"), "blk": avg("blk"), "dep": avg("dep"),
        "dep_rate": avg("dep_rate"), "lam_eff": avg("lam_eff"),
        "p_wait": avg("p_wait"),
        "busy_occupied": avg("busy_frac"), "busy_util": avg("busy_util"),
        "per_seed_L": [r["L"] for r in results],
        "per_seed_W": [r["W"] * 60.0 for r in results],
        "per_seed_busy_frac": [r["busy_frac"] for r in results],
        "per_seed_p_loss": [r["p_loss"] for r in results],
        "per_seed_p_wait": [r["p_wait"] for r in results],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
