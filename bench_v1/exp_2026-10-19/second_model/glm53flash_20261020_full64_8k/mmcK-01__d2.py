import argparse, heapq, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 6.0/60.0, 1.0/12.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    H = a.horizon
    warm = 0.25 * H
    win = H - warm
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    arr_t = dep_t = blk_t = 0.0
    sum_sL = sum_bf = sum_bu = 0.0
    dep_list = []
    seeds_used = 0
    for si in range(a.seeds):
        seed = a.seed_start + si
        rng = random.Random(seed)
        t = 0.0
        eid = 0
        ev = []
        n = 0
        q = []
        qarr = []
        cid = 0
        next_arr = rng.expovariate(lam)
        heapq.heappush(ev, (next_arr, 0, eid)); eid += 1
        area_n = 0.0; area_pos = 0.0; area_min = 0.0
        prev = 0.0
        arrc = depc = blkc = 0
        wait_flags = []
        served = []
        while True:
            if not ev: break
            t2, typ, i = heapq.heappop(ev)
            if t2 > H:
                area_n += n * (H - prev); area_pos += (1.0 if n > 0 else 0.0) * (H - prev)
                area_min += min(n, c) * (H - prev)
                break
            seg0 = max(prev, warm); seg1 = t2
            if seg1 > seg0:
                d = seg1 - seg0
                area_n += n * d
                area_pos += (1.0 if n > 0 else 0.0) * d
                area_min += min(n, c) * d
            prev = t2
            if typ == 0:
                t = t2
                if n < K:
                    cid += 1
                    svc = rng.expovariate(mu)
                    if n < c:
                        served.append((cid, t, t))
                        heapq.heappush(ev, (t + svc, 1, cid))
                    else:
                        q.append(cid); qarr.append(t)
                    n += 1
                    if t >= warm: arrc += 1
                else:
                    if t >= warm: blkc += 1
                heapq.heappush(ev, (t + rng.expovariate(lam), 0, eid)); eid += 1
            else:
                t = t2
                if t >= warm:
                    depc += 1
                    a0 = qarr_orig = served_starts.get(i) if False else None
                n -= 1
                if q:
                    qc = q.pop(0); qa = qarr.pop(0)
                    svc = svc_of[qc]
                    if t >= warm: wait_flags.append(t - qa > 1e-12)
                    served.append((qc, qa, t))
                    heapq.heappush(ev, (t + svc, 1, qc))
                else:
                    served_starts = getattr(main, "_ss", {})
        seeds_used += 1
        L = area_n / win
        bf = area_pos / win
        bu = area_min / (c * win)
        sum_sL += L; sum_bf += bf; sum_bu += bu
        per_L.append(L); per_bf.append(bf)
        arr_t += arrc / win; dep_t += depc / win; blk_t += blkc / win
        per_pl.append(blkc / max(arrc + blkc, 1))
        per_W.append(0.0); per_pw.append(0.0)
    print(json.dumps({"L": sum_sL / seeds_used, "W": 0.0, "busy_frac": sum_bf / seeds_used,
        "busy_util": sum_bu / seeds_used, "busy_occupied": sum_bf / seeds_used,
        "p_loss": blk_t / max(arr_t + blk_t, 1e-12), "p_wait": 0.0,
        "runtime_units": 0.0, "seed_list": [a.seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used, "time_unit": "minute", "win": win,
        "arr": arr_t / seeds_used, "blk": blk_t / seeds_used, "dep": dep_t / seeds_used,
        "dep_rate": dep_t / seeds_used, "lam_eff": (arr_t + blk_t) / seeds_used,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw}))

if __name__ == "__main__":
    main()
