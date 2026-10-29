import argparse, json, random, heapq, math

def run_seed(seed, lam, serv, c, H, warm):
    rnd = random.Random(seed)
    arrs = []
    t = 0.0
    while True:
        t += rnd.expovariate(lam)
        if t >= H:
            break
        arrs.append(t)
    n = len(arrs)
    i = 0
    heap = []
    q = []
    last = 0.0
    lastN = 0
    aN = 0.0
    aB = 0.0
    pN = 0.0
    pB = 0.0
    pre_t = min(warm, H)

    def add(t0, t1):
        nonlocal aN, aB, pN, pB
        if t1 <= t0:
            return
        dt = t1 - t0
        aN += lastN * dt
        aB += dt if lastN >= 1 else 0.0
        if t0 < pre_t:
            d = min(pre_t, t1) - t0
            pN += lastN * d
            pB += d if lastN >= 1 else 0.0

    done = []
    waits = []
    while i < n or heap:
        if heap:
            te = min(arrs[i] if i < n else math.inf, heap[0])
        else:
            te = arrs[i]
        add(last, te)
        last = te
        if i < n and arrs[i] <= te + 1e-12 and (not heap or arrs[i] <= heap[0]):
            a = arrs[i]
            i += 1
            if len(heap) < c:
                heapq.heappush(heap, a + serv)
                done.append((a + serv, a, False))
            else:
                q.append(a)
        else:
            heapq.heappop(heap)
            lastN -= 1
            if q:
                a = q.pop(0)
                heapq.heappush(heap, te + serv)
                done.append((te + serv, a, True))
        lastN = len(heap) + len(q)
    add(last, H)
    win = H - warm
    warr = [x for x in arrs if warm <= x < H]
    wd = [(d, a, w) for (d, a, w) in done if warm <= a < H and d <= H]
    aN_w = aN - pN
    aB_w = aB - pB
    L = aN_w / win
    W = sum(d - a for d, a, w in wd) / len(wd) if wd else 0.0
    bf = aB_w / win
    p_loss = 0.0
    p_wait = sum(1 for d, a, w in wd if w) / len(wd) if wd else 0.0
    return {"L": L, "W": W, "busy_frac": bf, "arr": float(len(warr)),
            "dep": float(len(wd)), "blk": 0.0, "p_loss": p_loss, "p_wait": p_wait}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()
    H = float(args.horizon)
    lam = 6.0
    serv = 6.0 / 60.0
    c = 1
    if args.pert == "lam_up":
        lam *= 1.2
    elif args.pert == "mu_up":
        serv /= 1.2
    elif args.pert == "c_up":
        c = 2
    warm = 0.25 * H
    win = H - warm
    seed_list = [args.seed_start + k for k in range(args.seeds)]
    rs = [run_seed(s, lam, serv, c, H, warm) for s in seed_list]
    m = len(rs)
    agg = lambda k: sum(r[k] for r in rs) / m
    out = {
        "L": agg("L"), "W": agg("W"), "busy_frac": agg("busy_frac"),
        "runtime_units": H, "seed_list": seed_list, "seeds_used": m,
        "time_unit": "hour", "win": win,
        "arr": agg("arr"), "dep": agg("dep"), "blk": agg("blk"),
        "busy_util": agg("busy_frac"), "busy_occupied": agg("busy_frac"),
        "dep_rate": agg("dep") / win, "lam_eff": agg("arr") / win,
        "p_loss": agg("p_loss"), "p_wait": agg("p_wait"),
        "per_seed_L": [r["L"] for r in rs],
        "per_seed_W": [r["W"] for r in rs],
        "per_seed_busy_frac": [r["busy_frac"] for r in rs],
        "per_seed_p_loss": [r["p_loss"] for r in rs],
        "per_seed_p_wait": [r["p_wait"] for r in rs],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
