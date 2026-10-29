import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu1, mu2 = 6.0, 10.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up": mu1 *= 0.9; mu2 *= 0.9
    warm = 0.25 * H
    res = {"L": [], "W": [], "busy": [], "arr": [], "dep": [], "pwait": []}
    seed_list = []
    for k in range(nseeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0; ev = []
        heapq.heappush(ev, (rng.expovariate(lam), 0, 0))
        q1 = []; q2 = []; s1 = None; s2 = None
        area = 0.0; busy_area = 0.0; last = 0.0
        arr_c = 0; dep_c = 0; w_sum = 0.0; w_n = 0; waited = 0; left_c = 0
        def integrate(tn):
            nonlocal area, busy_area, last
            if tn > last and tn > warm:
                lo = max(last, warm)
                n_sys = len(q1) + len(q2) + (1 if s1 else 0) + (1 if s2 else 0)
                nb = (1 if s1 else 0) + (1 if s2 else 0)
                area += n_sys * (tn - lo)
                busy_area += nb * (tn - lo)
            last = max(last, tn)
        while t < H:
            t, _, _ = heapq.heappop(ev)
            integrate(t)
            if t > H: break
            if t < H:
                heapq.heappush(ev, (t + rng.expovariate(lam), 0, 0))
        # simulate properly (redo loop body)
        pass
        # event handling
        heapq2 = ev
        # rebuild: simplest to re-run with correct structure
        # --- actual simulation below ---
        t = 0.0; ev = [(rng.expovariate(lam), 0)]
        heapq.heapify(ev)
        q1 = []; q2 = []; s1 = None; s2 = None
        area = 0.0; busy_area = 0.0; last = 0.0
        arr_c = 0; dep_c = 0; w_sum = 0.0; w_n = 0; waited = 0
        rng2 = random.Random(seed)
        ev = []
        heapq.heappush(ev, (rng2.expovariate(lam), 0, None))
        while ev:
            t, typ, info = heapq.heappop(ev)
            if t > H: break
            integrate(t)
            if typ == 0:
                arr_c += 1
                heapq.heappush(ev, (t + rng2.expovariate(lam), 0, None))
                svc1 = rng2.expovariate(mu1); svc2 = rng2.expovariate(mu2)
                job = {"a": t, "s1": svc1, "s2": svc2}
                if s1 is None:
                    s1 = (t + svc1, job)
                    heapq.heappush(ev, (t + svc1, 1, job))
                else:
                    q1.append(job); waited += 1
            elif typ == 1:
                s1 = None
                if q1:
                    j = q1.pop(0)
                    s1 = (t + j["s1"], j)
                    heapq.heappush(ev, (t + j["s1"], 1, j))
                if s2 is None:
                    s2 = (t + info["s2"], info)
                    heapq.heappush(ev, (t + info["s2"], 2, info))
                else:
                    q2.append(info)
            else:
                s2 = None
                if q2:
                    j = q2.pop(0)
                    s2 = (t + j["s2"], j)
                    heapq.heappush(ev, (t + j["s2"], 2, j))
                if t > warm:
                    dep_c += 1; w_sum += t - info["a"]; w_n += 1
        win = H - warm
        res["L"].append(area / win)
        res["W"].append(w_sum / w_n if w_n else 0.0)
        res["busy"].append(busy_area / win / 2.0)
        res["arr"].append(arr_c / (nseeds and 1) / win * 1.0)
        res["dep"].append(dep_c)
        res["pwait"].append(waited / arr_c if arr_c else 0.0)
        # accumulate per-seed counts of arrivals in window roughly arr_c*win/H
    # fix arr: arrivals in window approx arr_c (total); scale
    win = H - warm
    out = {
        "L": sum(res["L"]) / nseeds,
        "W": sum(res["W"]) / nseeds,
        "runtime_units": 1,
        "seed_list": seed_list,
        "seeds_used": nseeds,
        "time_unit": "hour",
        "win": win,
        "arr": sum(res["arr"]) / nseeds,
        "blk": 0.0,
        "busy_frac": sum(res["busy"]) / nseeds,
        "busy_util": sum(res["busy"]) / nseeds,
        "dep": sum(res["dep"]) / nseeds / win * (H / win),
        "dep_rate": sum(res["dep"]) / nseeds / win,
        "lam_eff": lam,
        "p_loss": 0.0,
        "p_wait": sum(res["pwait"]) / nseeds,
        "per_seed_L": res["L"],
        "per_seed_W": res["W"],
        "per_seed_busy_frac": res["busy"],
        "per_seed_p_loss": [0.0] * nseeds,
        "per_seed_p_wait": res["pwait"],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
