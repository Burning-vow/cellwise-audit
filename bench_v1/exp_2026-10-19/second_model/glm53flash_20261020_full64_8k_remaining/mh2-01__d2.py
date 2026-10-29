import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    lam = 3.0
    if pert == "lam_up": lam *= 1.1
    mu_scale = 1.0
    if pert == "mu_up": mu_scale = 1.1
    c_scale = 1.0
    if pert == "c_up": c_scale = 1.1
    m = 6.0 * mu_scale
    cv = 1.5 * c_scale
    c2 = cv * cv
    p = 0.5 * (1.0 + math.sqrt((c2 - 1.0) / (c2 + 1.0)))
    m1 = 2.0 * p * m
    m2 = 2.0 * (1.0 - p) * m
    r1, r2 = 60.0 / m1, 60.0 / m2
    warm = H * 0.25
    win = H - warm
    Ls, Ws, Bs, PLs, PWs = [], [], [], [], []
    seed_list = []
    arr_tots, dep_tots, blk_tots = 0.0, 0.0, 0.0
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed * 2654435761 % (2**32) + 12345)
        t = 0.0; queue = []; busy_until = None; n = 0
        area = 0.0; busy_t = 0.0; last = 0.0
        arr = dep = blk = 0
        wait_sums = 0.0; wait_n = 0
        next_arr = rng.expovariate(lam)
        while True:
            nt = next_arr
            nd = busy_until if busy_until is not None else float("inf")
            if min(nt, nd) > H and n == 0:
                break
            if nt <= nd:
                t = nt
                if t <= warm:
                    pass
                area += n * (t - last) if last >= warm else n * max(0.0, t - warm)
                if last < warm:
                    busy_t += max(0.0, min(t, warm + 0) - warm) if n > 0 else 0.0
                else:
                    busy_t += (t - last) if n > 0 else 0.0
                last = t
                arr += 1
                u = rng.random()
                s = (1.0 / r1) if u < p else (1.0 / r2)
                if n == 0:
                    busy_until = t + s
                    wait_sums += 0.0; wait_n += 1
                else:
                    queue.append((t, s))
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = nd
                if t <= warm:
                    pass
                area += n * (t - last) if last >= warm else n * max(0.0, t - warm)
                if last < warm:
                    busy_t += max(0.0, t - warm) if n > 0 else 0.0
                else:
                    busy_t += (t - last) if n > 0 else 0.0
                last = t
                dep += 1
                n -= 1
                if queue:
                    at, s = queue.pop(0)
                    wait_sums += (t - at); wait_n += 1
                    busy_until = t + s
                else:
                    busy_until = None
        L = area / win
        B = busy_t / win
        W = (wait_sums / wait_n) * 60.0 if wait_n else 0.0
        pw = (wait_n - (dep)) and 0
        p_wait = sum(1 for i in range(wait_n) if True)
        pw_est = (wait_sums > 0) and 0
        pw_count = 0
        Ls.append(L); Ws.append(W); Bs.append(B)
        PLs.append(blk / arr if arr else 0.0)
        PWs.append(wait_frac)
        arr_tots += arr; dep_tots += dep; blk_tots += blk
    print(json.dumps({"L": sum(Ls)/n_seeds, "W": sum(Ws)/n_seeds, "busy_frac": sum(Bs)/n_seeds,
        "busy_util": sum(Bs)/n_seeds, "busy_occupied": sum(Bs)/n_seeds,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": n_seeds,
        "time_unit": "hour", "win": win, "arr": arr_tots/n_seeds, "blk": blk_tots/n_seeds,
        "busy_util2": sum(Bs)/n_seeds, "dep": dep_tots/n_seeds,
        "dep_rate": dep_tots/n_seeds/win, "lam_eff": arr_tots/n_seeds/win,
        "p_loss": blk_tots/arr_tots if arr_tots else 0.0,
        "p_wait": sum(PWs)/n_seeds,
        "per_seed_L": Ls, "per_seed_W": Ws, "per_seed_busy_frac": Bs,
        "per_seed_p_loss": PLs, "per_seed_p_wait": PWs}))

if __name__ == "__main__":
    main()
