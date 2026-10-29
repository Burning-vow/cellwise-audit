import argparse, json, random, heapq, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 8.0
    svc = 5.0 / 60.0
    c = 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": svc *= 0.9
    elif a.pert == "c_up": c = 2
    H = float(a.horizon)
    ws = 0.25 * H
    win = H - ws
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    agg_arr = agg_dep = agg_blk = agg_busy = agg_area = 0.0
    agg_waited = agg_winarr = 0.0
    seed_list = []
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        t_last = 0.0
        area = 0.0
        busy = 0.0
        depq = []
        next_arr = rng.expovariate(lam)
        n_arr = n_dep = n_blk = 0
        n_waited = 0
        sum_soj = 0.0
        soj = {}
        while t_last < H:
            nxt = next_arr
            ev_arr = True
            if depq and depq[0] < nxt:
                nxt = depq[0]; ev_arr = False
            if nxt >= H: nxt = H
            lo = max(t_last, ws)
            if nxt > lo:
                seg = nxt - lo
                N = len(depq)
                area += N * seg
                if N > 0: busy += seg
            t_last = nxt
            if nxt >= H: break
            if ev_arr:
                t = next_arr
                if len(depq) < c:
                    d = t + svc
                    if depq and depq[0] > t: n_waited += 1 if t >= ws else 0
                    heapq.heappush(depq, d)
                    soj[id(d)] = t
                    if t >= ws:
                        n_arr += 1
                        agg_winarr += 1
                else:
                    if t >= ws: n_blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                d = heapq.heappop(depq)
                arr_t = soj.pop(id(d))
                if arr_t >= ws:
                    n_dep += 1
                    sum_soj += d - arr_t
        n_arr_tot = n_arr + n_blk
        L = area / win
        W = sum_soj / n_arr if n_arr > 0 else svc
        bf = busy / win
        pl = n_blk / n_arr_tot if n_arr_tot > 0 else 0.0
        pw = n_waited / n_arr if n_arr > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        agg_area += area; agg_busy += busy
        agg_arr += n_arr; agg_dep += n_dep; agg_blk += n_blk
        agg_waited += n_waited
    S = a.seeds
    out = {
        "L": agg_area / (S * win),
        "W": (sum(per_W)) / S,
        "busy_frac": agg_busy / (S * win),
        "busy_util": agg_busy / (S * win) / c,
        "busy_occupied": agg_busy / (S * win),
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": S,
        "time_unit": "hour",
        "win": win,
        "arr": agg_arr / S,
        "dep": agg_dep / S,
        "blk": agg_blk / S,
        "dep_rate": agg_dep / (S * win),
        "lam_eff": agg_arr / (S * win),
        "p_loss": agg_blk / (S * agg_arr) if agg_arr > 0 else 0.0,
        "p_wait": agg_waited / agg_arr if agg_arr > 0 else 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
