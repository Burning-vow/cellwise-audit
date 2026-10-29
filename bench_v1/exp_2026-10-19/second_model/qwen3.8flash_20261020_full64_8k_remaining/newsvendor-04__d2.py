import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1000.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d, sigma_d = 60.0, 25.0
    price, cost, salvage = 30.0, 12.0, 4.0
    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    if args.pert == "lam_up":
        mu_d *= 1.2
    elif args.pert == "mu_up":
        sigma_d *= 1.2
    elif args.pert == "c_up":
        cost *= 1.2
        cu = price - cost
        co = cost - salvage
        critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        return math.sqrt(2) * erfinv(2*p - 1)

    def erfinv(x):
        a = [0.14714899, -0.03877608, 0.00318387]
        b = [-0.00318387, 0.03877608, -0.14714899]
        c = [0.00318387, -0.03877608, 0.14714899]
        d = [-0.00318387, 0.03877608, -0.14714899]
        e = [0.00318387, -0.03877608, 0.14714899]
        f = [-0.00318387, 0.03877608, -0.14714899]
        g = [0.00318387, -0.03877608, 0.14714899]
        h = [-0.00318387, 0.03877608, -0.14714899]
        i = [0.00318387, -0.03877608, 0.14714899]
        j = [-0.00318387, 0.03877608, -0.14714899]
        k = [0.00318387, -0.03877608, 0.14714899]
        l = [-0.00318387, 0.03877608, -0.14714899]
        m = [0.00318387, -0.03877608, 0.14714899]
        n = [-0.00318387, 0.03877608, -0.14714899]
        o = [0.00318387, -0.03877608, 0.14714899]
        p = [-0.00318387, 0.03877608, -0.14714899]
        q = [0.00318387, -0.03877608, 0.14714899]
        r = [-0.00318387, 0.03877608, -0.14714899]
        s = [0.00318387, -0.03877608, 0.14714899]
        t = [-0.00318387, 0.03877608, -0.14714899]
        u = [0.00318387, -0.03877608, 0.14714899]
        v = [-0.00318387, 0.03877608, -0.14714899]
        w = [0.00318387, -0.03877608, 0.14714899]
        x = [-0.00318387, 0.03877608, -0.14714899]
        y = [0.00318387, -0.03877608, 0.14714899]
        z = [-0.00318387, 0.03877608, -0.14714899]
        # Use standard approximation for erfinv
        sign = 1 if x >= 0 else -1
        ax = abs(x)
        if ax < 1e-10:
            return x * math.sqrt(math.pi) / 2
        ln_term = math.log(1 - ax*ax)
        t_val = -ln_term
        if t_val > 0:
            sqrt_t = math.sqrt(t_val)
            result = sqrt_t - (a[0]*sqrt_t + a[1])/(b[0]*sqrt_t + b[1])
            # Better approach: use scipy-like rational approx or just use normal ppf via Box-Muller inverse
            pass
        # Simpler: use the fact that we can compute normal ppf directly
        # Let's use a well-known approximation for normal quantile
        return None

    # Actually, let's use a simpler and more robust method for normal ppf
    # Using the Abramowitz and Stegun approximation or similar
    
    def normal_ppf_approx(p):
        """Approximate inverse of standard normal CDF using rational approximation."""
        if p <= 0:
            return float('-inf')
        if p >= 1:
            return float('inf')
        
        # Coefficients for rational approximation
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 1.094652922400000e+00]
        b = [-5.447609879822407e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188721944e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709031462e-03, 3.224671290700398e-01, 2.400022644564968e+00,
             2.549732539343734e+00]
        
        p_low = 0.02425
        p_high = 1 - p_low
        
        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    # Find optimal q by minimizing expected loss or maximizing expected profit
    # Expected profit(q) = price * E[min(D,q)] - cost * q + salvage * E[max(q-D,0)]
    # = price * (E[D] - E[max(D-q,0)]) - cost * q + salvage * E[max(q-D,0)]
    # Alternatively: profit = revenue from sales - cost of purchase + salvage value
    # Sales = min(D, q), Unsold = max(q - D, 0)
    # Profit = price * min(D,q) - cost * q + salvage * max(q-D,0)
    
    # For normal distribution, we can compute E[min(D,q)] analytically
    # E[min(D,q)] = mu * Phi(z) - sigma * phi(z) where z = (q-mu)/sigma... wait no
    # Actually: E[min(X,a)] = mu*Phi((a-mu)/sigma) - sigma*phi((a-mu)/sigma) ... hmm let me recall
    # For X ~ N(mu, sigma^2):
    # E[X] = mu
    # E[max(X-a,0)] = (mu-a)*Phi((mu-a)/sigma) + sigma*phi((mu-a)/sigma)
    # E[min(X,a)] = a - E[max(a-X,0)] = a - [(a-mu)*Phi((a-mu)/sigma) + sigma*phi((a-mu)/sigma)]
    # Wait: E[max(a-X,0)] when X~N(mu,sigma^2): let Y=a-X, Y~N(a-mu, sigma^2)
    # E[max(Y,0)] = (a-mu)*Phi((a-mu)/sigma) + sigma*phi((a-mu)/sigma)
    # So E[min(X,a)] = a - E[max(a-X,0)] = a - (a-mu)*Phi((a-mu)/sigma) - sigma*phi((a-mu)/sigma)
    
    def phi(z):
        return math.exp(-z*z/2) / math.sqrt(2*math.pi)
    
    def Phi(z):
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    def expected_profit(q):
        z = (q - mu_d) / sigma_d
        # E[min(D,q)] = q - (q-mu_d)*Phi(z) - sigma_d*phi(z)
        # Wait, let me re-derive carefully
        # E[max(q-D,0)] = (q-mu_d)*Phi((q-mu_d)/sigma_d) + sigma_d*phi((q-mu_d)/sigma_d)
        # E[min(D,q)] = E[D] - E[max(D-q,0)] = mu_d - [(mu_d-q)*Phi((mu_d-q)/sigma_d) + sigma_d*phi((mu_d-q)/sigma_d)]
        # Note: Phi(-x) = 1-Phi(x), phi(-x)=phi(x)
        # E[max(D-q,0)] = (mu_d-q)*Phi((mu_d-q)/sigma_d) + sigma_d*phi((mu_d-q)/sigma_d)
        # Let w = (q-mu_d)/sigma_d, then (mu_d-q)/sigma_d = -w
        # E[max(D-q,0)] = (-sigma_d*w)*Phi(-w) + sigma_d*phi(w) = sigma_d*(-w*(1-Phi(w)) + phi(w))
        # E[min(D,q)] = mu_d - sigma_d*(-w*(1-Phi(w)) + phi(w)) = mu_d + sigma_d*w*(1-Phi(w)) - sigma_d*phi(w)
        # Hmm, this is getting messy. Let me use a different form.
        # Standard result: E[min(X,a)] = a*Phi((a-mu)/sigma) + mu*(1-Phi((a-mu)/sigma)) - sigma*phi((a-mu)/sigma)
        # No wait. Let me just use numerical integration or the known formula.
        # 
        # Known: If X~N(mu,sigma^2), then E[(X-a)+] = (mu-a)*Phi((mu-a)/sigma) + sigma*phi((mu-a)/sigma)
        # And E[(a-X)+] = (a-mu)*Phi((a-mu)/sigma) + sigma*phi((a-mu)/sigma)
        # 
        # Profit = price*min(D,q) - cost*q + salvage*max(q-D,0)
        # min(D,q) = D - max(D-q,0)
        # max(q-D,0) = (q-D)+
        # So Profit = price*D - price*max(D-q,0) - cost*q + salvage*max(q-D,0)
        # E[Profit] = price*mu_d - price*E[max(D-q,0)] - cost*q + salvage*E[max(q-D,0)]
        # E[max(D-q,0)] = (mu_d-q)*Phi((mu_d-q)/sigma_d) + sigma_d*phi((mu_d-q)/sigma_d)
        # E[max(q-D,0)] = (q-mu_d)*Phi((q-mu_d)/sigma_d) + sigma_d*phi((q-mu_d)/sigma_d)
        
        w1 = (mu_d - q) / sigma_d
        w2 = (q - mu_d) / sigma_d
        e_shortage = (mu_d - q) * Phi(w1) + sigma_d * phi(w1)
        e_surplus = (q - mu_d) * Phi(w2) + sigma_d * phi(w2)
        return price * mu_d - price * e_shortage - cost * q + salvage * e_surplus

    # Optimal q satisfies F(q*) = critical_ratio, where F is CDF of demand
    # For normal: q* = mu_d + sigma_d * z*, where Phi(z*) = critical_ratio
    z_star = normal_ppf_approx(critical_ratio)
    q_optimal = mu_d + sigma_d * z_star

    # Now simulate to get empirical estimates per seed
    horizon_days = int(args.horizon)
    warmup_fraction = 0.25
    warmup_days = int(horizon_days * warmup_fraction)
    eval_days = horizon_days - warmup_days

    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    per_seed_exp_profit = []
    per_seed_q = []

    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        total_profit = 0.0
        for day in range(horizon_days):
            # Generate demand
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)  # Demand can't be negative
            # Use fixed optimal q
            q = q_optimal
            sales = min(demand, q)
            unsold = max(q - demand, 0)
            daily_profit = price * sales - cost * q + salvage * unsold
            if day >= warmup_days:
                total_profit += daily_profit
        avg_profit = total_profit / eval_days if eval_days > 0 else 0.0
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_optimal)

    overall_exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": round(overall_exp_profit, 4),
        "q": round(q_optimal, 4),
        "runtime_units": horizon_days,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": [round(v, 4) for v in per_seed_exp_profit],
        "per_seed_q": [round(v, 4) for v in per_seed_q]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
