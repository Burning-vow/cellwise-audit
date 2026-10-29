import argparse, json, heapq, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, c, K = 8.0, 5.0, 3, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25 * H
    seed_list, pL, pW, pB, pP, pPW = [], [], [], [], [], []
    tot = dict(L=0.0, W=0.0, bf=0.0, pl=0.0, pw=0.0, arr=0.0, dep=0.0, blk=0.0, bu=0.0)
    for si in range(n_seeds):
        seed = S + si
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        deps = []
        n = 0
        area_n = 0.0; area_busy = 0.0; area_occ = 0.0
        arr = dep = blk = served = waited = 0
        wsum = 0.0
        last = 0.0
        while t < H:
            nd = deps[0] if deps else math.inf
            t2 = min(next_arr, nd)
            if t2 > H: t2 = H
            if t2 >= warm:
                area_n += n * (t2 - max(t, warm))
                area_busy += (1.0 if n > 0 else 0.0) * (t2 - max(t, warm))
                area_occ += min(n, c) * (t2 - max(t, warm))
            t = t2
            if t >= H: break
            if next_arr <= nd:
                arr += 1
                st = rng.expovariate(mu)
                if n < K:
                    waited_here = 1 if n >= c else 0
                    if t >= warm and waited_here: waited += 1
                    start = max(t, deps[0]) if deps else t
                    if t >= warm:
                        wsum += start - t
                    heapq.heappush(deps, start + st)
                    n += 1
                else:
                    if t >= warm: blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                heapq.heappop(deps)
                n -= 1
                dep += 1
                if t >= warm: served += 1
        win = H - warm
        L = area_n / win
        bf = area_busy / win
        bu = area_occ / (win * c)
        p_loss = blk / arr if arr else 0.0
        p_wait = waited / arr if arr else 0.0
        W = (wsum / arr) * 60.0 if arr else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pP.append(p_loss); pPW.append(p_wait)
        tot["L"] += L; tot["W"] += W; tot["bf"] += bf; tot["pl"] += p_loss
        tot["pw"] += p_wait; tot["arr"] += arr / win; tot["dep"] += dep / win
        tot["blk"] += blk / win; tot["bu"] += bu
    m = n_seeds
    lam_eff = tot["dep"] / m
    out = {
        "L": tot["L"] / m, "W": tot["W"] / m,
        "busy_frac": tot["bf"] / m, "busy_occupied": tot["bf"] / m,
        "p_loss": tot["pl"] / m, "p_wait": tot["pw"] / m,
        "runtime_units": H, "time_unit": "hour", "win": H - warm,
        "seed_list": seed_list, "seeds_used": m,
        "arr": tot["arr"] / m, "dep": tot["dep"] / m, "blk": tot["blk"] / m,
        "dep_rate": lam_eff, "lam_eff": lam_eff, "busy_util": tot["bu"] / m,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": pP, "per_seed_p_wait": pPW,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
