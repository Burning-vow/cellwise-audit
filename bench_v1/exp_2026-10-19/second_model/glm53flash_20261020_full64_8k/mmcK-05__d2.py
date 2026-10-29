import argparse, heapq, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    c = 3; K = 4
    lam = 6.0; mu = 5.0  # per hour, mean service 12 min
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    t_unit = "hour"
    burn = a.horizon * 0.25
    per = {k: [] for k in ["L", "W", "busy_frac", "p_loss", "p_wait"]}
    seed_list = []
    agg = {k: 0.0 for k in ["arr", "blk", "dep", "areaL", "areaB", "areaBusy", "wait", "nwait"]}
    for si in range(a.seeds):
        seed = a.seed_start + si
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        state = 0  # cars in station
        busy_occ = 0.0; areaL = 0.0; areaB = 0.0; areaBusy = 0.0
        arr = blk = dep = 0
        wsum = 0.0; nwait = 0
        # event list: (time, kind, idx)
        ev = []
        nctr = 0
        heapq.heappush(ev, (rng.expovariate(lam), "arr", 0))
        nctr += 1
        pend = {}  # idx -> (arrive_time, service_time, in_service bool)
        def schedule_next_arr(now):
            nonlocal nctr
            heapq.heappush(ev, (now + rng.expovariate(lam), "arr", nctr))
            nctr += 1
        def try_start(now, idx, svc):
            nonlocal state
            pend[idx] = (now, svc, True)
            heapq.heappush(ev, (now + svc, "dep", idx))
            state += 1
        while True:
            tt, kind, idx = heapq.heappop(ev)
            if tt > a.horizon: break
            # integrate before state change
            dt = tt - t
            if tt > burn:
                w = tt - max(t, burn)
                if w > 0:
                    areaL += state * w
                    areaB += w if state > 0 else 0.0
                    areaBusy += min(state, c) * w
            t = tt
            if kind == "arr":
                schedule_next_arr(t)
                if tt > burn: arr += 1
                if state >= K:
                    if tt > burn: blk += 1
                else:
                    svc = rng.expovariate(mu)
                    inS = state < c
                    if inS:
                        if state > 0:
                            if tt > burn: wsum += 0.0; nwait += 1
                        try_start(t, idx, svc)
                    else:
                        pend[idx] = (t, svc, False)
            else:
                at, svc, inS = pend.pop(idx)
                dep += 1
                state -= 1
                if not inS:
                    if tt > burn:
                        wsum += t - at; nwait += 1
                # pull from queue: waiting cars
                for j in list(pend.keys()):
                    aj, sj, inSj = pend[j]
                    if not inSj and state < c:
                        try_start(t, j, sj)
                        break
        wlen = a.horizon - burn
        if wlen <= 0: wlen = 1.0
        Lq = areaL / wlen
        busyF = areaB / wlen
        busyU = areaBusy / wlen / c
        pl = blk / arr if arr else 0.0
        pw = wsum / nwait if nwait else 0.0
        Wm = (pw * 60.0) if nwait else 0.0
        per["L"].append(Lq); per["W"].append(Wm)
        per["busy_frac"].append(busyF); per["p_loss"].append(pl)
        per["p_wait"].append(pw)
        agg["arr"] += arr / wlen; agg["blk"] += blk / wlen; agg["dep"] += dep / wlen
        agg["areaL"] += Lq; agg["areaB"] += busyF; agg["areaBusy"] += busyU
        agg["wait"] += pw; agg["nwait"] += 1
    n = max(1, a.seeds)
    L = agg["areaL"] / n
    busy_frac = agg["areaB"] / n
    busy_util = agg["areaBusy"] / n
    p_loss = agg["blk"] / agg["arr"] if agg["arr"] else 0.0
    p_wait = agg["wait"] / n
    W = p_wait * 60.0
    arr = agg["arr"]; blk = agg["blk"]; dep = agg["dep"]
    out = {
        "L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
        "busy_util": busy_util, "busy_occupied": busy_frac,
        "runtime_units": t_unit, "time_unit": t_unit,
        "seed_list": seed_list, "seeds_used": a.seeds,
        "win": a.horizon * 0.75,
        "arr": arr, "blk": blk, "dep": dep,
        "dep_rate": dep, "lam_eff": arr,
        "p_wait": p_wait,
        "per_seed_L": per["L"], "per_seed_W": per["W"],
        "per_seed_busy_frac": per["busy_frac"],
        "per_seed_p_loss": per["p_loss"],
        "per_seed_p_wait": per["p_wait"],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
