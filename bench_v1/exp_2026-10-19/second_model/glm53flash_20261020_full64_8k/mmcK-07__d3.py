import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, cap = 8.0, 5.0, 3, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 4
    H = a.horizon
    T0 = 0.25 * H
    per = {k: [] for k in ("L","W","busy_frac","p_loss","p_wait")}
    seed_list, tot = [], {k:0.0 for k in ("arr","blk","dep","L","W","busy_frac","p_loss","p_wait","busy_util")}
    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        t = 0.0; n = 0; lanes = []; area = 0.0; area_busy0 = 0.0; area_util = 0.0
        st = {"arr":0,"blk":0,"dep":0,"wt":0.0,"nwait":0,"nserv":0,"nlost":0}
        while t < H:
            ta = t + rng.expovariate(lam)
            td = min(lanes) if lanes else math.inf
            t = min(ta, td, H)
            if t >= H: break
            area += n * (0 if t < T0 else (t - max(t, T0)))
            area_busy0 += (1 if n > 0 else 0) * (0 if t < T0 else (t - max(t, T0)))
            area_util += min(n, c) * (0 if t < T0 else (t - max(t, T0)))
            if ta <= td:
                t = ta
                if n < cap:
                    n += 1
                    st["arr"] += 1
                    st["nserv"] += 1
                    if n > c: st["nwait"] += 1
                    lanes.append(t + rng.expovariate(mu))
                else:
                    st["arr"] += 1; st["nlost"] += 1; st["blk"] += 1
            else:
                t = td
                lanes.remove(td)
                n -= 1
                st["dep"] += 1
        win = H - T0
        ns = st["nserv"]
        pw = st["nwait"] / ns if ns else 0.0
        pl = st["nlost"] / st["arr"] if st["arr"] else 0.0
        wv = st["wt"] / st["dep"] if st["dep"] else 0.0
        per["L"].append(area / win)
        per["busy_frac"].append(area_busy0 / win)
        per["p_loss"].append(pl)
        per["p_wait"].append(pw)
        per["W"].append(wv)
        tot["arr"] += st["arr"] / a.seeds; tot["dep"] += st["dep"] / a.seeds
        tot["blk"] += st["blk"] / a.seeds; tot["L"] += area / win / a.seeds
        tot["busy_frac"] += area_busy0 / win / a.seeds
        tot["busy_util"] += area_util / win / c / a.seeds
        tot["p_loss"] += pl / a.seeds; tot["p_wait"] += pw / a.seeds
        tot["W"] += wv / a.seeds
    out = {
        "time_unit": "hour", "runtime_units": "hour", "win": H - T0,
        "seed_list": seed_list, "seeds_used": a.seeds,
        "L": tot["L"], "W": tot["W"], "busy_frac": tot["busy_frac"],
        "p_loss": tot["p_loss"], "p_wait": tot["p_wait"],
        "busy_util": tot["busy_util"], "busy_occupied": tot["busy_frac"],
        "arr": tot["arr"], "blk": tot["blk"], "dep": tot["dep"],
        "dep_rate": tot["dep"] / (H - T0) if a.seeds else 0.0,
        "lam_eff": tot["arr"] / (H - T0),
        "per_seed_L": per["L"], "per_seed_W": per["W"],
        "per_seed_busy_frac": per["busy_frac"],
        "per_seed_p_loss": per["p_loss"], "per_seed_p_wait": per["p_wait"],
        "pert": a.pert,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
