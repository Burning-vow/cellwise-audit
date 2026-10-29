import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon)
    lam, c = 5.0, 1.0
    if a.pert == "lam_up": lam *= 1.1
    if a.pert == "mu_up": c *= 1.1
    if a.pert == "c_up": c *= 1.1
    m = 0.1
    cv2 = 4.0
    p = 0.5 * (1 + math.sqrt((cv2 - 1) / (cv2 + 1)))
    mu1, mu2 = 2 * p / (m / c), 2 * (1 - p) / (m / c)
    warm = 0.25 * H
    def svc(rng):
        if rng.random() < p: return rng.expovariate(mu1)
        return rng.expovariate(mu2)
    Ls, Ws, BFs, PLs, PWs, seeds_used = [], [], [], [], [], []
    arr_t = dep_t = blk_n = busy_area = n_area = wait_sum = ncnt = 0.0
    wait_cnt = 0
    for k in range(nseeds):
        rng = random.Random(a.seed_start + k)
        t = 0.0; n = 0
        next_arr = rng.expovariate(lam)
        next_dep = math.inf
        busy = 0.0; area_n = 0.0
        soj_sum = 0.0; soj_n = 0
        lost = 0; served = 0
        q_wait = 0.0; q_cnt = 0
        pq = []
        while t < H:
            if next_arr <= next_dep and next_arr <= H:
                tn = next_arr
            elif next_dep <= H:
                tn = next_dep
            else:
                tn = H
            if tn > warm:
                dt = tn - t
                area_n += n * dt
                busy += (1 if n >= 1 else 0) * dt
            t = tn
            if t == next_arr:
                n += 1
                if t > warm: ncnt += 1
                if n == 1:
                    st = svc(rng)
                    next_dep = t + st
                else:
                    st = svc(rng)
                    heapq.heappush(pq, (t, st))
                next_arr = t + rng.expovariate(lam)
            elif t == next_dep:
                n -= 1
                if t > warm:
                    dep_t += 1; served += 1
                if pq:
                    at, st = heapq.heappop(pq)
                    if t > warm:
                        q_wait += t - at; q_cnt += 1
                    next_dep = t + st
                else:
                    next_dep = math.inf
        if H > warm:
            w = H - warm
            L = area_n / w
            dep_rate = served / w
            bf = busy / w
            lam_eff_arr = ncnt / w
            throughput = dep_rate
            W = L / throughput if throughput > 0 else 0.0
            p_wait = q_cnt / ncnt if ncnt > 0 else 0.0
            p_loss = lost / ncnt if ncnt > 0 else 0.0
            Ls.append(L); Ws.append(W); BFs.append(bf)
            PLs.append(p_loss); PWs.append(p_wait)
            seeds_used.append(a.seed_start + k)
            arr_t += ncnt / w; dep_t_cum = dep_rate
    n_run = len(Ls) if Ls else 0
    if n_run:
        L = sum(Ls) / n_run; W = sum(Ws) / n_run
        busy_frac = sum(BFs) / n_run
        p_loss = sum(PLs) / n_run; p_wait = sum(PWs) / n_run
        win = H * 0.75
        dep = sum(dep_rate for _ in range(0)) if False else None
        arr_avg = arr_t / n_run
    else:
        L = W = busy_frac = p_loss = p_wait = 0.0; win = 0.0
        arr_avg = dep_rate = 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac
    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "runtime_units": "hour", "seed_list": seeds_used,
        "seeds_used": n_run, "time_unit": "hour", "win": win,
        "arr": arr_avg, "blk": 0.0,
        "busy_util": busy_util, "busy_occupied": busy_occupied,
        "dep": dep_rate if n_run else 0.0,
        "dep_rate": dep_rate if n_run else 0.0,
        "lam_eff": lam if not (a.pert == "lam_up") else lam,
        "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": Ls, "per_seed_W": Ws,
        "per_seed_busy_frac": BFs,
        "per_seed_p_loss": PLs, "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
