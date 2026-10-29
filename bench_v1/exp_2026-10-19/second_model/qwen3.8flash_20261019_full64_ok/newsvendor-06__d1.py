import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 25.0
    p = 30.0
    c = 12.0
    s = 7.0

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        sigma_d *= 1.1
    elif args.pert == "c_up":
        c *= 1.1

    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)

    def norm_ppf(p_val):
        return random.gauss(0, 1) * 1.0 

    # Use standard normal inverse CDF approximation or just use statistics? 
    # We need optimal q for newsvendor: F(q) = critical_ratio => q = mu + sigma * Z(critical_ratio)
    # Since we can't import scipy, we approximate the inverse normal CDF.
    
    def inv_norm_cdf(p_val):
        # Rational approximation for central range
        if p_val <= 0.0: return -float('inf')
        if p_val >= 1.0: return float('inf')
        
        # Coefficients for rational approximation
        a = [3.3871328727963666080, 1.3314166789178437745e+2, 1.9715909503065514427e+3,
             1.3735013053123737574e+4, 4.5921953931549871457e+4, 6.7265770927008700853e+4,
             3.3600134016312645824e+4]
        b = [1.0, 4.2313330701600911252e+1, 6.8718700749205797832e+2, 5.3941960214247511077e+3,
             2.1213794301584595146e+4, 3.9307895800092710610e+4, 2.8729085735721942674e+4]
        c_ = [2.5066282774592355e-1, 2.5066282774592355e-1, 2.5066282774592355e-1, 2.5066282774592355e-1,
              2.5066282774592355e-1, 2.5066282774592355e-1, 2.5066282774592355e-1]
        d = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        
        # This is getting complex to implement from scratch accurately without libraries.
        # Alternative: Monte Carlo simulation to find best q among integers?
        # Or use a simpler approximation.
        
        # Let's use a simple lookup/interpolation or Newton-Raphson on erf?
        # Actually, for Newsvendor, we can simulate profit for a range of q and pick max.
        pass

    # Strategy: Simulate days for a set of candidate q values to find optimal q empirically.
    # But the problem asks for "optimal order quantity". Analytical solution is better.
    # q* = mu + sigma * Phi^{-1}(critical_ratio)
    
    # Approximation of Phi^{-1} using Abramowitz and Stegun formula 26.2.23
    def approx_inv_norm(p_val):
        if p_val < 0.5:
            return -approx_inv_norm(1.0 - p_val)
        t = math.sqrt(-2.0 * math.log(1.0 - p_val))
        c0, c1, c2 = 2.515517, 0.802853, 0.010328
        d1, d2, d3 = 1.432788, 0.189269, 0.001308
        return t - (c0 + c1*t + c2*t*t) / (1.0 + d1*t + d2*t*t + d3*t*t*t)

    z_score = approx_inv_norm(critical_ratio)
    optimal_q_float = mu_d + sigma_d * z_score
    optimal_q = int(round(optimal_q_float))
    
    # Calculate expected profit analytically or via simulation?
    # Expected Profit E[Profit(q)] = p*E[min(D,q)] - c*q + s*E[max(q-D,0)]
    # E[min(D,q)] = integral... 
    # For Normal distribution, there are closed forms involving PDF and CDF.
    # E[min(D,q)] = mu * Phi((q-mu)/sigma) - sigma * phi((q-mu)/sigma) ... wait.
    # Let X ~ N(mu, sigma^2). E[min(X, q)] = mu * Phi(z) - sigma * phi(z) + q * (1 - Phi(z))? No.
    # Standard result: E[(X-q)^+] = sigma * phi(z) - (q-mu)*(1-Phi(z)) where z=(q-mu)/sigma?
    # Let's stick to simulation for robustness given the constraints, but analytical is faster.
    # However, the prompt implies a discrete event simulation context ("discrete event simulation engineer").
    # But this is a static optimization problem per day.
    # I will compute expected profit by simulating many days with the fixed optimal q.
    
    num_days = int(args.horizon)
    if num_days < 100: num_days = 100
    
    total_profit = 0.0
    count = 0
    
    # Warmup removal logic: remove first 25%
    warmup_count = int(num_days * 0.25)
    
    seed_list = []
    per_seed_profits = []
    per_seed_qs = []
    
    current_seed = args.seed_start
    
    for i in range(args.seeds):
        rng = random.Random(current_seed)
        seed_list.append(current_seed)
        current_seed += 1
        
        daily_profits = []
        for _ in range(num_days):
            demand = rng.gauss(mu_d, sigma_d)
            if demand < 0: demand = 0
            
            sold = min(demand, optimal_q)
            leftover = max(0, optimal_q - demand)
            
            revenue = p * sold
            cost = c * optimal_q
            salvage = s * leftover
            
            profit = revenue - cost + salvage
            daily_profits.append(profit)
            
        # Remove warmup
        valid_profits = daily_profits[warmup_count:]
        if not valid_profits:
            avg_p = sum(daily_profits) / len(daily_profits)
        else:
            avg_p = sum(valid_profits) / len(valid_profits)
            
        per_seed_profits.append(avg_p)
        per_seed_qs.append(optimal_q)
        total_profit += avg_p
        count += 1
        
    exp_profit = total_profit / count if count > 0 else 0.0
    
    output = {
        "exp_profit": round(exp_profit, 2),
        "q": optimal_q,
        "runtime_units": num_days,
        "seed_list": seed_list,
        "seeds_used": count,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 2) for x in per_seed_profits],
        "per_seed_q": per_seed_qs
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
