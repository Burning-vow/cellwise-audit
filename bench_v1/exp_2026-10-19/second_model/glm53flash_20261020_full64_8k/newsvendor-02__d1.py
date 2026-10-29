import argparse, json, math, random, time

def sim_profit(seed, q, days, warmup_frac=0.25):
    rng = random.Random(seed)
    n_warm = int(days * warmup_frac)
    tot = 0.0
    cnt = 0
    for d in range(days):
        demand = rng.gauss(60.0, 25.0)
        if demand < 0:
            demand = 0.0
        sold = min(q, demand)
        profit = 20.0 * sold + 7.0 * max(0.0, q - demand) - 12.0 * q
        if d >= n_warm:
            tot += profit
            cnt += 1
    return tot / cnt if cnt > 0 else 0.0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=2000)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    args = p.parse_args()

    mu, sd, price, cost, salvage = 60.0, 25.0, 20.0, 12.0, 7.0
    lam_adj, mu_adj, c_adj = 1.0, 1.0, 1.0
    if args.pert == "lam_up":
        lam_adj = 1.1
    elif args.pert == "mu_up":
        mu_adj = 1.1
    elif args.pert == "c_up":
        c_adj = 1.05
    price *= lam_adj
    cost *= mu_adj
    salvage *= c_adj

    t0 = time.time()
    days = int(max(1, round(args.horizon)))
    seeds = [args.seed_start + i for i in range(args.seeds)]

    fractile = (price - cost) / ((price - cost) + (cost - salvage))
    z = _norm_ppf(fractile)
    q_theory = mu + sd * z

    best_q = None
    best_val = -1e18
    lo = max(0, int(q_theory - 25))
    hi = int(q_theory + 25) + 1
    base_seed = seeds[0]
    for q in range(lo, hi):
        val = sim_profit(base_seed, q, days)
        if val > best_val:
            best_val = val
            best_q = q

    per_seed_q = []
    per_seed_ep = []
    for s in seeds:
        bq = None
        bv = -1e18
        for q in range(max(0, best_q - 3), best_q + 4):
            v = sim_profit(s, q, days)
            if v > bv:
                bv = v
                bq = q
        per_seed_q.append(bq)
        per_seed_ep.append(sim_profit(s, bq, days))

    exp_profit = sum(per_seed_ep) / len(per_seed_ep)
    q_hat = sum(per_seed_q) / len(per_seed_q)
    out = {
        "exp_profit": exp_profit,
        "q": q_hat,
        "runtime_units": days,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit_fix(per_seed_ep),
        "per_seed_q": per_seed_q,
        "q_theory": q_theory,
    }
    print(json.dumps(out))

def per_seed_exp_profit_fix(a):
    return list(a)

if __name__ == "__main__":
    main()
