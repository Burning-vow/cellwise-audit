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
    seeds = 30
    horizon = 1000.0
    seed_start = 1
    pert = "none"
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--seeds":
            seeds = int(args[i+1]); i += 2
        elif a == "--horizon":
            horizon = float(args[i+1]); i += 2
        elif a == "--seed-start":
            seed_start = int(args[i+1]); i += 2
        elif a == "--pert":
            pert = args[i+1]; i += 2
        else:
            i += 1
    mu_d = 60.0
    sd_d = 15.0
    price = 20.0
    cost = 12.0
    salvage = 7.0
    if pert == "lam_up":
        mu_d = 60.0 * 1.2
    elif pert == "mu_up":
        price = 20.0 * 1.1
    elif pert == "c_up":
        cost = 12.0 * 1.1
    cu = price - cost
    co = cost - salvage
    crit = cu / (cu + co)
    q = mu_d + sd_d * norm_ppf(crit)
    q = max(0.0, q)
    per_seed_profit = []
    per_seed_q = []
    seed_list = []
    t0 = time.time()
    for s in range(seeds):
        seed = seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        total_profit = 0.0
        days = 0
        t = 0.0
        while t < horizon:
            d = rng.gauss(mu_d, sd_d)
            if d < 0:
                d = 0.0
            sold = min(q, d)
            leftover = q - sold
            profit = price * sold + salvage * leftover - cost * q
            total_profit += profit
            days += 1
            t += 1.0
        if days == 0:
            days = 1
        per_seed_profit.append(total_profit / days)
        per_seed_q.append(q)
    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    runtime_units = time.time() - t0
    out = {
        "exp_profit": exp_profit,
        "q": q,
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "second",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
