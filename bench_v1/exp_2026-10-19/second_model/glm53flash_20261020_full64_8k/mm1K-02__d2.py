import argparse, json, math, random, sys

def run_seed(seed, H, lam, mu, K):
    rng = random.Random(seed)
    warm = 0.25 * H
    t = 0.0
    next_arr = rng.expovariate(lam)
    dep = math.inf
    N = 0
    queue = []
    area = 0.0
    busy_area = 0.0
    last = 0.0
    arr = 0
    dep_c = 0
    blk = 0
    waitsum = 0.0
    waited = 0
    served = 0

    def adv(t2):
        nonlocal area, busy_area, last
        a = max(last, warm)
        b = min(t2, H)
        if b > a:
            area += N * (b - a)
            if N > 0:
                busy_area += (b - a)
        last = t2

    while True:
        t2 = min(next_arr, dep, H)
        if t2 >= H:
            adv(H)
            break
        adv(t2)
        t = t2
        inwin = t >= warm
        if next_arr <= dep:
            next_arr = t + rng.expovariate(lam)
            if inwin:
                arr += 1
            if N < K:
                s = rng.expovariate(mu)
                queue.append([t, s])
                N += 1
                if dep == math.inf:
                    it = queue.pop(0)
                    dep = t + it[1]
                    dep_start = (t, it[0])
            else:
                if inwin:
                    blk += 1
        else:
            dep_c += 1 if inwin else 0
            served += 1 if inwin else 0
            w = dep_start[0] - dep_start[1]
            if inwin:
                waitsum += w
                if w > 0:
                    waited += 1
            N -= 1
            if queue:
                it = queue.pop(0)
                dep_start = (t, it[0])
                dep = t + it[1]
            else:
                dep = math.inf
    win = H - warm
    L = area / win
    busy_frac = busy_area / win
    busy_util = busy_area / win / 1.0
    p_loss = blk / arr if arr > 0 else 0.0
    W = (waitsum / served) * 60.0 if served > 0 else 0.0
    p_wait = waited / dep_c if dep_c > 0 else 0.0
    lam_eff = dep_c / win
    dep_rate = dep_c / win
    return {"L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
            "p_wait": p_wait, "arr": arr, "dep": dep_c, "blk": blk,
            "lam_eff": lam_eff, "dep_rate": dep_rate, "busy_util": busy_util}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 6.0
    mu = 12.0
    K = 4
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        K = 5
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per = []
    for s in seeds:
        per.append(run_seed(s, a.horizon, lam, mu, K))
    n = len(per)
    out = {
        "L": sum(r["L"] for r in per) / n,
        "W": sum(r["W"] for r in per) / n,
        "busy_frac": sum(r["busy_frac"] for r in per) / n,
        "p_loss": sum(r["p_loss"] for r in per) / n,
        "p_wait": sum(r["p_wait"] for r in per) / n,
        "arr": sum(r["arr"] for r in per) / n,
        "dep": sum(r["dep"] for r in per) / n,
        "blk": sum(r["blk"] for r in per) / n,
        "lam_eff": sum(r["lam_eff"] for r in per) / n,
        "dep_rate": sum(r["dep_rate"] for r in per) / n,
        "busy_util": sum(r["busy_util"] for r in per) / n,
        "runtime_units": a.horizon,
        "seed_list": seeds,
        "seeds_used": n,
        "time_unit": "hour",
        "win": 0.75 * a.horizon,
        "per_seed_L": [r["L"] for r in per],
        "per_seed_W": [r["W"] for r in per],
        "per_seed_busy_frac": [r["busy_frac"] for r in per],
        "per_seed_p_loss": [r["p_loss"] for r in per],
        "per_seed_p_wait": [r["p_wait"] for r in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
