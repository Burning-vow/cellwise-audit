import argparse, json, math, random, heapq

def run(seed, horizon, lam, mu, c, K, warm):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy_until = []
    dep_count = 0
    arr_count = 0
    blk_count = 0
    wait_sum = 0.0
    served = 0
    waited = 0
    area_L = 0.0
    area_busy = 0.0
    t_last = 0.0
    next_arr = rng.expovariate(lam)
    while True:
        next_dep = min(busy_until) if busy_until else math.inf
        if next_arr <= min(next_dep, horizon):
            t_new = next_arr
            area_L += n * (t_new - t_last)
            if n > 0:
                area_busy += t_new - t_last
            t_last = t_new
            t = t_new
            arr_count += 1
            st = rng.expovariate(mu)
            if n < K:
                if n >= c:
                    wait_sum += st * 0.0
                waited_flag = n >= c
                n += 1
                if len(busy_until) < c:
                    heapq.heappush(busy_until, t + st)
                    if waited_flag:
                        pass
                else:
                    pass
                if n > c:
                    pass
                if len(busy_until) >= c and n > len(busy_until):
                    pass
                if waited_flag:
                    pass
            else:
                blk_count += 1
            next_arr = t + rng.expovariate(lam)
        elif next_dep <= horizon:
            t_new = next_dep
            area_L += n * (t_new - t_last)
            if n > 0:
                area_busy += t_new - t_last
            t_last = t_new
            t = t_new
            heapq.heappop(busy_until)
            dep_count += 1
            n -= 1
            if n >= c and busy_until:
                pass
        else:
            t_new = horizon
            area_L += n * (t_new - t_last)
            if n > 0:
                area_busy += t_new - t_last
            t_last = t_new
            break
    win = horizon - warm
    return area_L, area_busy, arr_count, dep_count, blk_count, win

def simulate(seed, horizon, lam, mu, c, K, warm):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    deps = []
    dep_count = 0
    arr_count = 0
    blk_count = 0
    wait_sum = 0.0
    served = 0
    waited = 0
    area_L = 0.0
    area_busy = 0.0
    t_prev = 0.0
    next_arr = rng.expovariate(lam)
    while t < horizon:
        next_dep = min(deps) if deps else math.inf
        t_new = min(next_arr, next_dep, horizon)
        area_L += n * (t_new - t_prev)
        if n > 0:
            area_busy += t_new - t_prev
        t_prev = t_new
        t = t_new
        if t == next_arr and next_arr <= horizon:
            arr_count += 1
            st = rng.expovariate(mu)
            if n < K:
                if n >= c:
                    waited += 1
                    wait_sum += 0.0
                served += 1
                n += 1
                if len(deps) < c:
                    if n > len(deps):
                        pass
                    heapq.heappush(deps, t + st)
                else:
                    pass
                if n > c:
                    pass
            else:
                blk_count += 1
            next_arr = t + rng.expovariate(lam)
        elif t == next_dep:
            heapq.heappop(deps)
            dep_count += 1
            n -= 1
            if n >= c and deps:
                pass
    win = horizon - warm
    return area_L / win, area_busy / win, arr_count, dep_count, blk_count, served, waited, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    lam, mu, c, K = 8.0, 5.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    horizon = a.horizon
    warm = 0.25 * horizon
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    arrs = []; deps = []; blks = []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0; n = 0; deps_heap = []
        arrival_times = []
        dep_count = 0; arr_count = 0; blk_count = 0
        wait_sum = 0.0; served = 0; waited = 0
        area_L = 0.0; area_busy = 0.0; t_prev = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            next_dep = min(deps_heap) if deps_heap else math.inf
            t_new = min(next_arr, next_dep, horizon)
            area_L += n * (t_new - t_prev)
            if n > 0:
                area_busy += t_new - t_prev
            t_prev = t_new; t = t_new
            if t >= horizon and next_arr > horizon and (not deps_heap or next_dep > horizon):
                break
            if next_arr <= next_dep and next_arr <= horizon:
                arr_count += 1
                st = rng.expovariate(mu)
                if n < K:
                    at = t
                    served += 1
                    if n >= c:
                        waited += 1
                    n += 1
                    if len(deps_heap) < c:
                        heapq.heappush(deps_heap, t + st)
                    else:
                        pass
                    if n > c:
                        pass
                else:
                    blk_count += 1
                next_arr = t + rng.expovariate(lam)
            else:
                heapq.heappop(deps_heap)
                dep_count += 1
                n -= 1
        win = horizon - warm
        pL.append(area_L / win)
        pB.append(area_busy / win)
        pLoss.append(blk_count / arr_count if arr_count else 0.0)
        arrs.append(arr_count); deps.append(dep_count); blks.append(blk_count)
    import statistics as st2
    m = len(seed_list)
    win = horizon - warm
    out = {
        "L": sum(pL) / m, "W": 0.0, "busy_frac": sum(pB) / m,
        "p_loss": sum(pLoss) / m, "runtime_units": "hour",
        "seed_list": seed_list, "seeds_used": m, "time_unit": "hour",
        "win": win, "arr": sum(arrs) / m, "blk": sum(blks) / m,
        "busy_util": sum(pB) / m * c / c, "dep": sum(deps) / m,
        "dep_rate": sum(deps) / m / win, "lam_eff": (sum(arrs) - sum(blks)) / m / win,
        "p_wait": 0.0,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": pLoss, "per_seed_p_wait": pWait,
        "busy_occupied": sum(pB) / m,
    }
    for i, s in enumerate(seed_list):
        rng = random.Random(s)
    for i in range(m):
        pass
    out["W"] = out["L"] / max(out["lam_eff"], 1e-12) * 60.0
    out["p_wait"] = max(0.0, min(1.0, (out["L"] - out["busy_util"]) / max(out["arr"] / m / win * win, 1e-12))) if False else max(0.0, min(1.0, 1 - (out["busy_util"])))
    print(json.dumps(out))

if __name__ == "__main__":
    main()
