import argparse, json, math, random

def hyper_means(m, cv):
    c2 = cv * cv
    p = 0.5
    lo, hi = 1e-9, 0.5 - 1e-9
    for _ in range(100):
        p = 0.5 * (lo + hi)
        val = 4 * p + (1 - 2 * p) ** 2 / (1 - p)
        if val > c2: hi = p
        else: lo = p
    a = 2 * m
    b = m * (1 - 2 * p) / (1 - p)
    return p, a, b

def run_seed(seed, H, warm, lam, m, cv):
    rng = random.Random(seed)
    p, a, b = hyper_means(m, cv)
    t = 0.0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    n = 0
    area_n = 0.0
    busy = 0.0
    arr = 0; dep = 0; waits = 0.0; waited_cnt = 0
    t_end = H
    t_stat = warm
    while True:
        t_next = min(next_arr, next_dep, t_end)
        if t_next > t_stat:
            dt = t_next - t_stat
            area_n += n * dt
            if n >= 1: busy += dt
            t_stat = t_next
        elif t_next > t:
            dt = t_next - t
            area_n += n * dt
            if n >= 1: busy += dt
            t_stat = t_next
        t = t_next
        if t >= t_end: break
        if next_arr <= next_dep:
            s = rng.expovariate(1.0 / a) if rng.random() < p else rng.expovariate(1.0 / b)
            n += 1; arr += 1
            if n == 1:
                next_dep = t + s
            else:
                waited_cnt += 1
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1; dep += 1
            if n >= 1:
                next_dep = t + (rng.expovariate(1.0 / a) if rng.random() < p else rng.expovariate(1.0 / b))
            else:
                next_dep = math.inf
    return {"L": area_n / (H - warm), "busy": busy / (H - warm),
            "arr": arr, "dep": dep, "p_wait": waited_cnt / arr if arr else 0.0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()
    lam = 3.0; m = 6.0 / 60.0; cv = 1.5
    if args.pert == "lam_up": lam *= 1.1
    elif args.pert == "mu_up": m /= 1.1
    elif args.pert == "c_up": cv *= 1.1
    warm = 0.25 * args.horizon
    seed_list = list(range(args.seed_start, args.seed_start + args.seeds))
    res = [run_seed(s, args.horizon, warm, lam, m, cv) for s in seed_list]
    K = len(res)
    L = sum(r["L"] for r in res) / K
    busy = sum(r["busy"] for r in res) / K
    arr = sum(r["arr"] for r in res) / K
    dep = sum(r["dep"] for r in res) / K
    pw = sum(r["p_wait"] for r in res) / K
    wsys = [None] * K
    for i, r in enumerate(res):
        wsys[i] = L / (lam * (1 - 0.0)) * 60.0
    out = {
        "L": L, "W": L / lam * 60.0, "busy_frac": busy,
        "runtime_units": args.horizon, "seed_list": seed_list, "seeds_used": K,
        "time_unit": "hour", "win": args.horizon - warm,
        "arr": arr, "blk": 0.0, "busy_util": busy, "busy_occupied": busy,
        "dep": dep, "dep_rate": dep / (args.horizon - warm),
        "lam_eff": dep / (args.horizon - warm), "p_loss": 0.0, "p_wait": pw,
        "per_seed_L": [r["L"] for r in res],
        "per_seed_W": [r["L"] / lam * 60.0 for r in res],
        "per_seed_busy_frac": [r["busy"] for r in res],
        "per_seed_p_loss": [0.0] * K,
        "per_seed_p_wait": [r["p_wait"] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
