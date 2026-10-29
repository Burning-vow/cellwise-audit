import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5.0)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds)
    H = float(a.horizon)
    lam, mu, c = 10.0, 10.0, 2
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    t_warm = 0.25 * H
    win = H - t_warm
    seed_list, per_L, per_W, per_bf, per_pw, per_pl = [], [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    for k in range(n_seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        N = 0
        busy_ids = []
        queue = []
        t = 0.0
        next_arr = rng.expovariate(lam)
        L_int = 0.0
        busy_int = 0.0
        idle_int = 0.0
        W_sum = W_n = 0
        arr_cnt = dep_cnt = wait_cnt = arr_win = 0
        while True:
            t_dep = min(busy_ids) if busy_ids else math.inf
            t_next = min(next_arr, t_dep)
            if t_next > H and t >= t_warm:
                break
            if t_next <= H:
                lo = max(t, t_warm)
                hi = min(t_next, H)
                if hi > lo:
                    dt = hi - lo
                    L_int += N * dt
                    busy_int += min(N, c) * dt
                    if N == 0:
                        idle_int += dt
                if t_next == next_arr:
                    t = next_arr
                    svc = rng.expovariate(mu)
                    if t >= t_warm and t < H:
                        arr_win += 1
                        if N >= c:
                            wait_cnt += 1
                    cust = (t, svc)
                    if len(busy_ids) < c:
                        start = t
                        if cust[0] >= t_warm and cust[0] < H:
                            W_sum += (start + svc - cust[0])
                            W_n += 1
                        heapq.heappush(busy_ids, t + svc)
                    else:
                        queue.append(cust)
                    N += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    t = t_dep
                    heapq.heappop(busy_ids)
                    N -= 1
                    if t >= t_warm and t <= H:
                        dep_cnt += 1
                    if queue:
                        cust = queue.pop(0)
                        svc = cust[1]
                        if cust[0] >= t_warm and cust[0] < H:
                            W_sum += (t + svc - cust[0])
                            W_n += 1
                        heapq.heappush(busy_ids, t + svc)
            else:
                t = H
                lo = max(t, t_warm)
                if H > lo:
                    dt = H - lo
                    L_int += N * dt
                    busy_int += min(N, c) * dt
                    if N == 0:
                        idle_int += dt
                break
        p_w = wait_cnt / arr_win if arr_win > 0 else 0.0
        L_v = L_int / win if win > 0 else 0.0
        W_v = W_sum / W_n if W_n > 0 else 0.0
        bf = busy_int / (c * win) if win > 0 else 0.0
        per_L.append(L_v); per_W.append(W_v); per_bf.append(bf)
        per_pw.append(p_w); per_pl.append(0.0)
        tot_arr += arr_win; tot_dep += dep_cnt; tot_blk += 0.0
    n = n_seeds
    out = {
        "L": sum(per_L) / n, "W": sum(per_W) / n,
        "busy_frac": sum(per_bf) / n,
        "p_wait": sum(per_pw) / n,
        "busy_util": sum(per_bf) / n,
        "busy_occupied": 1.0 - (sum(1.0 - per_bf[i] * c for i in range(n)) / n if False else 0.0),
        "runtime_units": H * n,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win,
        "arr": tot_arr / n, "dep": tot_dep / n, "blk": tot_blk / n,
        "dep_rate": (tot_dep / n) / win,
        "lam_eff": (tot_arr / n) / win,
        "p_loss": 0.0,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    out["busy_occupied"] = 1.0 - (out["busy_occupied"] if False else 0.0)
    idle = []
    print(json.dumps(out))

if __name__ == "__main__":
    main()
