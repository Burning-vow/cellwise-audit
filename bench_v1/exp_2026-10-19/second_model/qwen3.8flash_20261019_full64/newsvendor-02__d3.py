import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    p = 20.0
    c = 12.0
    s = 7.0

    if args.pert == 'lam_up':
        mu_d *= 1.1
    elif args.pert == 'mu_up':
        sigma_d *= 1.1
    elif args.pert == 'c_up':
        c *= 1.1

    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)

    def norm_ppf(p_val):
        # Approximation for inverse normal CDF using rational approximation
        if p_val <= 0: return -math.inf
        if p_val >= 1: return math.inf
        
        # Abramowitz and Stegun approximation 26.2.23
        if p_val < 0.5:
            t = math.sqrt(-2 * math.log(p_val))
            x = -(t - (2.30753 + 0.278843*t)/(1+0.99229*t+0.044815*t**2))
        else:
            t = math.sqrt(-2 * math.log(1-p_val))
            x = t - (2.30753 + 0.278843*t)/(1+0.99229*t+0.044815*t**2)
        return x

    z_star = norm_ppf(critical_ratio)
    q_opt = mu_d + z_star * sigma_d
    q_opt = max(0, round(q_opt))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []
    
    total_days = int(args.horizon)
    if total_days <= 0:
        total_days = 1

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        profits = []
        
        # Simulate days to estimate expected profit at optimal q
        # We use the analytical formula for expected profit of newsvendor with normal demand
        # E[Profit] = (p-c)*mu - (p-s)*sigma*phi(z) - (c-s)*(z*Phi(z)+phi(z))*sigma ... wait simpler:
        # Expected Profit = p*E[min(D,q)] - c*q + s*E[max(0, q-D)]
        # Or standard result: E[Profit] = (p-c)*mu - (p-s)*sigma*(phi(z) - z*(1-Phi(z)))? 
        # Let's just simulate or use exact integral approximation via sampling for robustness as requested "discrete event simulation" style but this is static.
        # The prompt asks for a simulation engineer approach. Let's do Monte Carlo estimation of the profit for the calculated q_opt.
        
        day_profits = []
        warmup_count = int(total_days * 0.25)
        
        for d in range(total_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand) # Demand cannot be negative practically, though normal allows it. Usually truncated or just max(0).
            
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            revenue = p * sold
            cost = c * q_opt
            salvage = s * leftover
            
            profit = revenue - cost + salvage
            day_profits.append(profit)
            
        # Discard warmup
        valid_profits = day_profits[warmup_count:]
        if not valid_profits:
            avg_profit = sum(day_profits)/len(day_profits)
        else:
            avg_profit = sum(valid_profits)/len(valid_profits)
            
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)
        seed_list.append(seed)

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    output = {
        "exp_profit": overall_exp_profit,
        "q": q_opt,
        "runtime_units": total_days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
