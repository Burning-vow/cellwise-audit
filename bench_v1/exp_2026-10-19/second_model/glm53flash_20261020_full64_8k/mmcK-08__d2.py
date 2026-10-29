import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    c, K = 3, 4
    lam, mu = 8.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1

    horizon = a.horizon
    warm = 0.25 * horizon
    win = horizon - warm

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_blk = tot_dep = tot_busy = tot_area = tot_wait = tot_nwait = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        n = 0
        in_win = False
        area = busy = 0.0
        arr = blk = dep = nwait = ntot = 0
        waits = []
        depq = []
        while t < horizon:
            ta = t + rng.expovariate(lam)
            td = depq[0] if depq else math.inf
            t2 = min(ta, td)
            if t2 >= horizon:
                area += n * (horizon - t)
                if t >= warm: busy += (1 if n > 0 else 0) * (horizon - t)
                t = horizon
                break
            if t >= warm:
                area += n * (t2 - t)
                busy += (1 if n > 0 else 0) * (t2 - t)
            if ta <= td:
                t = ta
                if t >= warm: arr += 1
                if n >= K:
                    if t >= warm: blk += 1
                else:
                    st = rng.expovariate(mu)
                    if n < c:
                        if t >= warm:
                            nwait += 1
                            waits.append(st)
                    else:
                        if t >= warm: ntot += 1
                    heapq.heappush(depq, t + st)
                    n += 1
            else:
                t = td
                heapq.heappop(depq)
                n -= 1
                if t >= warm: dep += 1
        L = area / win
        bf = busy / win
        bu = area / win / c
        pl = blk / arr if arr else 0.0
        pw = nwait / arr if arr else 0.0
        W = (sum(waits) + sum(rng.expovariate(mu) for _ in range(ntot))) / (nwait + ntot) * 60.0 if (nwait + ntot) else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot_area += area; tot_busy += busy
        tot_arr += arr; tot_blk += blk; tot_dep += dep
        tot_wait += sum(waits) + sum(rng.expovariate(mu) for _ in range(ntot))
        tot_nwait += nwait + ntot

    m = a.seeds
    L = tot_area / m / win
    bf = tot_busy / m / win
    bu = tot_busy / m / win / c
    pl = tot_blk / tot_arr if tot_arr else 0.0
    pw = tot_nwait and 0.0
    W = tot_wait / tot_nwait * 60.0 if tot_nwait else 0.0
    dep_rate = tot_dep / m / win
    lam_eff = tot_arr / m / win
    out = {
        "L": L, "W": W, "busy_frac": bf, "p_loss": pl,
        "runtime_units": "hour", "seed_list": list(range(a.seed_start, a.seed_start + a.seeds)),
        "seeds_used": m, "time_unit": "hour", "win": win,
        "arr": tot_arr / m, "blk": tot_blk / m, "busy_util": bu,
        "busy_occupied": bf, "dep": tot_dep / m, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_wait": per_pw and sum(per_pw) / m,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
