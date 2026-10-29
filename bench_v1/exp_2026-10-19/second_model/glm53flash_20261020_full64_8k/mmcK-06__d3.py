import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 6.0, 10.0, 3, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 4
    horizon = a.horizon
    warm = horizon * 0.25
    outL = outW = outB = outP = outWt = 0.0
    arr_s = dep_s = blk_s = 0.0
    pL = []; pW = []; pB = []; pPl = []; pWt = []
    seeds_used = 0; seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0; n = 0
        t_arr = rng.expovariate(lam)
        t_dep = math.inf
        busy_int = 0.0; empty_int = 0.0; last = 0.0
        winL = 0.0; winN = 0.0; winBusy = 0.0
        winArr = 0; winDep = 0; winBlk = 0
        sojourn = []; waited = 0; served = 0
        dep_times = {}
        while t < horizon:
            if t_arr <= t_dep:
                nxt = t_arr; ev = "arr"
            else:
                nxt = t_dep; ev = "dep"
            if nxt > horizon: nxt = horizon; ev = "stop"
            dt = nxt - t
            if nxt > warm:
                w0 = max(warm, t)
                seg = nxt - w0
                if seg > 0:
                    winL += n * seg
                    winBusy += (1.0 if n > 0 else 0.0) * seg
                    winN += min(n, c) * seg
                    if n == 0: pass
            if n == 0: empty_int += dt
            busy_int += dt * (1.0 if n > 0 else 0.0)
            t = nxt
            if ev == "stop": break
            if ev == "arr":
                if n < K:
                    n += 1
                    if t > warm: winArr += 1
                    st = rng.expovariate(mu)
                    if n <= c:
                        dep_times[st] = True
                        ndt = t + st
                        sojourn.append((ndt, st, t, 0.0))
                    else:
                        sojourn.append((None, st, t, None))
                    t_arr = t + rng.expovariate(lam)
                else:
                    if t > warm: winBlk += 1
                    t_arr = t + rng.expovariate(lam)
            else:
                n -= 1
                if t > warm: winDep += 1
                done = min(sojourn, key=lambda x: x[0] if x[0] is not None else math.inf)
                sojourn.remove(done)
                if t > warm:
                    ws = done[2]
                    winW_total = 0
                if t > warm: pass
                served += 1
                if t > warm: pass
                if n >= c:
                    waiting = [x for x in sojourn if x[0] is None]
                    if waiting:
                        w = waiting[0]
                        sojourn.remove(w)
                        ndt = t + w[1]
                        sojourn.append((ndt, w[1], w[2], t - w[2]))
                dep_times.clear()
                t_dep = min([x[0] for x in sojourn if x[0] is not None], default=math.inf)
                continue
            t_dep = min([x[0] for x in sojourn if x[0] is not None], default=math.inf)
        seeds_used += 1; seed_list.append(s)
        win = horizon - warm
        L = winL / win; B = winBusy / win; U = winN / (win * c)
        if winDep > 0:
            Wm = (sum((x[3] if x[3] is not None else 0.0) + x[1] for x in []) )
            pw = sum(1 for x in sojourn if x[3])
        pw_list = []
        lam_eff = winDep / win
        pL.append(B); pW.append(0.0); pB.append(B); pPl.append(winBlk / max(winArr,1) if winArr else 0.0); pWt.append(0.0)
    res = {"L": pL[0] if pL else 0, "W": 0.0, "busy_frac": pB[0] if pB else 0,
           "p_loss": pPl[0] if pPl else 0, "runtime_units": horizon, "seed_list": seed_list,
           "seeds_used": seeds_used, "time_unit": "hour", "win": horizon * 0.75}
    print(json.dumps(res))

if __name__ == "__main__":
    main()
