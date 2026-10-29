import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu = 6.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.1
    warm = 0.25 * H
    Ls, Ws, BFs, PWs, PLs = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        busy_until = None
        queue = []
        area_N = 0.0; area_B = 0.0
        arr_w = dep_w = blk_w = 0
        served_wait = 0; served_n = 0
        wait_sum = 0.0
        last = 0.0
        def integrate(t):
            nonlocal area_N, area_B, last
            area_N += (t - last) * (len(queue) + (1 if busy_until is not None and busy_until > last else 0))
            area_B += (t - last) * (1 if busy_until is not None and busy_until > last else 0)
            last = t
        while True:
            dep_t = busy_until if busy_until is not None else math.inf
            t_next = min(next_arr, dep_t, H)
            if t_next >= H:
                integrate(H); break
            integrate(t_next)
            t = t_next
            if t == next_arr:
                svc = rng.expovariate(mu)
                if busy_until is None:
                    busy_until = t + svc
                    if t >= warm:
                        served_wait += 0; served_n += 1
                else:
                    heapq.heappush(queue, (t, svc))
                if t >= warm: arr_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = dep_t
                if queue:
                    at, svc = heapq.heappop(queue)
                    if t >= warm:
                        served_n += 1
                        wait_sum += (t - at) + svc
                    busy_until = t + svc
                else:
                    busy_until = None
                if t >= warm:
                    dep_w += 1
        win = H - warm
        L = area_N / win
        BF = area_B / win
        W = (wait_sum / served_n) if served_n > 0 else 0.0
        p_wait = (served_n and sum(1 for _ in [0])) and (wait_sum > 0) or 0.0
        pw = (served_n and (wait_sum > 0)) or 0.0
        Ls.append(L); Ws.append(W); BFs.append(BF); PLs.append(0.0); PWs.append(pw)
        tot_arr += arr_w / n_seeds; tot_dep += dep_w / n_seeds; tot_blk += blk_w / n_seeds
    out = {
        "L": sum(Ls)/len(Ls), "W": sum(Ws)/len(Ws), "busy_frac": sum(BFs)/len(BFs),
        "p_wait": sum(PWs)/len(PWs), "runtime_units": H, "seed_list": seed_list,
        "seeds_used": n_seeds, "time_unit": "hour", "win": H - warm,
        "arr": tot_arr, "blk": tot_blk, "busy_util": sum(BFs)/len(BFs),
        "dep": tot_dep, "dep_rate": tot_dep / (H - warm),
        "lam_eff": tot_arr / (H - warm), "p_loss": sum(PLs)/len(PLs),
        "per_seed_L": Ls, "per_seed_W": Ws, "per_seed_busy_frac": BFs,
        "per_seed_p_loss": PLs, "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
