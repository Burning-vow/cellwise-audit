import argparse, json, math, random, heapq

def run_seed(seed, lam, mu, c, H, W0):
    rng = random.Random(seed)
    t = 0.0
    k = 0
    q = []
    heap = []
    cnt = 0
    next_arr = rng.expovariate(lam)
    if next_arr <= H:
        heapq.heappush(heap, (next_arr, 0, cnt)); cnt += 1
    last = 0.0
    aN = aM = aO = 0.0
    arr_n = dep_n = wait_hits = 0
    wsum = 0.0
    wcnt = 0
    def integ(t1):
        nonlocal last, aN, aM, aO
        lo = max(last, W0); hi = min(t1, H)
        if hi > lo:
            seg = hi - lo
            aN += k * seg
            aM += min(k, c) * seg
            aO += (1.0 if k > 0 else 0.0) * seg
        last = t1
    while heap:
        te, typ, _ = heapq.heappop(heap)
        if te > H:
            break
        integ(te)
        t = te
        if typ == 0:
            if t >= W0:
                arr_n += 1
                if k == c:
                    wait_hits += 1
            svc = rng.expovariate(mu)
            if k < c:
                k += 1
                if t >= W0:
                    wcnt += 1
                heapq.heappush(heap, (t + svc, 1, cnt)); cnt += 1
            else:
                q.append((t, svc))
            na = t + rng.expovariate(lam)
            if na <= H:
                heapq.heappush(heap, (na, 0, cnt)); cnt += 1
        else:
            k -= 1
            if t >= W0:
                dep_n += 1
            if q:
                at, svc = q.pop(0)
                if t >= W0:
                    wsum += t - at
                    wcnt += 1
                heapq.heappush(heap, (t + svc, 1, cnt)); cnt += 1
            else:
                k += 0
        t = te
    if last < H:
        integ(H)
    win = H - W0
    L = aN / win
    W = (wsum / wcnt) * 60.0 if wcnt > 0 else 0.0
    busy_frac = aM / c / win
    p_wait = wait_hits / arr_n if arr_n > 0 else 0.0
    p_loss = 0.0
    return L, W, busy_frac, p_wait, p_loss, aO / win, arr_n, dep_n, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds)
    H = float(a.horizon)
    S = int(a.seed_start)
    lam, mu, c = 8.0, 5.0, 3.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c += 1
    W0 = 0.25 * H
    res = [run_seed(s, lam, mu, c, H, W0) for s in range(S, S + n_seeds)]
    win = res[0][8]
    seeds_used = len(res)
    seed_list = [s for s in range(S, S + n_seeds)]
    avg = lambda i: sum(r[i] for r in res) / seeds_used
    out = {
        "L": avg(0), "W": avg(1), "busy_frac": avg(2), "p_wait": avg(3),
        "runtime_units": "event", "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "hour", "win": win,
        "arr": avg(6) / win, "blk": 0.0, "busy_util": avg(2),
        "busy_occupied": avg(5), "dep": avg(7) / win,
        "dep_rate": avg(7) / win, "lam_eff": avg(6) / win,
        "p_loss": avg(4),
        "per_seed_L": [r[0] for r in res],
        "per_seed_W": [r[1] for r in res],
        "per_seed_busy_frac": [r[2] for r in res],
        "per_seed_p_loss": [r[4] for r in res],
        "per_seed_p_wait": [r[3] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
