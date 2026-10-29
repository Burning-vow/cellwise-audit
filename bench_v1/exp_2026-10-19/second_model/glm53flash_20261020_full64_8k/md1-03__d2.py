import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    ns = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 6.0; svc = 6.0 / 60.0
    if a.pert == "lam_up": lam *= 1.2
    elif a.pert == "mu_up": svc *= 0.8
    elif a.pert == "c_up": svc *= 0.5
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot = dict(L=0.0, W=0.0, bf=0.0, pl=0.0, pw=0.0, arr=0, dep=0, blk=0)
    for k in range(ns):
        sd = S + k
        seed_list.append(sd)
        rng = random.Random(sd)
        t = 0.0; ta = rng.expovariate(lam); tdep = math.inf
        queue = []; N = 0; tprev = 0.0
        areaN = 0.0; areaB = 0.0
        arr = dep = blk = waited = 0
        sumW = 0.0
        while tprev < H or queue or tdep < H:
            t = min(ta, tdep)
            if t > H:
                t = H
            if t > warm:
                dt = min(t, H) - max(tprev, warm)
                if dt > 0:
                    areaN += N * dt
                    if N > 0: areaB += dt
            if t >= H: break
            if ta <= tdep:
                t = ta
                svc_i = svc
                cust = {"arr": t, "svc": svc_i}
                arr += 1
                if N == 0:
                    N = 1
                    tdep = t + svc_i
                else:
                    waited += 1
                    queue.append(cust)
                    N += 1
                ta = t + rng.expovariate(lam)
            else:
                t = tdep
                dep += 1
                sumW += t - queue[0]["arr"] if queue else 0.0
                if queue:
                    c = queue.pop(0)
                    sumW += t - c["arr"]
                else:
                    sumW += 0.0
                N -= 1
                if queue:
                    c2 = queue[0]
                    tdep = t + c2["svc"]
                else:
                    tdep = math.inf
                    N = 0
            tprev = t
        win = H - warm
        L = areaN / win
        bf = areaB / win
        W = (sumW / dep) * 60.0 if dep else 0.0
        pl = 0.0
        pw = waited / arr if arr else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf); per_pl.append(pl); per_pw.append(pw)
        tot["L"] += L; tot["W"] += W; tot["bf"] += bf; tot["pl"] += pl; tot["pw"] += pw
        tot["arr"] += arr; tot["dep"] += dep; tot["blk"] += blk
    m = ns
    out = {
        "L": tot["L"] / m, "W": tot["W"] / m, "busy_frac": tot["bf"] / m,
        "busy_util": tot["bf"] / m, "busy_occupied": tot["bf"] / m,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": ns,
        "time_unit": "hour", "win": H - warm,
        "arr": tot["arr"] / m, "blk": tot["blk"] / m,
        "dep": tot["dep"] / m, "dep_rate": tot["dep"] / m / (H - warm),
        "lam_eff": tot["dep"] / m / (H - warm),
        "p_loss": tot["pl"] / m, "p_wait": tot["pw"] / m,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
