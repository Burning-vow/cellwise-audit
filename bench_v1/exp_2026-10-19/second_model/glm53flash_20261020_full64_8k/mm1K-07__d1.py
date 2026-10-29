import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--horizon", type=lambda x: float(x), default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, K = 6.0, 10.0, 6
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1

    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list, tot_arr, tot_blk, tot_dep = [], 0.0, 0.0, 0.0
    burn = 0.25 * a.horizon

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        depq = []
        arr_cnt = blk_cnt = dep_cnt = wait_cnt = 0
        area = 0.0
        busy = 0.0
        win_arr = win_blk = win_dep = win_wait = 0
        win_area = 0.0
        win_busy = 0.0
        W_sum = 0.0
        W_n = 0
        while t < a.horizon:
            t_next_arr = next_arr
            t_next_dep = depq[0] if depq else math.inf
            tn = min(t_next_arr, t_next_dep, a.horizon)
            dt = tn - t
            if tn > burn:
                win_area += n * dt
                if n > 0:
                    win_busy += dt
            t = tn
            if t >= a.horizon:
                break
            if t_next_arr <= t_next_dep:
                if tn > burn:
                    win_arr += 1
                if n < K:
                    n += 1
                    st = rng.expovariate(mu)
                    heapq.heappush(depq, tn + st)
                    if tn > burn:
                        wait_cnt += 1
                else:
                    if tn > burn:
                        win_blk += 1
                next_arr = tn + rng.expovariate(lam)
            else:
                heapq.heappop(depq)
                n -= 1
                if tn > burn:
                    win_dep += 1
        win = a.horizon - burn
        L = win_area / win
        busy_frac = win_busy / win
        p_loss = win_blk / win_arr if win_arr > 0 else 0.0
        p_wait = win_dep / win_arr if win_arr > 0 else 0.0
        lam_eff = win_dep / win
        W = L / lam_eff * 60.0
        seed_list.append(s)
        per_L.append(L); per_W.append(W); per_busy.append(busy_frac)
        per_ploss.append(p_loss); per_pwait.append(p_wait)
        tot_arr += win_arr; tot_blk += win_blk; tot_dep += win_dep

    m = a.seeds
    out = {
        "L": sum(per_L) / m,
        "W": sum(per_W) / m,
        "busy_frac": sum(per_busy) / m,
        "p_loss": sum(per_ploss) / m,
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": m,
        "time_unit": "hour",
        "win": a.horizon - burn,
        "arr": tot_arr / m,
        "blk": tot_blk / m,
        "busy_util": sum(per_busy) / m,
        "busy_occupied": sum(per_busy) / m,
        "dep": tot_dep / m,
        "dep_rate": tot_dep / m / (a.horizon - burn),
        "lam_eff": tot_dep / m / (a.horizon - burn),
        "p_wait": sum(per_pwait) / m,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
