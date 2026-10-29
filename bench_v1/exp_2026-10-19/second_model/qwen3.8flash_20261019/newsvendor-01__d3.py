import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    p = 20.0
    c = 12.0
    s = 7.0

    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)

    def norm_ppf(p_val):
        if p_val <= 0: return float('-inf')
        if p_val >= 1: return float('inf')
        # Approximation for inverse normal CDF using rational approximation
        # Abramowitz and Stegun formula 26.2.23
        t = math.sqrt(-2 * math.log(1 - p_val)) if p_val < 0.5 else math.sqrt(-2 * math.log(p_val))
        # Better approach: use standard library? No, only stdlib allowed but no scipy/numpy.
        # We can approximate or use a simple iterative method.
        # Let's use a robust approximation for the probit function.
        # Using the algorithm from Peter John Acklam's paper (approximate)
        # Or simpler: since we need optimal q, we can just solve Phi((q-mu)/sigma) = CR
        # So (q-mu)/sigma = Phi^{-1}(CR)
        
        # Implementing a decent approximation for Phi^{-1}
        if p_val < 0.5:
            sign = -1
            p_val = 1 - p_val
        else:
            sign = 1
        
        # Rational approximation coefficients
        a1 = -39.69683028665376
        a2 = 220.94609842452057
        a3 = -275.9285104469687
        a4 = 138.3577518672690
        a5 = -30.66479806614716
        b1 = -54.47609879822406
        b2 = 161.5821368580409
        b3 = -155.68952057187107
        b4 = 66.95617667838171
        b5 = -13.760568349120902
        c1 = -0.0077848940028323846
        c2 = -0.32239645804113649
        c3 = -2.400758277161838
        c4 = -2.5497325393437345
        d1 = 0.007784695709041462
        d2 = 0.3224671290700398
        d3 = 2.445134299056471
        d4 = 3.7851358835223963

        plow = 0.02425
        phigh = 1 - plow

        if p_val < plow:
            q = math.sqrt(-2 * math.log(p_val))
            x = (((((c1*q+c2)*q+c3)*q+c4)*q+1) / ((((d1*q+d2)*q+d3)*q+d4)*q+1))
        elif p_val <= phigh:
            q = p_val - 0.5
            r = q*q
            x = (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+1) * q / (((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1)
        else:
            q = math.sqrt(-2 * math.log(1 - p_val))
            x = -(((((c1*q+c2)*q+c3)*q+c4)*q+1) / ((((d1*q+d2)*q+d3)*q+d4)*q+1))
            
        return sign * x

    z_opt = norm_ppf(critical_ratio)
    q_opt = mu_d + z_opt * sigma_d
    
    # Calculate expected profit analytically for newsvendor model with normal demand
    # E[Profit] = (p-c)q - (p-s)E[(q-D)^+] ... wait, let's use the standard formula
    # Profit = p*min(D,q) + s*(q-D)^+ - c*q
    # E[Profit] = (p-s)E[min(D,q)] + (s-c)q
    # For Normal D ~ N(mu, sigma^2):
    # E[min(D,q)] = mu - sigma * phi(z) - (mu-q)*(1-Phi(z)) where z=(q-mu)/sigma? 
    # Actually: E[min(D,q)] = q - E[(D-q)^+]
    # E[(D-q)^+] = sigma * [phi(z) - z*(1-Phi(z))] where z = (q-mu)/sigma
    # Let's compute directly.
    
    z = (q_opt - mu_d) / sigma_d
    phi_z = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    # Phi(z) is approximated by critical_ratio at optimum, but let's be precise for general q
    # We need Phi(z). Let's implement a CDF approximation too.
    
    def norm_cdf(x):
        # Approximation of error function
        t = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        erf_approx = 1.0 - poly * math.exp(-x*x/2.0) / math.sqrt(math.pi) * 2.0 # Wait, this is not quite right.
        
        # Standard approximation for Phi(x)
        if x < 0:
            return 1.0 - norm_cdf(-x)
        k = 1.0 / (1.0 + 0.2316419 * x)
        poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))))
        return 1.0 - poly * math.exp(-x*x/2.0) / math.sqrt(2*math.pi)

    Phi_z = norm_cdf(z)
    
    # Expected Shortage E[(D-q)^+] = sigma * (phi(z) - z*(1-Phi(z)))
    exp_shortage = sigma_d * (phi_z - z * (1 - Phi_z))
    
    # E[Sales] = E[min(D,q)] = q - E[(q-D)^+] ? No.
    # E[min(D,q)] = integral_0^q x f(x) dx + q * P(D>q)
    # Also E[D] = E[min(D,q)] + E[(D-q)^+]
    # So E[min(D,q)] = mu_d - exp_shortage
    
    exp_sales = mu_d - exp_shortage
    
    # Profit = p * Sales + s * Leftover - c * q
    # Leftover = q - Sales
    # Profit = p * Sales + s * (q - Sales) - c * q
    # Profit = (p - s) * Sales + (s - c) * q
    
    exp_profit_analytical = (p - s) * exp_sales + (s - c) * q_opt

    # Now simulate to get per-seed estimates
    seeds_used = args.seeds
    seed_list = []
    per_seed_exp_profit = []
    per_seed_q = []
    
    horizon_days = int(args.horizon) # Assuming horizon is in days for this problem context, though time_unit says hour/min/sec. 
    # The prompt asks for time_unit. Since it's daily ordering, "day" isn't an option. 
    # I will treat the simulation as running for H "units". If H is large, it's many days.
    # Let's assume 1 unit = 1 day for simplicity in counting, but report time_unit as 'hour' or similar? 
    # Prompt says: time_unit fill your internal timeline unit (hour/minute/second).
    # This is a static optimization problem essentially. But they ask for simulation.
    # I'll simulate `horizon` days. Each day is one event.
    # To satisfy "time_unit", I'll say 'hour' and assume 24 hours per day? Or just treat each iteration as 1 unit.
    # Let's stick to iterating `horizon` times.
    
    num_iterations = max(1, int(args.horizon))
    
    for i in range(seeds_used):
        current_seed = args.seed_start + i
        seed_list.append(current_seed)
        rng = random.Random(current_seed)
        
        total_profit = 0.0
        count = 0
        
        # Warmup: discard first 25%
        warmup_count = int(num_iterations * 0.25)
        
        for j in range(num_iterations):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand) # Demand cannot be negative
            
            sales = min(demand, q_opt)
            leftover = q_opt - sales
            
            profit = p * sales + s * leftover - c * q_opt
            
            if j >= warmup_count:
                total_profit += profit
                count += 1
                
        avg_profit = total_profit / count if count > 0 else 0.0
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_opt)

    overall_avg_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": round(overall_avg_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": num_iterations,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour", # Arbitrary choice as per options, simulating discrete steps
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
