import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, c = 8.0, 10.0, 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 2

    H = a.horizon
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seeds_used, seed_list = 0, []

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        events = []
        arr_t = rng.expovariate(lam)
        heapq.heappush(events, (arr_t, "a"))
        busy_until = []
        queue = []
        in_sys = 0
        area_N = 0.0; area_bu = 0.0
        n_arr = 0; n_dep = 0; n_blk = 0
        waited = 0; served = 0; sojourn_sum = 0.0
        acc = False
        while t < H:
            te, ev = heapq.heappop(events)
            if te > H: break
            if te >= warm:
                area_N += in_sys * (te - t)
                area_bu += min(len(busy_until), c) * (te - t)
            t = te
            if ev == "a":
                st = rng.expovariate(mu)
                if len(busy_until) < c:
                    heapq.heappush(events, (t + st, "d"))
                    heapq.heappush(busy_until, t + st)
                    start = t
                    waited = waited + (1 if te >= warm else 0)
                    if te >= warm:
                        served += 1; sojourn_sum += st
                else:
                    queue.append((t, st))
                    if te >= warm: waited += 1
                in_sys += 1
                if t >= warm: n_arr += 1
                nt = t + rng.expovariate(lam)
                heapq.heappush(events, (nt, "a"))
            else:
                heapq.heappop(busy_until)
                if queue:
                    at, st = queue.pop(0)
                    heapq.heappush(events, (t + st, "d"))
                    heapq.heappush(busy_until, t + st)
                    if t >= warm:
                        served += 1; sojourn_sum += t - at + st
                in_sys -= 1
                if t >= warm: n_dep += 1
        if H > warm:
            per_L.append(area_N / (H - warm))
            per_bf.append(area_bu / (H - warm) / c)
            per_pw.append(waited / n_arr if n_arr else 0.0)
            per_pl.append(n_blk / n_arr if n_arr else 0.0)
            per_W.append(sojourn_sum / served if served else 0.0)
        else:
            per_L.append(0.0); per_bf.append(0.0); per_pw.append(0.0); per_pl.append(0.0); per_W.append(0.0)
        seeds_used += 1
        seed_list.append(s)

    n = max(seeds_used, 1)
    W_min = sum(per_W) / n * 60.0
    L = sum(per_L) / n
    bf = sum(per_bf) / n
    pw = sum(per_pw) / n
    pl = sum(per_pl) / n
    win = H - 0.25 * H
    dep_rate = sum(per_L) / n * mu
    out = {
        "L": L, "W": W_min, "busy_frac": bf, "p_wait": pw, "p_loss": pl,
        "runtime_units": "minute", "time_unit": "hour", "win": win,
        "seed_list": seed_list, "seeds_used": seeds_used,
        "arr": None, "dep": None, "blk": n_blk / seeds_used if seeds_used else 0.0,
        "busy_util": bf, "busy_occupied": bf, "lam_eff": lam * (1 - pl),
        "dep_rate": dep_rate,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
