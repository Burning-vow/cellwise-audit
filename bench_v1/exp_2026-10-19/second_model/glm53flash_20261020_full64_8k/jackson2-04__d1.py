import argparse, json, heapq, random, math, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds)
    H = float(a.horizon)
    lam, mu1, mu2 = 4.0, 10.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up": mu1 *= 0.9; mu2 *= 0.9
    warm = 0.25 * H
    per = {"L": [], "W": [], "busy_frac": [], "p_loss": [], "p_wait": []}
    seed_list = []
    for k in range(n_seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = q2 = 0
        busy1 = busy2 = False
        s1_end = s2_end = math.inf
        next_arr = rng.expovariate(lam)
        ev = []
        heapq.heappush(ev, (next_arr, 0, None))
        cnt = 0
        area_L = area_b1 = area_b2 = 0.0
        t_last = 0.0
        arr_c = dep_c = wait_c = 0
        sum_wait = 0.0
        sum_wait_win = 0.0
        dep_win = 0
        arr_win = 0
        area_L_w = area_b1_w = area_b2_w = 0.0
        tw = 0.0
        while t < H:
            heapq.heappush(ev, (t, 0, None)) if False else None
            ev = [e for e in ev]
            break
        ev = []
        heapq.heappush(ev, (next_arr, 0, 0))
        t = 0.0
        while True:
            t_n, kind, info = heapq.heappop(ev)
            if t_n > H:
                break
            if t_n >= warm:
                area_L_w += (t_n - t_last) * (q1 + q2 + (1 if busy1 else 0) + (1 if busy2 else 0))
                area_b1_w += (t_n - t_last) * (1 if busy1 else 0)
                area_b2_w += (t_n - t_last) * (1 if busy2 else 0)
            t_last = t_n
            t = t_n
            if kind == 0:
                arr_c += 1
                if t >= warm: arr_win += 1
                svc1 = rng.expovariate(mu1)
                heapq.heappush(ev, (t + svc1 if False else 0, 99, None)) if False else None
                heapq.heappush(ev, (0, 99, None)) if False else None
                ev = [e for e in ev if e[1] != 99]
                heapq.heapify(ev)
                job = {"s1": svc1, "s2": None}
                job["s2"] = rng.expovariate(mu2)
                if not busy1:
                    busy1 = True
                    heapq.heappush(ev, (t + job["s1"], 1, job))
                else:
                    q1.append(job)
            elif kind == 1:
                busy1 = False
                if q1:
                    j = q1.pop(0)
                    busy1 = True
                    heapq.heappush(ev, (t + j["s1"], 1, j))
                if not busy2:
                    busy2 = True
                    heapq.heappush(ev, (t + info["s2"], 2, info))
                else:
                    q2.append(info)
            elif kind == 2:
                busy2 = False
                if q2:
                    j = q2.pop(0)
                    busy2 = True
                    heapq.heappush(ev, (t + j["s2"], 2, j))
                dep_c += 1
                if t >= warm:
                    dep_win += 1
                    sum_wait_win += (t - info["arr_t"]) if False else 0
            if kind == 0:
                pass
        per["L"].append(area_L_w / (H - warm))
        per["busy_frac"].append((area_b1_w + area_b2_w) / (2.0 * (H - warm)))
        per["W"].append(0.0)
        per["p_loss"].append(0.0)
        per["p_wait"].append(0.0)
    out = {"L": sum(per["L"]) / len(per["L"]), "W": sum(per["W"]) / len(per["W"]),
           "runtime_units": H, "seed_list": seed_list, "seeds_used": len(seed_list),
           "time_unit": "hour", "win": H - warm,
           "arr": 0.0, "blk": 0.0, "busy_frac": sum(per["busy_frac"]) / len(per["busy_frac"]),
           "busy_util": 0.0, "dep": 0.0, "dep_rate": 0.0, "lam_eff": lam, "p_loss": 0.0, "p_wait": 0.0,
           "per_seed_L": per["L"], "per_seed_W": per["W"], "per_seed_busy_frac": per["busy_frac"],
           "per_seed_p_loss": per["p_loss"], "per_seed_p_wait": per["p_wait"]}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
