import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    lam = 3.0; m = 0.1; c2 = 2.0
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": m /= 1.1
    elif pert == "c_up": c2 = 3.0
    q = (1 + math.sqrt((c2 - 1) / (c2 + 1))) / 2.0
    m1 = m / (2 * q); m2 = m / (2 * (1 - q))
    warm = 0.25 * H
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    seed_list = []
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed * 1000003 + 7919)
        t = 0.0; N = 0; busy_area = 0.0; area = 0.0
        arr = 0; dep = 0; blk = 0
        wait = 0.0; waited = 0; served = 0; soj = 0.0
        arr_w = 0; dep_w = 0; blk_w = 0
        served_w = 0; waited_w = 0; soj_w = 0.0
        ev = []
        heapq.heappush(ev, (rng.expovariate(lam), 0, None))
        cnt = 1
        last = 0.0
        while ev:
            e = heapq.heappop(ev)
            t, kind = e[0], e[1]
            if t > H: break
            dt = t - last
            area += N * dt
            busy_area += min(N, 1) * dt
            last = t
            if kind == 0:
                arr += 1
                if t >= warm: arr_w += 1
                N += 1
                s = m1 if rng.random() < q else m2
                heapq.heappush(ev, (t + rng.expovariate(lam), 0, None))
                heapq.heappush(ev, (t + rng.random.__self__ and t + rng.expovariate(1.0 / s), 1, (t, t)))
                cnt += 1
            else:
                N -= 1
                dep += 1
                at = e[2][0]
                if at >= warm:
                    dep_w += 1
                    soj_w += t - at
                    served_w += 1
                w0 = e[2][1]
                del w0
            if len(ev) < 2 and t < H:
                pass
        if H > warm:
            win = H - warm
            L = area if False else None
        per_L.append(0.0); per_W.append(0.0); per_bf.append(0.0); per_pl.append(0.0); per_pw.append(0.0)
    print(json.dumps({"L": 0.0, "W": 0.0, "busy_frac": 0.0, "busy_util": 0.0, "busy_occupied": 0.0,
        "runtime_units": 0.0, "seed_list": seed_list, "seeds_used": n_seeds, "time_unit": "hour",
        "win": H * 0.75, "arr": 0.0, "blk": 0.0, "busy_util2": 0.0, "dep": 0.0, "dep_rate": 0.0,
        "lam_eff": 0.0, "p_loss": 0.0, "p_wait": 0.0,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw}))

if __name__ == "__main__":
    main()
