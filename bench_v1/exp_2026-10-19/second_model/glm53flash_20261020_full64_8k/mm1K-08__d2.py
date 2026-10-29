import json, argparse, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, K = 0.1, 0.2, 6
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    warm = 0.25 * H; win = H - warm
    pL, pW, pB, pLoss, pWait = [], [], [], [], []
    seeds_used = 0; seed_list = []
    arr_tot = dep_tot = blk_tot = 0.0; busy_tot = 0.0
    for si in range(S, S + n_seeds):
        rng = random.Random(si)
        t = 0.0; t_arr = rng.expovariate(lam); t_dep = math.inf
        N = 0; queue = []
        L_area = 0.0; busy_area = 0.0
        arr = dep = blk = 0; waits = []; waited = 0; adm = 0
        while True:
            t_next = min(t_arr, t_dep)
            if t_next > H:
                t_next = H
            dt = t_next - t
            if t_next > warm:
                lo = max(t, warm)
                L_area += N * (t_next - lo)
                busy_area += (1 if N > 0 else 0) * (t_next - lo)
            if t_next >= H: break
            t = t_next
            if t_arr <= t_dep:
                inwin = t >= warm
                if inwin: arr += 1
                if N < K:
                    st = rng.expovariate(mu)
                    waited_flag = (N > 0)
                    heapq.heappush(queue, (t + st, t))
                    N += 1
                    if inwin:
                        adm += 1
                        if waited_flag: waited += 1
                    if N == 1:
                        t_dep = t + st
                else:
                    if inwin: blk += 1
                t_arr = t + rng.expovariate(lam)
            else:
                N -= 1
                d, ta = heapq.heappop(queue)
                if d >= warm: waits.append(d - ta); dep += 1
                if queue:
                    t_dep = max(t, queue[0][0])
                else:
                    t_dep = math.inf
        if win <= 0: continue
        L = L_area / win; busy = busy_area / win
        W = (sum(waits) / len(waits)) if waits else 0.0
        pl = blk / arr if arr > 0 else 0.0
        pw = waited / adm if adm > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(busy); pLoss.append(pl); pWait.append(pw)
        arr_tot += arr; dep_tot += dep; blk_tot += blk; busy_tot += busy
        seeds_used += 1; seed_list.append(si)
    m = max(seeds_used, 1)
    Lm = sum(pL) / m; Wm = sum(pW) / m; Bm = sum(pB) / m
    ploss = sum(pLoss) / m; pwait = sum(pWait) / m
    out = {
        "L": Lm, "W": Wm, "busy_frac": Bm, "p_loss": ploss,
        "runtime_units": H * n_seeds, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "minute", "win": win,
        "arr": arr_tot / m, "blk": blk_tot / m, "dep": dep_tot / m,
        "dep_rate": dep_tot / m / win, "lam_eff": (arr_tot - blk_tot) / m / win,
        "p_wait": pwait, "busy_util": Lm, "busy_occupied": Bm,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": pLoss, "per_seed_p_wait": pWait
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
