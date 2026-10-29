import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 5.0; mean_s = 6.0 / 60.0
    if a.pert == "lam_up": lam *= 1.1
    if a.pert == "mu_up": mean_s /= 1.1
    if a.pert == "c_up": pass
    cv2 = 2.25
    q = 0.5 * (1.0 + math.sqrt((cv2 - 1.0) / (cv2 + 1.0)))
    r1 = 2.0 * q / mean_s; r2 = 2.0 * (1.0 - q) / mean_s
    warm = 0.25 * H; win = H - warm
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        arr_t = []
        def next_arr(t):
            return t + rng.expovariate(lam)
        na = next_arr(t)
        events = []
        heapq.heappush(events, (na, 0))
        in_sys = 0
        busy = False
        dep_heap = []
        area_N = 0.0; area_B = 0.0
        arr_w = dep_w = wait_n = 0
        sum_resid = 0.0
        last = t
        while True:
            if events:
                te, kind = heapq.heappop(events)
            else:
                break
            if te > H:
                break
            dt = te - last
            area_N += in_sys * dt
            area_B += (1.0 if busy else 0.0) * dt
            last = te
            t = te
            if kind == 0:
                in_sys += 1
                st = rng.random()
                if st < q:
                    sv = rng.expovariate(r1)
                else:
                    sv = rng.expovariate(r2)
                stime = sv
                if not busy:
                    busy = True
                    heapq.heappush(dep_heap, (t + stime, t, 0.0))
                else:
                    arr_t.append((t, stime))
                heapq.heappush(events, (next_arr(t), 0))
            else:
                _, a0, _ = heapq.heappop(dep_heap)
                in_sys -= 1
                if t >= warm:
                    dep_w += 1
                    sum_resid += t - a0
                if arr_t:
                    at, sst = arr_t.pop(0)
                    heapq.heappush(dep_heap, (t + sst, at, 0.0))
                else:
                    busy = False
            while arr_t and not busy:
                pass
            if not busy and arr_t:
                at, sst = arr_t.pop(0)
                busy = True
                heapq.heappush(dep_heap, (t + sst, at, 0.0))
        dt = H - last
        area_N += in_sys * dt
        area_B += (1.0 if busy else 0.0) * dt
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += 0
        per_L.append(area_N / win)
        per_W.append(sum_resid / dep_w if dep_w else 0.0)
        per_bf.append(area_B / win)
        per_pl.append(0.0)
        per_pw.append(0.0)
    seeds_used = n_seeds
    L = sum(per_L) / seeds_used
    W = sum(per_W) / seeds_used
    busy_frac = sum(per_bf) / seeds_used
    arr = tot_arr / seeds_used
    dep = tot_dep / seeds_used
    blk = tot_blk / seeds_used
    out = {
        "L": L, "W": W * 60.0, "busy_frac": busy_frac,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "hour", "win": win,
        "arr": arr, "blk": blk, "busy_util": busy_frac,
        "busy_occupied": busy_frac, "dep": dep, "dep_rate": dep / win,
        "lam_eff": arr / win, "p_loss": 0.0, "p_wait": 0.0,
        "per_seed_L": per_L, "per_seed_W": [w * 60.0 for w in per_W],
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
