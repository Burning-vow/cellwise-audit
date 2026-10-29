import sys, json, math, random
from argparse import ArgumentParser

def main():
    p = ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add('--seed-start', type=int, default=42)
    p.add('--pert', type=str, default='none')
    a = p.parse_args()
    
    mu_d = 60.0
    sigma_d = 15.0
    price = 30.0
    cost = 12.0
    salvage = 4.0
    
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)
    
    # Inverse normal approximation for optimal q
    # Using standard library only. We can use statistics.NormalDist if available in py3.8+
    try:
        from statistics import NormalDist
        nd = NormalDist(mu_d, sigma_d)
        q_opt = nd.inv_cdf(crit_ratio)
    except ImportError:
        # Fallback simple approximation or just use mean if critical ratio is 0.5? 
        # CR = 18/26 = 9/13 ~ 0.69. Z ~ 0.5.
        # Let's implement a basic inverse CDF approximation for robustness if needed, 
        # but usually stdlib has it. If not, we simulate to find best q among candidates.
        pass

    # Since the problem asks for "optimal order quantity" and "expected daily profit",
    # and it's a newsvendor model, the analytical solution is preferred.
    # However, the prompt implies a simulation context ("discrete event simulation engineer", "warm-up", "per_seed").
    # But Newsvendor is a static optimization per day. The "simulation" here likely means simulating many days
    # to estimate the expected profit for a given q, or perhaps optimizing q via simulation.
    # Given "output requirements" ask for `q` and `exp_profit`, and `per_seed_q`, it suggests we might be 
    # estimating these values via simulation over multiple seeds/days.
    
    # Let's interpret: We need to find the optimal q. For Newsvendor, q* is fixed by distribution parameters.
    # Then we calculate E[Profit] at q*.
    # The "simulation" aspect with seeds/warmup/horizon suggests we should simulate the daily sales process
    # to verify/calculate the expected profit, rather than just using the closed-form integral.
    # Or, more likely, the task is to *simulate* the store operation over H days (horizon) for N seeds,
    # determine the best q (maybe via grid search or just using the theoretical one?), and report stats.
    # But "optimal order quantity" is a single value. 
    
    # Let's assume the standard approach: Calculate theoretical q*, then simulate to get expected profit.
    # Or, since it's a simulation task, maybe we simulate for a range of q and pick the best?
    # The output requires `q`. If we use theoretical q, `per_seed_q` would be constant.
    # If we optimize via simulation, `per_seed_q` might vary slightly due to noise.
    
    # Let's stick to the most robust interpretation for a "simulation engineer":
    # 1. Determine optimal q analytically (it's deterministic based on params).
    # 2. Simulate the daily demand/profit process for each seed over the horizon to estimate Expected Profit.
    # 3. Report the analytical q and the simulated average profit.
    
    # Wait, the prompt says "service duration must be drawn at arrival". This is generic DES boilerplate.
    # For Newsvendor, there are no "arrivals" in the queueing sense. It's a daily cycle.
    # I will treat each "day" as an event.
    
    # Re-reading carefully: "Newsvendor-03". 
    # Output keys: exp_profit, q, runtime_units, seed_list, seeds_used, time_unit, per_seed_exp_profit, per_seed_q.
    
    # Strategy:
    # Use the analytical formula for q.
    # Simulate `horizon` days for each seed.
    # Each day: Draw Demand ~ N(60, 15). Calculate Profit(q, D).
    # Accumulate profit.
    # Warm-up: Discard first 25% of days.
    # Average remaining profits -> exp_profit for that seed.
    # Final exp_profit = average of per_seed_exp_profit.
    # q is the same for all seeds (analytical).
    
    if 'nd' not in locals():
        # Manual inverse normal approximation if NormalDist missing (unlikely in modern python)
        # Just use a rough guess or raise error. Assuming Python 3.8+.
        raise Exception("NormalDist required")

    q_star = round(q_opt) # Order quantities are integers usually, but problem doesn't specify integer constraint explicitly. 
                          # "个" implies integer. Let's keep float for calculation, round for reporting? 
                          # Usually continuous approximation is fine. Let's use float q_opt.
    
    # Actually, let's look at the perturbation. `lam_up`, `mu_up`, `c_up`.
    # These modify parameters.
    # lam_up: increase demand mean?
    # mu_up: increase service rate? Not applicable directly. Maybe increase demand variance? Or cost?
    # c_up: increase cost?
    
    # Let's map perturbations to parameters:
    # none: base
    # lam_up: mu_d *= 1.1
    # mu_up: sigma_d *= 1.1 (uncertainty up?) OR maybe cost changes? 
    #       In queueing, mu is service rate. Here, maybe "supply reliability"? 
    #       Let's assume mu_up increases the "mean" of something else? 
    #       Standard mapping: lambda=demand rate, mu=service rate.
    #       Here, demand is stochastic. 
    #       Let's assume:
    #       lam_up: mu_d += 10%
    #       mu_up: sigma_d += 10% (harder to predict?) OR maybe salvage price?
    #       c_up: cost += 10%
    
    # Let's refine parameter updates based on names:
    # lam_up -> Lambda (Demand Mean) Up
    # mu_up -> Mu (Service Rate/Capacity?) Up. In Newsvendor, capacity is infinite unless constrained. 
    #          Maybe it refers to the "cost" parameter? No, c_up exists.
    #          Maybe it refers to the "salvage" value? 
    #          Let's assume mu_up affects the standard deviation (volatility) or simply isn't used in this specific static model structure differently.
    #          However, to be safe, I'll map:
    #          lam_up: mu_d *= 1.1
    #          mu_up: sigma_d *= 1.1 (interpreting mu as variability factor? Unlikely.)
    #          Let's look at standard queueing: lambda arrival, mu service.
    #          Here, no service. 
    #          Let's assume:
    #          lam_up: mu_d *= 1.1
    #          mu_up: cost *= 1.1 (No, c_up is cost).
    #          Maybe mu_up: salvage *= 1.1?
    #          Let's just implement simple multiplicative factors for the named parameters if they exist, otherwise ignore.
    #          Actually, `mu` often denotes mean in some contexts, but `lam` is also mean.
    #          Let's assume:
    #          lam_up: mu_d *= 1.1
    #          mu_up: sigma_d *= 1.1 (Volatility)
    #          c_up: cost *= 1.1
    
    if a.pert == 'lam_up':
        mu_d *= 1.1
    elif a.pert == 'mu_up':
        sigma_d *= 1.1
    elif a.pert == 'c_up':
        cost *= 1.1
        
    # Recalculate optimal q with potentially perturbed params
    cu = price - cost
    co = cost - salvage
    if cu + co <= 0:
        crit_ratio = 0.5
    else:
        crit_ratio = cu / (cu + co)
        
    nd = NormalDist(mu_d, sigma_d)
    q_opt = nd.inv_cdf(crit_ratio)
    
    # Simulation
    total_days = int(a.horizon)
    warmup_days = int(total_days * 0.25)
    valid_days = total_days - warmup_days
    
    if valid_days <= 0:
        valid_days = 1
        warmup_days = 0
        
    per_seed_profits = []
    per_seed_qs = []
    seed_list = []
    
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        seed_list.append(s)
        
        daily_profits = []
        for d in range(total_days):
            # Generate demand
            # Box-Muller or use rng.gauss
            demand = rng.gauss(mu_d, sigma_d)
            if demand < 0: demand = 0
            
            sold = min(demand, q_opt)
            leftover = max(0, q_opt - demand)
            
            revenue = sold * price
            salvage_val = leftover * salvage
            total_cost = q_opt * cost
            
            profit = revenue + salvage_val - total_cost
            daily_profits.append(profit)
            
        # Warmup removal
        window_profits = daily_profits[warmup_days:]
        if len(window_profits) > 0:
            avg_p = sum(window_profits) / len(window_profits)
        else:
            avg_p = 0.0
            
        per_seed_profits.append(avg_p)
        per_seed_qs.append(q_opt)
        
    final_exp_profit = sum(per_seed_profits) / len(per_seed_profits) if per_seed_profits else 0.0
    
    result = {
        "exp_profit": final_exp_profit,
        "q": q_opt,
        "runtime_units": "day", # Horizon is in days
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profits,
        "per_seed_q": per_seed_qs
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
