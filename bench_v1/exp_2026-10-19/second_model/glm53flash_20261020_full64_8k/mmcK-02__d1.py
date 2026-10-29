import argparse, heapq, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 6.0, 10.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    t0 = 0.25 * a.horizon
    per = []
    seeds_used = 0
    seed_list = []
    agg = {"L": 0.0, "W": 0.0, "busy": 0.0, "p_loss": 0.0, "p_wait": 0.0,
           "arr": 0.0, "dep": 0.0, "blk": 0.0, "util": 0.0}
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s); seeds_used += 1
        t = 0.0; n = 0; busy_srv = 0
        ev = []
        nid = 0
        first = -math.log(1.0 - rng.random()) / lam
        heapq.heappush(ev, (first, 0, nid)); nid += 1
        area_L = area_busy = area_util = 0.0
        last = 0.0
        arr = dep = blk = waits = 0
        win_started = False
        pend = []  # arrival times in window awaiting departure, but we need sojourn at departure
        # store arrival time per customer
        atime = {}
        sojourns = []
        done = False
        while not done:
            if not ev: break
            t, kind, cid = heapq.heappop(ev)
            if t > a.horizon:
                t = a.horizon
                done = True
            inwin = t >= t0
            # integrate before state change
            area_L += n * (t - last)
            b = 1.0 if n > 0 else 0.0
            area_busy += b * (t - last)
            u = min(n, c)
            area_util += u * (t - last)
            last = t
            if done: break
            if kind == 0:  # arrival
                if inwin: arr += 1
                dt = -math.log(1.0 - rng.random()) / lam
                heapq.heappush(ev, (t + dt, 0, nid)); nid += 1
                st = -math.log(1.0 - rng.random()) / mu  # service time drawn at arrival
                atime[cid] = t
                if n < c:
                    n += 1; busy_srv += 1
                    heapq.heappush(ev, (t + st, 1, cid))
                elif n < K:
                    n += 1
                    # queue: need to schedule start when server frees; simulate queue properly
                    # store pending start: find when a server frees -> handle at departure
                    q.append((cid, st))
                else:
                    if inwin: blk += 1
                    del atime[cid]
            elif kind == 1:  # departure
                if inwin:
                    dep += 1
                    sojourns.append(t - atime[cid])
                    del atime[cid]
                n -= 1
                if q:
                    c2, st2 = q.pop(0)
                    heapq.heappush(ev, (t + st2, 1, c2))
                    if inwin: waits += 1
            # noqa
        # fix: q must be defined before loop
        win = a.horizon - t0
        if dep > 0:
            W = sum(sojourns) / len(sojourns)
        else:
            W = 0.0
        L = area_L / win
        busy_occ = area_busy / win
        p_loss = blk / arr if arr > 0 else 0.0
        p_wait = waits / dep if dep > 0 else 0.0
        util = area_util / (c * win)
        per.append({"L": L, "W": W, "busy": busy_occ, "p_loss": p_loss,
                    "p_wait": p_wait, "arr": arr, "dep": dep, "blk": blk, "util": util})
        agg["L"] += L; agg["W"] += W; agg["busy"] += busy_occ
        agg["p_loss"] += p_loss; agg["p_wait"] += p_wait
        agg["arr"] += arr; agg["dep"] += dep; agg["blk"] += blk; agg["util"] += util
    n = seeds_used
    Lm = agg["L"] / n; Wm = agg["W"] / n; busym = agg["busy"] / n
    pl = agg["p_loss"] / n; pw = agg["p_wait"] / n
    arrm = agg["arr"] / n; depm = agg["dep"] / n; blkm = agg["blk"] / n
    util = agg["util"] / n
    out = {
        "L": Lm, "W": Wm, "busy_frac": busym, "p_loss": pl,
        "runtime_units": "hours", "seed_list": seed_list, "seeds_used": n,
        "time_unit": "hour", "win": a.horizon - 0.25 * a.horizon,
        "arr": arrm, "blk": blkm, "busy_util": util, "busy_occupied": busym,
        "dep": depm, "dep_rate": depm / (a.horizon - 0.25 * a.horizon),
        "lam_eff": arrm / (a.horizon - 0.25 * a.horizon),
        "p_wait": pw,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy"] for p in per],
        "per_seed_p_loss": [p["p_loss"] for p in per],
        "per_seed_p_wait": [p["p_wait"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
