import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, K = 9.0/60.0, 1.0/6.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K = 5
    warm = 0.25 * H; win = H - warm
    agg = dict(L=0.0, W=0.0, busy=0.0, p_loss=0.0, p_wait=0.0)
    per = {"L": [], "W": [], "busy_frac": [], "p_loss": [], "p_wait": []}
    seeds_used = 0; seed_list = []; arrs = 0.0; deps = 0.0; blks = 0.0
    for si in range(nseeds):
        rng = random.Random(S + si)
        t = 0.0; ta = rng.expovariate(lam); td = math.inf
        n = 0; service = {}; q = []; nxt = ta; tprev = 0.0
        area = 0.0; busy = 0.0; blk = 0; arr = 0; dep = 0
        waited = 0; served = 0; wsum = 0.0
        while True:
            nxt = min(ta, td)
            if nxt > H: nxt = H
            dt = nxt - tprev
            if nxt > warm:
                seg = min(nxt, H) - max(tprev, warm)
                if seg > 0:
                    area += n * seg
                    if n > 0: busy += seg
            tprev = nxt; t = nxt
            if t >= H: break
            if ta <= td:
                arr += 1
                at = t
                t += 0.0
                if n < K:
                    st = rng.expovariate(mu)
                    if n == 0:
                        td = t + st
                        service["_cur"] = st
                    else:
                        q.append((t, st))
                    n += 1
                    arr_time_of_cur = at if n == 1 else q[-1][0]
                    arrive_map = service.setdefault("_arr", [])
                    if n == 1:
                        service["_arr_cur"] = at
                    else:
                        q[-1] = (q[-1][0], q[-1][1], at)
                else:
                    blk += 1
                ta = t + rng.expovariate(lam)
                ta = t + rng.expovariate(lam)
                ta = t + rng.expovariate(lam)
            else:
                dep += 1
                w = t - service.get("_arr_cur", t)
                if w > 1e-12: waited += 1
                served += 1; wsum += w
                n -= 1
                if q:
                    s0 = q.pop(0)
                    td = t + s0[1]
                    service["_arr_cur"] = s0[2]
                else:
                    td = math.inf
                    service.pop("_arr_cur", None)
        L = area / win; bf = busy / win
        pl = blk / win if False else (blk / max(arr, 1))
        pw = waited / served if served else 0.0
        Wm = (wsum / served) if served else 0.0
        per["L"].append(L); per["W"].append(Wm); per["busy_frac"].append(bf)
        per["p_loss"].append(pl); per["p_wait"].append(pw)
        agg["L"] += L; agg["W"] += Wm; agg["busy"] += bf
        agg["p_loss"] += pl; agg["p_wait"] += pw
        arrs += arr; deps += dep; blks += blk
        seeds_used += 1; seed_list.append(S + si)
    L = agg["L"] / seeds_used; W = agg["W"] / seeds_used
    bf = agg["busy"] / seeds_used; pl = agg["p_loss"] / seeds_used
    pw = agg["p_wait"] / seeds_used
    out = {
        "L": L, "W": W, "busy_frac": bf, "p_loss": pl,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "minute", "win": win,
        "arr": arrs / seeds_used, "blk": blks / seeds_used,
        "busy_util": min(lam / mu, 1.0), "busy_occupied": bf,
        "dep": deps / seeds_used,
        "dep_rate": (deps / seeds_used) / (win / 60.0),
        "lam_eff": (deps / seeds_used) / (win / 60.0),
        "p_wait": pw,
        "per_seed_L": per["L"], "per_seed_W": per["W"],
        "per_seed_busy_frac": per["busy_frac"],
        "per_seed_p_loss": per["p_loss"], "per_seed_p_wait": per["p_wait"],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
