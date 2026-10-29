import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    N = args.seeds
    H = int(args.horizon)
    S = args.seed_start
    pert = args.pert

    mu_d = 60.0
    sigma_d = 15.0
    price = 30.0
    cost = 12.0
    salvage = 7.0

    if pert == "lam_up":
        mu_d *= 1.1
    elif pert == "mu_up":
        pass
    elif pert == "c_up":
        cost *= 1.1

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        # Approximation for inverse normal CDF using rational approximation
        if p <= 0: return -1e9
        if p >= 1: return 1e9
        t = math.sqrt(-2 * math.log(1 - p)) if p < 0.5 else math.sqrt(-2 * math.log(p))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        z = t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t)
        if p < 0.5:
            return -z
        else:
            return z

    q_opt = mu_d + sigma_d * norm_ppf(critical_ratio)
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []

    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        total_profit = 0.0
        days = H
        for _ in range(days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            total_profit += profit
        avg_profit = total_profit / days
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(seed)

    exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()
