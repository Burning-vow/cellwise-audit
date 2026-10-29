import argparse, json, random, math, statistics, time

def sim_day(q, rng):
    d = rng.gauss(60.0, 15.0)
    if d < 0: d = 0.0
    sold = min(q, d)
    return sold * 30.0 - q * 12.0 - max(0.0, q - d) * 4.0

def run_seed(seed, horizon, q):
    rng = random.Random(seed)
    warm = horizon * 0.25
    total = 0.0
    n = 0
    for t in range(horizon):
        p = sim_day(q, rng)
        if t >= warm:
            total += p
            n += 1
    return total / n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=400)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    N = int(a.seeds); H = int(a.horizon); S = int(a.seed_start)
    mu, sd, price, cost, salvage = 60.0, 15.0, 30.0, 12.0, 4.0
    if a.pert == "lam_up": mu += 6.0
    elif a.pert == "mu_up": mu += 6.0
    elif a.pert == "c_up": cost += 2.0
    cu = price - cost
    co = cost - salvage
    frac = cu / (cu + co)
    z = statistics.NormalDist().inv_cdf(frac)
    q_opt = mu + sd * z
    t0 = time.time()
    per = [run_seed(S + i, H, q_opt) for i in range(N)]
    seeds_used = len(per)
    seed_list = list(range(S, S + seeds_used))
    exp_profit = sum(per) / seeds_used
    print(json.dumps({
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": time.time() - t0,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_exp_profit": per,
        "per_seed_q": [q_opt] * seeds_used
    }))

if __name__ == "__main__":
    main()
