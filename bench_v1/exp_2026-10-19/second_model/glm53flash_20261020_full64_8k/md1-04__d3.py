import argparse, json, heapq, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 6.0
    if a.pert == "lam_up": lam *= 1.1
    mu = 12.0
    if a.pert == "mu_up": mu *= 1.1
    c = 1
    if a.pert == "c_up": c = 2
    svc = 1.0 / mu
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_wait = 0.0; tot_area = 0.0; tot_busy = 0.0
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed * 1000003 + 7919)
        t = 0.0
        served = 0
        q = []
        busy_until = [-1.0] * c
        heapq.heapify(busy_until)
        next_arr = rng.expovariate(lam)
        arr_n = dep_n = blk_n = 0
        wait_sum = 0.0; area = 0.0; busy_area = 0.0
        lost = 0; waited = 0
        last = 0.0
        n_in = 0
        while next_arr < H:
            t = next_arr
            dt = t - last
            if t > warm:
                area += n_in * dt
                busy_area += min(n_in, c) * dt
                arr_n += 1
            last = t
            if n_in < c or n_in < 1000000:
                if n_in < c:
                    st = t + svc
                    heapq.heappush(q, st)
                    n_in += 1
                else:
                    n_in += 1
                    heapq.heappush(q, t)
                    if t > warm: waited += 1
            else:
                if t > warm: lost += 1
            next_arr = t + rng.expovariate(lam)
            while q and q[0] <= next_arr:
                st = heapq.heappop(q)
                dt2 = min(st, next_arr) - max(last, warm)
                pass
                if next_arr > warm:
                    area += n_in * (min(st, next_arr) - max(last, 0.0))
                    busy_area += min(n_in, c) * (min(st, next_arr) - max(last, 0.0))
                if st <= next_arr:
                    n_in -= 1
                    last_dep = st
                    if last_dep > warm:
                        dep_n += 1
                last = st if st > last else last
            last = t
        while q:
            st = heapq.heappop(q)
            if st > H: break
            if H > warm:
                area += n_in * (min(st, H) - max(last, warm))
                busy_area += min(n_in, c) * (min(st, H) - max(last, warm))
            n_in -= 1
            last = st
            if st > warm: dep_n += 1
        win = H - warm
        per_L.append(area / win if win > 0 else 0.0)
        per_W.append((svc + (wait_sum / dep_n if dep_n else 0.0)) if dep_n else svc)
        per_bf.append(busy_area / win if win > 0 else 0.0)
        per_pl.append(lost / arr_n if arr_n else 0.0)
        per_pw.append(waited / arr_n if arr_n else 0.0)
        tot_arr += arr_n; tot_dep += dep_n; tot_blk += lost
        tot_area += area; tot_busy += busy_area
    W_est = sum(per_W) / n_seeds
    L_est = sum(per_L) / n_seeds
    out = {
        "L": L_est, "W": W_est,
        "busy_frac": sum(per_bf) / n_seeds,
        "runtime_units": "hour", "time_unit": "hour",
        "seed_list": seed_list, "seeds_used": n_seeds,
        "win": H - 0.25 * H,
        "arr": tot_arr / n_seeds, "dep": tot_dep / n_seeds, "blk": tot_blk / n_seeds,
        "busy_util": sum(per_bf) / n_seeds, "busy_occupied": sum(per_bf) / n_seeds,
        "dep_rate": (tot_dep / n_seeds) / (H - 0.25 * H),
        "lam_eff": (tot_dep / n_seeds) / (H - 0.25 * H),
        "p_loss": (tot_blk / n_seeds) / max(tot_arr / n_seeds, 1e-12),
        "p_wait": sum(per_pw) / n_seeds,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
