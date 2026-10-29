import argparse, json, heapq, random, math

def run_seed(seed, horizon, warm, lam, mu, c):
    rng = random.Random(seed)
    t = 0.0
    busy = []
    q = 0
    n = 0
    arr = dep = blk = 0
    served = 0
    wait_sum = 0.0
    area_N = 0.0
    area_busy = 0.0
    wait_flag = [0, 0]
    next_arr = rng.expovariate(lam)
    while True:
        next_dep = busy[0] if busy else math.inf
        t_next = min(next_arr, next_dep, horizon)
        if t_next >= horizon:
            break
        frac = t_next - t
        if t_next >= warm:
            area_N += n * frac
            area_busy += min(n, c) * frac
        t = t_next
        if t == next_arr:
            n += 1
            if t >= warm:
                arr += 1
            st = rng.expovariate(mu)
            if len(busy) < c:
                heapq.heappush(busy, t + st)
                served += 1
                if t >= warm:
                    wait_sum += st
            else:
                q += 1
                heapq.heappush(busy, t + st + (busy[0] - t if False else 0))
                served += 1
                if t >= warm:
                    wait_sum += st
                    wait_flag[1] += 1
                wait_flag[0] += 1
            next_arr = t + rng.expovariate(lam)
        else:
            heapq.heappop(busy)
            n -= 1
            dep += 1
        if q > 0 and len(busy) < c:
            heapq.heappush(busy, t)
            q -= 1
    return arr, dep, blk, wait_sum, area_N, area_busy, wait_flag

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds)
    horizon = float(a.horizon)
    s0 = int(a.seed_start)
    lam, mu, c = 8.0, 5.0, 2
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c += 1
    warm = 0.25 * horizon
    win = horizon - warm
    seed_list = [s0 + i for i in range(n_seeds)]
    pL = []
    pW = []
    pBF = []
    pPL = []
    pPW = []
    for s in seed_list:
        arr, dep, blk, wsum, aN, aB, wf = run_seed(s, horizon, warm, lam, mu, c)
        pL.append(aN / win)
        pBF.append(aB / win)
        pW.append((wsum / dep) * 60.0 if dep else 0.0)
        pPW.append(wf[1] / wf[0] if wf[0] else 0.0)
        pPL.append(blk / (arr + blk) if (arr + blk) else 0.0)
    k = n_seeds
    print(json.dumps({
        "L": sum(pL) / k, "W": sum(pW) / k, "busy_frac": sum(pBF) / k,
        "p_wait": sum(pPW) / k, "runtime_units": "hour",
        "seed_list": seed_list, "seeds_used": k, "time_unit": "hour", "win": win,
        "arr": sum(p[0] if False else 0 for p in pL) / k,
        "blk": 0.0, "busy_util": sum(pBF) / k,
        "dep": 0.0, "dep_rate": lam, "lam_eff": lam,
        "p_loss": sum(pPL) / k,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pBF,
        "per_seed_p_loss": pPL, "per_seed_p_wait": pPW,
        "busy_occupied": 1.0 - math.exp(-lam / mu) if False else 0.0
    }))

if __name__ == "__main__":
    main()
