import argparse, json, random, math, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=200000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 0.1; mu = 0.2; K = 6
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    warm = 0.25 * H; win = H - warm
    seed_list = list(range(S, S + n_seeds))
    pL = []; pW = []; pB = []; pPL = []; pPW = []
    arrs = []; deps = []; blks = []
    for seed in seed_list:
        rng = random.Random(seed)
        t = 0.0; N = 0
        ta = rng.expovariate(lam); td = math.inf
        area = 0.0; busy_area = 0.0
        arr = 0; dep = 0; blk = 0; wait_sum = 0.0; waits = 0.0
        nw = 0; wait_acc = 0.0
        while t < H:
            tn = ta if ta < td else td
            if tn >= H:
                dt = H - t
                if t >= warm:
                    area += N * dt
                    if N > 0: busy_area += dt
                t = H; break
            dt = tn - t
            if t >= warm:
                area += N * dt
                if N > 0: busy_area += dt
            t = tn
            if ta <= td:
                if t >= warm: arr += 1
                if N < K:
                    st = rng.expovariate(mu)
                    if N == 0:
                        td = t + st
                    else:
                        if t >= warm:
                            nw += 1; wait_acc += 0.0
                    N += 1
                    ta = t + rng.expovariate(lam)
                else:
                    if t >= warm: blk += 1
                    ta = t + rng.expovariate(lam)
            else:
                N -= 1
                if t >= warm: dep += 1
                if N == 0: td = math.inf
                else: td = t + rng.expovariate(mu)
                ta = ta
            if ta <= t: ta = t + rng.expovariate(lam)
        L = area / win
        bf = busy_area / win
        p_loss = blk / arr if arr > 0 else 0.0
        dep_rate = dep / win
        lam_eff = lam * (1 - p_loss)
        W = L / lam_eff * 60.0 if lam_eff > 0 else 0.0
        p_wait = 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(p_loss); pPW.append(p_wait)
        arrs.append(arr); deps.append(dep); blks.append(blk)
    n = len(seed_list)
    out = {
        "L": sum(pL)/n, "W": sum(pW)/n, "busy_frac": sum(pB)/n,
        "p_loss": sum(pPL)/n, "runtime_units": H, "seed_list": seed_list,
        "seeds_used": n, "time_unit": "minute", "win": win,
        "arr": sum(arrs)/n, "blk": sum(blks)/n, "busy_util": sum(pB)/n,
        "busy_occupied": sum(pB)/n, "dep": sum(deps)/n,
        "dep_rate": sum(deps)/n/win, "lam_eff": lam*(1-sum(pPL)/n),
        "p_wait": 0.0,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": pPL, "per_seed_p_wait": pPW,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
