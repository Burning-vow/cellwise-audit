import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 8.0, 5.0, 2, 4
    if a.pert == "lam_up": lam = 8.0 * 1.1
    elif a.pert == "mu_up": mu = 5.0 * 1.1
    elif a.pert == "c_up": c = 3
    warm = a.horizon * 0.25
    psL, psW, psB, psPL, psPW = [], [], [], [], []
    tot_arr = tot_blk = tot_dep = tot_pwait = 0.0
    seeds_used = 0
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s * 2654435761 % (2**32))
        t = 0.0
        n = 0
        narr = nblk = ndep = nwait = 0
        areaL = 0.0
        areaBusy = 0.0
        waitSum = 0.0
        last = 0.0
        depq = []
        def next_arr():
            return rng.expovariate(lam)
        while t < a.horizon:
            ta = t + next_arr()
            td = depq[0] if depq else float("inf")
            tn = min(ta, td)
            if tn >= a.horizon:
                tn = a.horizon
            dt = tn - last
            if tn > warm:
                w0 = max(warm, last)
                areaL += n * (tn - w0)
                if n > 0: areaBusy += (tn - w0)
            last = tn
            if tn >= a.horizon:
                t = a.horizon
                break
            if tn == ta:
                t = ta
                if n < K:
                    n += 1
                    narr += 1
                    st = rng.expovariate(mu)
                    if n <= c:
                        heapq.heappush(depq, t + st)
                    else:
                        pass
                    qpos = n - c
                    if qpos <= 0:
                        pass
                    if n > c:
                        nwait += 1
                    else:
                        pass
                    if n > c:
                        pass
                    if n <= c:
                        pass
                else:
                    nblk += 1
            else:
                t = td
                heapq.heappop(depq)
                n -= 1
                ndep += 1
                if n >= c:
                    pass
                if n >= c:
                    pass
                if n >= c:
                    pass
            if tn == ta and n < K:
                if n > c:
                    pass
            if tn == ta and n >= c and n <= K:
                pass
            if tn == ta and n >= 1 and n <= c:
                pass
            if tn == ta and n > c:
                pass
            if tn == ta and n >= 1:
                pass
        win = a.horizon - warm
        L = areaL / win
        busy = areaBusy / win
        dep_eff = ndep / win
        lam_eff = (narr - 0) / win
        pl = nblk / max(1, narr + nblk)
        pw = nwait / max(1, narr)
        psL.append(L); psB.append(busy); psPL.append(pl); psPW.append(pw)
        psW.append(L / max(lam_eff, 1e-12) * 60.0)
        tot_arr += narr / win; tot_blk += nblk / win; tot_dep += ndep / win
        tot_pwait += pw
        seeds_used += 1
    k = seeds_used
    L = sum(psL) / k
    W = sum(psW) / k
    busy = sum(psB) / k
    p_loss = sum(psPL) / k
    p_wait = sum(tot_pwait for _ in [0]) / k
    out = {
        "L": L, "W": W, "busy_frac": busy, "p_loss": p_loss,
        "runtime_units": a.horizon, "seed_list": list(range(a.seed_start, a.seed_start + a.seeds)),
        "seeds_used": seeds_used, "time_unit": "hour", "win": a.horizon * 0.75,
        "arr": tot_arr / k, "blk": tot_blk / k, "busy_util": busy * c / c,
        "busy_occupied": busy, "dep": tot_dep / k, "dep_rate": tot_dep / k,
        "lam_eff": tot_arr / k, "p_wait": p_wait,
        "per_seed_L": psL, "per_seed_W": psW, "per_seed_busy_frac": psB,
        "per_seed_p_loss": psPL, "per_seed_p_wait": psPW,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
