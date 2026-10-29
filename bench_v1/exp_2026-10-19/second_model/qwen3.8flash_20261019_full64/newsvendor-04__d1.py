import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    mu_d = 60.0
    sigma_d = 25.0
    price = 30.0
    cost = 12.0
    salvage = 4.0
    
    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)
    
    # Optimal q via inverse normal approximation or search
    # Using standard normal inverse approximation for simplicity in pure python without scipy
    # Or just grid search since it's a single day problem repeated? 
    # The prompt asks for "optimal order quantity q" and "expected daily profit".
    # This is a static optimization problem, not necessarily a discrete event simulation over time with arrivals/departures queueing logic.
    # However, the system prompt says "Discrete Event Simulation Engineer".
    # But Newsvendor is often solved analytically or by simple Monte Carlo on demand distribution.
    # Let's interpret "Horizon H" as number of days if unit is 'day'? No, time_unit must be hour/minute/second.
    # If we treat each "day" as an event interval, we need to map H to days.
    # Let's assume 1 day = 24 hours. So total days = int(H / 24).
    # But wait, the output requires `q` and `exp_profit`. These are parameters of the optimal policy.
    # Usually, you find q* first, then simulate to get expected profit at q*.
    # Or maybe the simulation estimates the optimal q?
    # Given the constraints "service duration... attached to customer", this sounds like a queueing model description template, but the task is Newsvendor.
    # I will implement a Monte Carlo estimation of the optimal Q and its Expected Profit.
    
    def norm_inv(p):
        # Approximation for inverse CDF of standard normal
        # Rational approximation for central range
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        
        # Coefficients for rational approximation
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 4.494606457085419e-01]
        b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989585806171e+02, 6.680131188771972e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539320758e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
        
        plow = 0.02425
        phigh = 1 - plow
        
        if p < plow:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p > phigh:
            q = math.sqrt(-2 * math.log(1-p))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        else:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

    z_opt = norm_inv(critical_ratio)
    q_opt = mu_d + z_opt * sigma_d
    
    # Simulate to estimate expected profit at q_opt
    # Horizon H is in hours. 1 day = 24 hours.
    num_days = max(1, int(args.horizon / 24.0))
    
    per_seed_profits = []
    per_seed_qs = []
    seeds_used_list = []
    
    for i in range(args.seeds):
        seed_val = args.seed_start + i
        rng = random.Random(seed_val)
        profits = []
        for _ in range(num_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand) # Demand cannot be negative
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            profit = price * sold + salvage * leftover - cost * q_opt
            profits.append(profit)
        
        avg_profit = sum(profits) / len(profits) if profits else 0.0
        per_seed_profits.append(avg_profit)
        per_seed_qs.append(q_opt) # Q is fixed optimal
        seeds_used_list.append(seed_val)
        
    overall_exp_profit = sum(per_seed_profits) / len(per_seed_profits) if per_seed_profits else 0.0
    
    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": round(q_opt, 4),
        "runtime_units": args.horizon,
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": "hour",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_profits],
        "per_seed_q": [round(x, 4) for x in per_seed_qs]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
