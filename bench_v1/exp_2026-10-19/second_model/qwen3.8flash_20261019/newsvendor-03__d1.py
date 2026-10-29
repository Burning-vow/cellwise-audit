import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 4.0
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        sigma_d *= 1.1
    elif args.pert == "c_up":
        cost *= 1.1
        cu = price - cost
        co = cost - salvage
        crit_ratio = cu / (cu + co)

    def norm_ppf(p):
        return random.gauss(0, 1) * sigma_d + mu_d

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    total_profit_sum = 0.0
    total_days = 0

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        days = int(args.horizon)
        warmup = int(days * 0.25)
        day_profits = []
        best_q = None
        best_profit = -float('inf')

        # For each day, we need to find optimal q analytically or via search
        # Since demand is normal, optimal q satisfies P(D <= q) = crit_ratio
        # We can approximate using inverse CDF of standard normal
        # But since we're simulating, let's just compute expected profit for a given q
        # Actually, the problem asks for optimal q and expected daily profit
        # Let's do a grid search over q values
        
        # Precompute: for a fixed q, expected profit = E[price*min(D,q) + salvage*max(q-D,0) - cost*q]
        # = price*E[min(D,q)] + salvage*E[max(q-D,0)] - cost*q
        # E[min(D,q)] = integral from -inf to q of x*f(x)dx + q*(1-F(q))
        # This is complex; instead simulate many days with different q values? 
        # No, better: use analytical approximation for normal distribution.
        
        # For normal D ~ N(mu, sigma), optimal q* = mu + sigma * z where Phi(z) = crit_ratio
        # Approximate z using simple method
        z = _approx_norm_ppf(crit_ratio)
        q_opt = mu_d + sigma_d * z
        q_int = round(q_opt)
        
        # Simulate to get expected profit at this q
        profits_at_q = []
        for d in range(days):
            demand = rng.gauss(mu_d, sigma_d)
            sold = min(demand, q_int)
            leftover = max(q_int - demand, 0)
            profit = price * sold + salvage * leftover - cost * q_int
            profits_at_q.append(profit)
        
        # Discard warmup
        steady_profits = profits_at_q[warmup:]
        avg_profit = sum(steady_profits) / len(steady_profits) if steady_profits else 0
        
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(float(q_int))
        seed_list.append(seed)
        total_profit_sum += avg_profit
        total_days += 1

    exp_profit = total_profit_sum / total_days if total_days > 0 else 0.0
    q_val = sum(per_seed_q) / len(per_seed_q) if per_seed_q else 0.0

    result = {
        "exp_profit": round(exp_profit, 2),
        "q": round(q_val, 2),
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": [round(p, 2) for p in per_seed_exp_profit],
        "per_seed_q": [round(q, 2) for q in per_seed_q]
    }
    print(json.dumps(result))

def _approx_norm_ppf(p):
    # Simple approximation for inverse normal CDF
    if p <= 0:
        return -3.0
    if p >= 1:
        return 3.0
    # Use rational approximation
    t = math.sqrt(-2.0 * math.log(1.0 - p)) if p < 0.5 else math.sqrt(-2.0 * math.log(p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    approx = t - (c0 + c1*t + c2*t*t) / (1.0 + d1*t + d2*t*t + d3*t*t*t)
    return approx if p < 0.5 else -approx

if __name__ == "__main__":
    main()
