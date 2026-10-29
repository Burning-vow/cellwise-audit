import json, random, math, argparse

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    mu_d, sd_d = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 4.0
    if args.pert == "lam_up":
        mu_d = mu_d * 1.2
    elif args.pert == "mu_up":
        price = price * 1.1
    elif args.pert == "c_up":
        cost = cost * 1.15

    cu = price - cost
    co = cost - salvage
    ratio = cu / (cu + co)
    z = 0.0
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < ratio:
            lo = mid
        else:
            hi = mid
    z = 0.5 * (lo + hi)
    q_opt = mu_d + z * sd_d

    def expected_profit(q):
        a = (q - mu_d) / sd_d
        b = (-mu_d) / sd_d
        e_sales = mu_d * (norm_cdf(a) - norm_cdf(b)) - sd_d * (norm_pdf(a) - norm_pdf(b))
        e_sales = min(e_sales, q)
        e_left = q - e_sales
        return price * e_sales + salvage * e_left - cost * q

    exp_profit = expected_profit(q_opt)

    horizon = float(args.horizon)
    n_seeds = int(args.seeds)
    seed_list = [args.seed_start + i for i in range(n_seeds)]
    per_seed_exp_profit = []
    per_seed_q = []
    warm = 0.25
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        total_profit = 0.0
        total_days = 0
        while t < horizon:
            day_len = 1.0
            t += day_len
            if t <= warm * horizon:
                continue
            d = rng.gauss(mu_d, sd_d)
            sales = min(d, q_opt)
            left = q_opt - sales
            profit = price * sales + salvage * left - cost * q_opt
            total_profit += profit
            total_days += 1
        if total_days > 0:
            per_seed_exp_profit.append(total_profit / total_days)
        else:
            per_seed_exp_profit.append(0.0)
        per_seed_q.append(q_opt)

    out = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
