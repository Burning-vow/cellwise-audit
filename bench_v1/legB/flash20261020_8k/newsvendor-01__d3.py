import json, math, random, sys, time

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_ppf(p):
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

def main():
    args = sys.argv[1:]
    seeds_n = 30
    horizon = 1000.0
    seed_start = 1
    pert = "none"
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--seeds":
            seeds_n = int(args[i+1]); i += 2
        elif a == "--horizon":
            horizon = float(args[i+1]); i += 2
        elif a == "--seed-start":
            seed_start = int(args[i+1]); i += 2
        elif a == "--pert":
            pert = args[i+1]; i += 2
        else:
            i += 1

    mu = 60.0
    sigma = 15.0
    price = 20.0
    cost = 12.0
    salvage = 7.0
    if pert == "lam_up":
        mu = mu * 1.1
    elif pert == "mu_up":
        mu = mu * 1.1
    elif pert == "c_up":
        cost = cost * 1.1

    cu = price - cost
    co = cost - salvage
    ratio = cu / (cu + co)
    q_opt = mu + sigma * norm_ppf(ratio)

    def sim_one(seed):
        rng = random.Random(seed)
        warm = 0.25 * horizon
        total_profit = 0.0
        count = 0
        t = 0.0
        while t < horizon:
            demand = rng.gauss(mu, sigma)
            sold = min(q_opt, demand)
            leftover = max(0.0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            if t >= warm:
                total_profit += profit
                count += 1
            t += 1.0
        if count == 0:
            return 0.0, q_opt
        return total_profit / count, q_opt

    per_seed_profit = []
    per_seed_q = []
    seed_list = []
    for k in range(seeds_n):
        s = seed_start + k
        seed_list.append(s)
        p, q = sim_one(s)
        per_seed_profit.append(p)
        per_seed_q.append(q)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    out = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
