import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    p = 30.0
    c = 12.0
    s = 7.0

    if args.pert == 'lam_up':
        mu_d *= 1.1
    elif args.pert == 'mu_up':
        pass # no change for newsvendor static params in this context usually, but perturbation might affect demand mean/std? 
              # The prompt says "pert NAME, NAME takes none/lam_up/mu_up/c_up". 
              # For Newsvendor, lam is likely demand mean, mu is likely... maybe cost? or just noise?
              # Let's assume standard mapping: lam -> demand mean, mu -> demand std? Or maybe mu is service rate?
              # In Newsvendor, there is no service rate. 
              # Let's interpret: lam_up increases demand mean. mu_up increases demand std? c_up increases cost?
              # Actually, let's look at the parameters: p, c, s are fixed costs/prices. Demand is Normal(mu, sigma).
              # Common perturbations:
              # lam_up: increase demand mean (lambda often denotes arrival rate/demand rate)
              # mu_up: increase demand std (sigma)? Or maybe it's a typo for sigma? 
              # c_up: increase unit cost c.
              # Let's implement:
              # lam_up: mu_d += 10%
              # mu_up: sigma_d += 10% (assuming mu refers to variability parameter here as there is no service rate)
              # c_up: c += 10%
    elif args.pert == 'mu_up':
        sigma_d *= 1.1
    elif args.pert == 'c_up':
        c *= 1.1
    
    # Optimal q for continuous normal demand:
    # Critical fractile F(q*) = (p - c) / (p - s)
    # q* = mu + sigma * Z_inv(F)
    
    critical_ratio = (p - c) / (p - s)
    # Find inverse CDF of standard normal for critical_ratio
    # Using approximation for probit function since scipy is not allowed
    def norm_ppf(p_val):
        # Rational approximation for central range
        if p_val <= 0: return -float('inf')
        if p_val >= 1: return float('inf')
        
        # Coefficients for rational approximation
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556987298549569e+02,
             6.680131188771972e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
             3.754403040875998e+00]
        
        p_low = 0.02425
        p_high = 1 - p_low
        
        if p_val < p_low:
            q = math.sqrt(-2 * math.log(p_val))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p_val <= p_high:
            q = p_val - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        else:
            q = math.sqrt(-2 * math.log(1 - p_val))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    z_score = norm_ppf(critical_ratio)
    optimal_q = mu_d + sigma_d * z_score
    
    # Calculate Expected Profit analytically for Normal Distribution
    # E[Profit] = p * E[min(D, q)] - c * q + s * E[max(0, q - D)]
    # E[min(D, q)] = mu - sigma * L(z) where L(z) is loss function? 
    # Alternatively:
    # E[Sales] = mu * Phi(z) - sigma * phi(z) + q * (1 - Phi(z))? No.
    # Standard formula for expected profit with salvage value:
    # E[Pi] = (p-s)*E[min(D,q)] + (s-c)*q
    # E[min(D,q)] = mu * Phi(z) - sigma * phi(z) + q * (1 - Phi(z)) -- wait, q = mu + sigma*z
    # Let's use: E[min(D,q)] = mu - sigma * (phi(z) - z*(1-Phi(z))) ?
    # Actually, simpler:
    # E[Profit] = p * E[min(D,q)] - c*q + s * (q - E[min(D,q)])
    #           = (p-s) * E[min(D,q)] + (s-c) * q
    # E[min(D,q)] = integral_{-inf}^{q} x f(x) dx + q * P(D>q)
    # For Normal(mu, sigma), let z = (q-mu)/sigma
    # E[min(D,q)] = mu * Phi(z) - sigma * phi(z) + q * (1 - Phi(z))
    #             = mu * Phi(z) - sigma * phi(z) + (mu + sigma*z) * (1 - Phi(z))
    #             = mu - sigma * phi(z) + sigma * z * (1 - Phi(z))
    #             = mu - sigma * (phi(z) - z * (1 - Phi(z)))
    
    from math import exp, sqrt, pi
    def pdf_std_normal(x):
        return exp(-x*x/2) / sqrt(2*pi)
    
    def cdf_std_normal(x):
        # Approximation using erf
        return 0.5 * (1 + math.erf(x / sqrt(2)))
        
    phi_z = pdf_std_normal(z_score)
    Phi_z = cdf_std_normal(z_score)
    
    E_min_D_q = mu_d - sigma_d * (phi_z - z_score * (1 - Phi_z))
    
    exp_profit_analytical = (p - s) * E_min_D_q + (s - c) * optimal_q
    
    # Simulation part to satisfy "per_seed" requirements and verify
    seeds_used = []
    per_seed_exp_profit = []
    per_seed_q = []
    
    horizon_days = int(args.horizon) # Assuming horizon is number of days if time_unit is day? 
    # Prompt says time_unit is hour/minute/second. But Newsvendor is daily.
    # Let's set time_unit to 'day' equivalent? No, must be hour/min/sec.
    # We can treat 1 simulation step = 1 day. If we say time_unit='day', it violates constraint.
    # Constraint: "time_unit fill your program internal timeline unit (hour/minute/second)".
    # So we must map days to one of these. Let's say 1 day = 24 hours.
    # Horizon H is in hours. Number of days = H / 24.
    
    time_unit = 'hour'
    steps_per_day = 24
    total_hours = args.horizon
    num_days = int(total_hours // steps_per_day)
    
    if num_days < 1:
        num_days = 1
        
    burn_in_fraction = 0.25
    burn_in_days = int(num_days * burn_in_fraction)
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # Use the analytical optimal q for all simulations as it's the decision variable
        current_q = optimal_q
        
        profits = []
        for d in range(num_days):
            # Generate demand
            demand = rng.gauss(mu_d, sigma_d)
            if demand < 0: demand = 0
            
            sales = min(demand, current_q)
            leftover = max(0, current_q - demand)
            
            profit = p * sales + s * leftover - c * current_q
            profits.append(profit)
            
        # Discard burn-in
        valid_profits = profits[burn_in_days:]
        if len(valid_profits) > 0:
            avg_profit = sum(valid_profits) / len(valid_profits)
        else:
            avg_profit = 0.0
            
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(current_q)
        
    overall_avg_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0
    
    result = {
        "exp_profit": round(overall_avg_profit, 4),
        "q": round(optimal_q, 4),
        "runtime_units": total_hours,
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": time_unit,
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp_profit],
        "per_seed_q": [round(x, 4) for x in per_seed_q]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
