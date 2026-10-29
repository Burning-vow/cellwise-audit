import argparse, json, heapq, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu = 6.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.1
    warm = 0.25 * H
    per = []
    seed_list = []
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        srv = []
        busy = 0.0
        area_N = 0.0
        area_B = 0.0
        arr_c = 0; dep_c = 0; wait_c = 0; loss_c = 0
        sum_W = 0.0; sum_sojourn = 0.0
        served_after = 0
        while t < H:
            nt = next_arr if not srv else min(next_arr, srv[0])
            if not srv and next_arr < srv[0] if srv else True:
                pass
            if not srv:
                nt = next_arr
            else:
                nt = min(next_arr, srv[0])
            if nt > H:
                dt = H - t
                area_N += len(srv) * dt
                area_B += (1 if srv else 0) * dt
                break
            dt = nt - t
            area_N += len(srv) * dt
            area_B += (1 if srv else 0) * dt
            t = nt
            if srv and srv[0] <= next_arr:
                heapq.heappop(srv)
                dep_c += 1
                if t > warm:
                    served_after += 1
            else:
                st = rng.expovariate(mu)
                if not srv:
                    heapq.heappush(srv, t + st)
                    if t > warm:
                        wait_c += 1
                else:
                    heapq.heappush(srv, srv[0] + st)
                    if t > warm:
                        wait_c += 1
                arr_c += 1
                sum_sojourn += st
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        L = area_N / win
        busy_frac = area_B / win
        W = sum_sojourn / max(1, arr_c) * 60.0
        per.append({"seed": seed, "L": L, "W": W, "busy_frac": busy_frac,
                    "p_wait": wait_c / max(1, arr_c), "p_loss": 0.0,
                    "arr": arr_c / win, "dep": dep_c / win, "blk": 0.0,
                    "dep_rate": dep_c / win, "busy_util": busy_frac,
                    "busy_occupied": busy_frac, "lam_eff": dep_c / win})
    L = sum(p["L"] for p in per) / n_seeds
    W = sum(p["W"] for p in per) / n_seeds
    bf = sum(p["busy_frac"] for p in per) / n_seeds
    pw = sum(p["p_wait"] for p in per) / n_seeds
    pl = sum(p["p_loss"] for p in per) / n_seeds
    ar = sum(p["arr"] for p in per) / n_seeds
    dp = sum(p["dep"] for p in per) / n_seeds
    bk = sum(p["blk"] for p in per) / n_seeds
    dr = sum(p["dep_rate"] for p in per) / n_seeds
    bu = sum(p["busy_util"] for p in per) / n_seeds
    bo = sum(p["busy_occupied"] for p in per) / n_seeds
    le = sum(p["lam_eff"] for p in per) / n_seeds
    out = {"L": L, "W": W, "busy_frac": bf, "p_wait": pw, "p_loss": pl,
           "runtime_units": H, "seed_list": seed_list, "seeds_used": n_seeds,
           "time_unit": "hour", "win": H * 0.75, "arr": ar, "blk": bk,
           "dep": dp, "dep_rate": dr, "lam_eff": le, "busy_util": bu,
           "busy_occupied": bo,
           "per_seed_L": [p["L"] for p in per],
           "per_seed_W": [p["W"] for p in per],
           "per_seed_busy_frac": [p["busy_frac"] for p in per],
           "per_seed_p_loss": [p["p_loss"] for p in per],
           "per_seed_p_wait": [p["p_wait"] for p in per]}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
