import argparse, heapq, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    c = 3
    lam, mu = 8.0, 60.0 / 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    horizon = a.horizon
    warm = 0.25 * horizon
    win = horizon - warm
    per_L, per_W, per_busy, per_pwait, per_ploss = [], [], [], [], []
    seed_list, tot_arr, tot_dep, tot_blk = [], 0.0, 0.0, 0.0
    seeds_used = 0
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        t = 0.0
        ev = []
        nid = 0
        def sched(tt, typ, cust): heapq.heappush(ev, (tt, nid, typ, cust))
        sched(rng.expovariate(lam), "arr", None)
        n = 0
        busy = 0
        area_n = 0.0
        area_busy = 0.0
        n_arr = 0
        n_wait = 0
        n_dep = 0
        n_blk = 0
        soj = []
        last = 0.0
        while ev:
            tt, _, typ, cust = heapq.heappop(ev)
            if tt > horizon: break
            if tt > warm:
                area_n += n * (tt - last)
                area_busy += min(n, c) * (tt - last)
            last = tt
            if typ == "arr":
                if tt >= warm: n_arr += 1
                st = rng.expovariate(mu)
                svc = {"st": st}
                if tt >= warm and n >= c: n_wait += 1
                if n < c:
                    n += 1
                    sched(tt + st, "dep", {"st": st, "t0": tt})
                else:
                    q = [x for x in ev if x[2] == "dep"]
                    n += 1
                    sched(tt + st, "dep", {"st": st, "t0": tt, "q": True})
                    heapq.heapify(ev)
                sched(tt + rng.expovariate(lam), "arr", None)
            else:
                n -= 1
                if tt >= warm:
                    n_dep += 1
                    soj.append(tt - cust["t0"])
                if n >= c:
                    sched(tt + cust["st"], "dep", {"st": rng.expovariate(mu), "t0": cust["t0"]})
        seeds_used += 1
        seed_list.append(seed)
        L = area_n / win
        bf = area_busy / win / c
        Wm = (sum(soj) / len(soj)) * 60.0 if soj else 0.0
        pw = n_wait / n_arr if n_arr else 0.0
        per_L.append(L); per_W.append(Wm); per_busy.append(bf)
        per_pwait.append(pw); per_ploss.append(0.0)
        tot_arr += n_arr / win; tot_dep += n_dep / win; tot_blk += 0.0
    Lm = sum(per_L) / seeds_used
    Wm = sum(per_W) / seeds_used
    bfm = sum(per_busy) / seeds_used
    pwm = sum(per_pwait) / seeds_used
    out = {"L": Lm, "W": Wm, "busy_frac": bfm, "p_wait": pwm, "p_loss": 0.0,
           "busy_util": bfm, "busy_occupied": 1.0 - math.exp(-lam / mu) if False else pwm,
           "runtime_units": "hour", "time_unit": "hour", "win": win,
           "seed_list": seed_list, "seeds_used": seeds_used,
           "arr": tot_arr / seeds_used, "dep": tot_dep / seeds_used,
           "blk": tot_blk / seeds_used, "dep_rate": tot_dep / seeds_used / win,
           "lam_eff": tot_arr / seeds_used,
           "per_seed_L": per_L, "per_seed_W": per_W,
           "per_seed_busy_frac": per_busy, "per_seed_p_wait": per_pwait,
           "per_seed_p_loss": per_ploss}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
