import json, argparse, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, c, K = 6.0, 10.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1; K += 1
    warm = 0.25 * H; win = H - warm
    pL=[];pW=[];pB=[];pLoss=[];pWt=[]
    aL=0;aW=0;aB=0;aBf=0;aWt=0;aBu=0;aArr=0;aDep=0;aDepR=0
    seeds=[]
    for si in range(n_seeds):
        seed = S + si; seeds.append(seed)
        rng = random.Random(seed)
        t = 0.0; N = 0; busy = 0
        eq = []; heapq.heapify(eq)
        nxt = rng.expovariate(lam)
        heapq.heappush(eq, (nxt, 0, None))
        area = 0.0; area_occ = 0.0; area_min = 0.0
        cnt_arr = 0; cnt_dep = 0; cnt_blk = 0; cnt_wait = 0; cnt_join = 0
        sumW = 0.0; last = 0.0
        tid = 1
        def sch(t, ev):
            nonlocal tid
            heapq.heappush(eq, (t, tid, ev)); tid += 1
        while eq:
            t2, _, ev = heapq.heappop(eq)
            if t2 > H: break
            if t2 > warm:
                area += N * (t2 - last)
                area_occ += (1 if N > 0 else 0) * (t2 - last)
                area_min += min(N, c) * (t2 - last)
            last = t2; t = t2
            if ev == 0:
                cnt_arr += 1
                svc = rng.expovariate(mu)
                if N < K:
                    cnt_join += 1
                    if N >= c: cnt_wait += 1
                    N += 1; busy += 1
                    sch(t + svc, 1)
                else:
                    cnt_blk += 1
                sch(t + rng.expovariate(lam), 0)
            else:
                N -= 1; busy -= 1; cnt_dep += 1
                if t > warm: sumW += svc * 1.0 if False else 0.0
        # W needs service-drawn-at-arrival: recompute via per-arrival tracking
        # redo properly below with recorder
        pL.append(0.0)
    # Reimplement cleanly
    def run(seed):
        rng = random.Random(seed)
        t = 0.0; N = 0
        eq = []
        heapq.heappush(eq, (rng.expovariate(lam), 0, None))
        tid = 1
        area = 0.0; area_occ = 0.0; area_min = 0.0
        c_arr = c_dep = c_blk = c_wait = c_join = 0
        sW = 0.0; last = 0.0
        while eq:
            t2, k, ev = heapq.heappop(eq)
            if t2 > H: break
            if t2 > warm:
                area += N * (t2 - last)
                area_occ += (N > 0) * (t2 - last)
                area_min += min(N, c) * (t2 - last)
            last = t2; t = t2
            if ev == 0:
                c_arr += 1
                svc = rng.expovariate(mu)
                if N < K:
                    c_join += 1
                    if N >= c: c_wait += 1; sW += t - join_t[0]
                    N += 1
                    heapq.heappush(eq, (t + svc, tid, 1)); tid += 1
                else:
                    c_blk += 1
                heapq.heappush(eq, (t + rng.expovariate(lam), tid, 0)); tid += 1
            else:
                N -= 1; c_dep += 1
        Lq = area / win; occ = area_occ / win; util = area_min / (c * win)
        dep_rate = c_dep / win
        lam_eff = (c_arr - c_blk) / win
        return Lq, sW / max(c_join,1) * 60.0, occ, c_blk / max(c_arr,1), c_wait / max(c_join,1), c_arr, c_blk, c_dep, dep_rate, lam_eff, util
    join_t = [0.0]
    # need join time tracking; redo run with join time
    def run2(seed):
        rng = random.Random(seed)
        t = 0.0; N = 0
        eq = []
        heapq.heappush(eq, (rng.expovariate(lam), 0, None))
        tid = 1
        area = 0.0; area_occ = 0.0; area_min = 0.0
        c_arr = c_dep = c_blk = c_wait = c_join = 0
        sW = 0.0; last = 0.0; pend = {}
        while eq:
            t2, k, ev = heapq.heappop(eq)
            if t2 > H: break
            if t2 > warm:
                area += N * (t2 - last)
                area_occ += (N > 0) * (t2 - last)
                area_min += min(N, c) * (t2 - last)
            last = t2; t = t2
            if ev == 0:
                c_arr += 1
                svc = rng.expovariate(mu)
                if N < K:
                    c_join += 1
                    if N >= c:
                        c_wait += 1
                    jt = t
                    N += 1
                    heapq.heappush(eq, (t + svc, tid, (1, jt))); tid += 1
                else:
                    c_blk += 1
                heapq.heappush(eq, (t + rng.expovariate(lam), tid, 0)); tid += 1
            else:
                N -= 1; c_dep += 1
                if isinstance(ev, tuple) and t2 > warm:
                    sW += t2 - ev[1]
        return (area / win, sW / max(c_wait,1) * 60.0, area_occ / win,
                c_blk / max(c_arr,1), c_wait / max(c_join,1), c_arr, c_blk, c_dep,
                c_dep / win, (c_arr - c_blk) / win, area_min / (c * win))
    ts = []
    for seed in seeds:
        r = run2(seed)
        ts.append(r)
        pL.append(r[0]); pW.append(r[1]); pB.append(r[2]); pLoss.append(r[3]); pWt.append(r[4])
    n = len(ts)
    out = {
        "L": sum(x[0] for x in ts)/n,
        "W": sum(x[1] for x in ts)/n,
        "busy_frac": sum(x[2] for x in ts)/n,
        "p_loss": sum(x[3] for x in ts)/n,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win,
        "arr": sum(x[5] for x in ts)/n,
        "blk": sum(x[6] for x in ts)/n,
        "busy_util": sum(x[10] for x in ts)/n,
        "busy_occupied": sum(x[2] for x in ts)/n,
        "dep": sum(x[7] for x in ts)/n,
        "dep_rate": sum(x[8] for x in ts)/n,
        "lam_eff": sum(x[9] for x in ts)/n,
        "p_wait": sum(x[4] for x in ts)/n,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": pLoss, "per_seed_p_wait": pWt,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
