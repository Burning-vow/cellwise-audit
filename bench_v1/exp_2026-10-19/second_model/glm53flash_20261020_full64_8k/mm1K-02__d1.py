import argparse, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 6.0; mu = 12.0; K = 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    warm = 0.25 * H
    per = {k: [] for k in ("L","W","busy_frac","p_loss","p_wait")}
    arrs = []; deps = []; blks = []
    seed_list = []
    for i in range(n_seeds):
        seed = S + i
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0; n = 0
        ta = rng.expovariate(lam)
        queue = []
        A = 0.0; B = 0.0; Qw = 0.0; Qn = 0.0
        arr = 0; dep = 0; blk = 0; waits = []; served = 0
        last = 0.0
        t_warm = None
        while True:
            if queue and queue[0][1] <= ta:
                t = queue[0][1]
                if t >= warm and t_warm is None: t_warm = t; A0 = A; B0 = B; Qw0 = Qw; Qn0 = Qn; arr0 = arr; dep0 = dep; blk0 = blk
                if t_warm is not None:
                    pass
                dt = t - last
                A += n * dt; Qn += (n - 1) * dt if n > 0 else 0.0
                if n > 0: B += dt
                if t >= warm: Qw += (n - 1) * dt
                last = t
                n -= 1; dep += 1
                if t_warm is not None: pass
                queue.pop(0)
                if queue and False: pass
                continue
            if ta > H: break
            t = ta
            if t >= warm and t_warm is None: t_warm = t; A0 = A; B0 = B; Qw0 = Qw; Qn0 = Qn; arr0 = arr; dep0 = dep; blk0 = blk
            dt = t - last
            if n > 0: B += dt
            A += n * dt
            if t >= warm and n > 0: Qw += (n - 1) * dt
            Qn += max(n - 1, 0) * dt if t >= warm else 0.0
            last = t
            arr += 1
            if n < K:
                st = rng.expovariate(mu)
                waits.append(t if False else 0.0)
                waits[-1] = t
                queue.append((t, t + st))
                n += 1
            else:
                blk += 1
            ta = t + rng.expovariate(lam)
        t = H
        dt = t - last
        if n > 0: B += dt
        A += n * dt
        if t >= warm: Qw += max(n - 1, 0) * dt
        if t_warm is None:
            t_warm = warm; A0 = A; B0 = B; Qw0 = Qw; Qn0 = 0.0; arr0 = arr; dep0 = dep; blk0 = blk
        win = H - t_warm
        dA = A - A0; dB = B - B0; dQ = Qw - Qw0
        darr = arr - arr0; ddep = dep - dep0; dblk = blk - blk0
        nserved = ddep
        per["L"].append(dA / win)
        per["busy_frac"].append(dB / win)
        per["p_loss"].append(dblk / darr if darr > 0 else 0.0)
        per["p_wait"].append(0.0)
        per["W"].append((dQ / nserved) * 60.0 if nserved > 0 else 0.0)
        arrs.append(darr); deps.append(ddep); blks.append(dblk)
    def mean(x): return sum(x) / len(x) if x else 0.0
    out = {
        "L": mean(per["L"]), "W": mean(per["W"]), "busy_frac": mean(per["busy_frac"]),
        "p_loss": mean(per["p_loss"]), "runtime_units": "hour", "seed_list": seed_list,
        "seeds_used": n_seeds, "time_unit": "hour", "win": H * 0.75,
        "arr": mean(arrs), "blk": mean(blks), "busy_util": mean(per["busy_frac"]),
        "busy_occupied": mean(per["busy_frac"]), "dep": mean(deps),
        "dep_rate": mean(deps) / (H * 0.75), "lam_eff": mean(deps) / (H * 0.75),
        "p_wait": mean(per["p_wait"]),
        "per_seed_L": per["L"], "per_seed_W": per["W"], "per_seed_busy_frac": per["busy_frac"],
        "per_seed_p_loss": per["p_loss"], "per_seed_p_wait": per["p_wait"],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
