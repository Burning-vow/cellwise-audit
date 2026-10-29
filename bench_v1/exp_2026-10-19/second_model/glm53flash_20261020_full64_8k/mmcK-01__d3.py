import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 6.0, 5.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    seeds_used, seed_list = 0, []
    per = {"L": [], "W": [], "busy_frac": [], "p_loss": [], "p_wait": []}
    tot = {"arr": 0, "blk": 0, "dep": 0, "L": 0.0, "busy_frac": 0.0, "busy_util": 0.0, "p_wait": 0.0}
    T0 = a.horizon * 0.25
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        events = [(rng.expovariate(lam), "arr")]
        n = 0
        in_svc = []
        waits, arrs, blks, deps = [], 0, 0, 0
        area_L, area_busy, area_occ, area_T = 0.0, 0.0, 0.0, 0.0
        t_prev = 0.0
        busy_time = 0.0
        def integr(now):
            nonlocal area_L, area_busy, area_occ, t_prev
            dt = now - t_prev
            if dt > 0:
                area_L += n * dt
                if n > 0: area_busy += dt
                area_occ += min(n, c) * dt
                t_prev = now
        while events:
            t, kind = heapq.heappop(events)
            if t > a.horizon: break
            integr(t)
            if kind == "arr":
                arrs += 1
                if n >= K:
                    blks += 1
                else:
                    st = rng.expovariate(mu)
                    waited = len(in_svc) >= c
                    if waited and t >= T0: waits.append(1)
                    if t >= T0 and not waited: waits.append(0)
                    in_svc.append((t, st))
                    n += 1
                heapq.heappush(events, (t + rng.expovariate(lam), "arr"))
            else:
                deps += 1
                n -= 1
                in_svc.pop(0)
            if n > 0 and not any(k == "dep" for _, k in events):
                pass
            nx = [e for e in events if e[1] == "dep"]
            if len(in_svc) > 0:
                for (at, st) in in_svc:
                    pass
        pass
    # restructure: redo simulation per seed cleanly
    per = {"L": [], "W": [], "busy_frac": [], "p_loss": [], "p_wait": []}
    tot = {"arr": 0, "blk": 0, "dep": 0, "L": 0.0, "busy_frac": 0.0, "busy_util": 0.0, "p_wait": 0.0}
    seeds_used = 0
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        dep_times = []
        n = 0
        waits, arrs, blks, deps = [], 0, 0, 0
        area_L = area_busy = area_occ = 0.0
        t_prev = 0.0
        while True:
            nd = min(dep_times) if dep_times else math.inf
            t = min(next_arr, nd)
            if t > a.horizon: break
            dt = t - t_prev
            area_L += n * dt
            if n > 0: area_busy += dt
            area_occ += min(n, c) * dt
            t_prev = t
            if next_arr <= nd:
                arrs += 1
                if n >= K: blks += 1
                else:
                    if len(dep_times) >= c: waits.append(1.0)
                    else: waits.append(0.0)
                    st = rng.expovariate(mu)
                    dep_times.append(t + st)
                    n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                deps += 1
                dep_times.remove(nd)
                n -= 1
        win = a.horizon - T0
        L = area_L / a.horizon
        bf = area_busy / a.horizon
        bu = area_occ / a.horizon / c
        pw = (sum(waits) / len(waits)) if waits else 0.0
        arrs_w = arrs * win / a.horizon
        blks_w = blks * win / a.horizon
        deps_w = deps * win / a.horizon
        W = L * a.horizon / deps / 1.0 if deps else 0.0
        W = L / (deps / a.horizon) * 60.0 if deps else 0.0
        pl = blks / arrs if arrs else 0.0
        per["L"].append(L); per["W"].append(W)
        per["busy_frac"].append(bf); per["p_loss"].append(pl); per["p_wait"].append(pw)
        tot["arr"] += arrs_w / win if win else 0
        tot["blk"] += blks_w / win if win else 0
        tot["dep"] += deps_w / win if win else 0
        tot["L"] += L; tot["busy_frac"] += bf; tot["busy_util"] += bu; tot["p_wait"] += pw
        seed_list.append(s); seeds_used += 1
    m = seeds_used if seeds_used else 1
    out = {
        "L": tot["L"]/m, "W": sum(per["W"])/m, "busy_frac": tot["busy_frac"]/m,
        "p_loss": sum(per["p_loss"])/m, "runtime_units": "hour", "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour", "win": a.horizon*0.75,
        "arr": tot["arr"], "blk": tot["blk"], "dep": tot["dep"],
        "dep_rate": tot["dep"], "lam_eff": tot["arr"]*(1-sum(per["p_loss"])/m),
        "p_wait": tot["p_wait"]/m, "busy_util": tot["busy_util"]/m, "busy_occupied": tot["busy_frac"]/m,
        "per_seed_L": per["L"], "per_seed_W": per["W"], "per_seed_busy_frac": per["busy_frac"],
        "per_seed_p_loss": per["p_loss"], "per_seed_p_wait": per["p_wait"]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
