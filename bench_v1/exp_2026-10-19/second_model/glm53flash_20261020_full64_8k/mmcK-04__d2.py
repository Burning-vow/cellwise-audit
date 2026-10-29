import argparse, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=8)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    S = int(a.seeds); H = float(a.horizon); S0 = int(a.seed_start)
    c, K = 2, 4
    lam, mu = 8.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    Tw = 0.25 * H
    acc = {"L": 0.0, "busy": 0.0, "util": 0.0, "arr": 0, "dep": 0, "blk": 0,
           "wait": 0.0, "nw": 0, "waited": 0}
    pL, pW, pB, pLoss, pPw = [], [], [], [], []
    seed_list = []
    for s in range(S0, S0 + S):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        in_srv = []          # [dep_time]
        queue = []           # customers: [arrive_t, wait, svc_time]
        prev_t = 0.0
        aL = aBusy = aUtil = 0.0
        nArr = nDep = nBlk = 0
        wSum = wN = waited = 0.0
        departed = True
        while t < H:
            t = next_arr
            if in_srv:
                t = min(t, min(in_srv))
            if t >= H:
                break
            if t >= Tw:
                dt = t - max(prev_t, Tw)
                aL += dt * (len(in_srv) + len(queue))
                aBusy += dt * (1.0 if (len(in_srv) + len(queue)) > 0 else 0.0)
                aUtil += dt * min(len(in_srv) + len(queue), c)
            prev_t = t
            if next_arr <= (min(in_srv) if in_srv else float("inf")):
                # arrival
                if t >= Tw: nArr += 1
                next_arr = t + rng.expovariate(lam)
                if len(in_srv) + len(queue) < K:
                    svc = rng.expovariate(mu)
                    if len(in_srv) < c:
                        if t >= Tw:
                            wSum += 0.0; wN += 1
                        in_srv.append(t + svc)
                    else:
                        queue.append([t, 0.0, svc])
                else:
                    if t >= Tw: nBlk += 1
            else:
                # departure
                in_srv.remove(t)
                if t >= Tw: nDep += 1
                if queue:
                    cust = queue.pop(0)
                    wt = t - cust[0]
                    if t >= Tw:
                        wSum += wt; wN += 1
                        if wt > 0: waited += 1
                    in_srv.append(t + cust[2])
        if wN > 0: pW.append(wSum / wN)
        else: pW.append(0.0)
        pL.append(aL / (H - Tw))
        pB.append(aBusy / (H - Tw))
        pLoss.append(nBlk / nArr if nArr > 0 else 0.0)
        pPw.append(waited / wN if wN > 0 else 0.0)
        acc["L"] += aL / (H - Tw); acc["busy"] += aBusy / (H - Tw)
        acc["util"] += aUtil / (H - Tw) / c
        acc["arr"] += nArr; acc["dep"] += nDep; acc["blk"] += nBlk
        acc["wait"] += wSum; acc["nw"] += wN; acc["waited"] += waited
    n = S
    L = acc["L"] / n
    W_min = (acc["wait"] / acc["nw"] if acc["nw"] > 0 else 0.0) * 60.0
    ploss = acc["blk"] / acc["arr"] if acc["arr"] > 0 else 0.0
    busy_frac = acc["busy"] / n
    busy_util = acc["util"] / n
    busy_occ = busy_frac
    pwait = acc["waited"] / acc["nw"] if acc["nw"] > 0 else 0.0
    dep_rate = acc["dep"] / n / (H - Tw)
    lam_eff = acc["arr"] / n / (H - Tw)
    out = {
        "L": L, "W": W_min, "busy_frac": busy_frac, "p_loss": ploss,
        "runtime_units": "event-driven discrete simulation, M/M/c/K (c=2,K=4), K changed to 5 for c_up",
        "seed_list": seed_list, "seeds_used": n, "time_unit": "hour",
        "win": H - Tw, "arr": acc["arr"] / n, "blk": acc["blk"] / n,
        "busy_util": busy_util, "busy_occupied": busy_occ, "dep": acc["dep"] / n,
        "dep_rate": dep_rate, "lam_eff": lam_eff, "p_wait": pwait,
        "per_seed_L": pL, "per_seed_W": [w * 60.0 for w in pW],
        "per_seed_busy_frac": pB, "per_seed_p_loss": pLoss,
        "per_seed_p_wait": pPw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
