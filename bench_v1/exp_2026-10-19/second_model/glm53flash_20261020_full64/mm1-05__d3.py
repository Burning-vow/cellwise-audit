import argparse, json, heapq, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    lam, mu = 7.0, 10.0
    if pert == "lam_up": lam *= 1.1
    if pert == "mu_up": mu *= 1.1
    if pert == "c_up": pass
    warm = H * 0.25
    win = H - warm
    res_L, res_W, res_bf, res_pw, res_pl = [], [], [], [], []
    used = []
    total_arr = total_dep = total_blk = 0.0
    for k in range(seeds):
        seed = S + k
        used.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0.0
        area = 0.0
        wsum = 0.0
        ncomp = 0
        nwait = 0
        narr = 0
        ndep = 0
        nblk = 0
        last = 0.0
        t_next_arr = rng.expovariate(lam)
        t_next_dep = math.inf
        while True:
            if t_next_arr <= t_next_dep and t_next_arr <= H:
                t = t_next_arr
                if t >= warm:
                    area += n * (t - last); busy += (1 if n > 0 else 0) * (t - last)
                    narr += 1
                last = t
                svc = rng.expovariate(mu)
                if n == 0:
                    t_next_dep = t + svc
                n += 1
                cust = {"arr": t, "svc": svc}
                if n == 1:
                    cust_serving = cust
                else:
                    queue.append(cust)
                t_next_arr = t + rng.expovariate(lam)
            elif t_next_dep <= H:
                t = t_next_dep
                if t >= warm:
                    area += n * (t - last); busy += (1 if n > 0 else 0) * (t - last)
                    ndep += 1
                    wsum += (t - cust_serving["arr"]); ncomp += 1
                    if t - cust_serving["arr"] > cust_serving["svc"] - 1e-12 and (t - cust_serving["arr"]) != cust_serving["svc"]:
                        pass
                last = t
                n -= 1
                if queue:
                    cust_serving = queue.pop(0)
                    t_next_dep = t + cust_serving["svc"]
                else:
                    t_next_dep = math.inf
            else:
                t = H
                if H >= warm:
                    area += n * (t - last); busy += (1 if n > 0 else 0) * (t - last)
                break
        res_L.append(area / win)
        res_W.append((wsum / ncomp) * 60.0 if ncomp else 0.0)
        res_bf.append(busy / win)
        res_pl.append(0.0)
        total_arr += narr; total_dep += ndep; total_blk += nblk
    # p_wait: recompute per seed needs waiting flag; do second pass-lite via stored? approximate by W>svc fraction -> recompute properly
    # redo p_wait properly: rerun quickly
    per_pw = []
    for k in range(seeds):
        seed = S + k
        rng = random.Random(seed)
        t = 0.0; n = 0; t_na = rng.expovariate(lam); t_nd = math.inf
        nw = nc = 0; queue = []
        while True:
            if t_na <= t_nd and t_na <= H:
                t = t_na; svc = rng.expovariate(mu)
                if n == 0:
                    t_nd = t + svc; cur = {"arr": t, "svc": svc, "waited": False}
                else:
                    queue.append({"arr": t, "svc": svc, "waited": True})
                n += 1
                t_na = t + rng.expovariate(lam)
            elif t_nd <= H:
                t = t_nd
                if t >= warm and cur["waited"]: nw += 1
                if t >= warm: nc += 1
                n -= 1
                if queue:
                    cur = queue.pop(0); t_nd = t + cur["svc"]
                else:
                    t_nd = math.inf
            else:
                break
        per_pw.append(nw / nc if nc else 0.0)
    out = {
        "L": sum(res_L) / seeds,
        "W": sum(res_W) / seeds,
        "busy_frac": sum(res_bf) / seeds,
        "p_wait": sum(per_pw) / seeds,
        "runtime_units": seeds,
        "seed_list": used,
        "seeds_used": seeds,
        "time_unit": "hour",
        "win": win,
        "arr": total_arr / seeds,
        "dep": total_dep / seeds,
        "blk": total_blk / seeds,
        "busy_util": sum(res_bf) / seeds,
        "busy_occupied": sum(res_bf) / seeds,
        "dep_rate": (total_dep / seeds) / win,
        "lam_eff": (total_dep / seeds) / win,
        "p_loss": 0.0,
        "per_seed_L": res_L,
        "per_seed_W": res_W,
        "per_seed_busy_frac": res_bf,
        "per_seed_p_loss": [0.0] * seeds,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
