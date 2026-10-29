import argparse, json, math, random
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    mu_d, sigma_d, price, cost, salvage = 60.0, 25.0, 20.0, 12.0, 7.0
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)
    q_opt = int(round(mu_d + sigma_d * _norm_ppf(crit_ratio)))
    exp_profit = _calc_exp_profit(q_opt, mu_d, sigma_d, price, cost, salvage)
    per_seed_exp_profit = []
    per_seed_q = []
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        profits = []
        qs = []
        days = int(a.horizon)
        if days <= 0: days = 1
        warmup = int(days * 0.25)
        total_profit = 0.0
        count = 0
        for d in range(days):
            demand = max(0, rng.gauss(mu_d, sigma_d))
            q = q_opt
            sold = min(demand, q)
            leftover = q - sold
            profit = price * sold + salvage * leftover - cost * q
            if d >= warmup:
                total_profit += profit
                count += 1
        avg_p = total_profit / count if count > 0 else 0.0
        per_seed_exp_profit.append(avg_p)
        per_seed_q.append(q_opt)
    out = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "runtime_units": a.horizon,
        "seed_list": [a.seed_start + i for i in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

def _norm_ppf(p):
    # Approximation of inverse normal CDF using rational approximation
    if p <= 0: return -float('inf')
    if p >= 1: return float('inf')
    if p < 0.5:
        return -_norm_ppf(1-p)
    t = math.sqrt(-2 * math.log(1-p))
    c0, c1, c2 = 2.307347976, 0.2708874353, 0.9928905293
    d0, d1, d2 = 0.9978214893, 0.0000000000, 0.0000000000 # Simplified coefficients for standard approx
    # Using a more robust simple approximation or lookup? 
    # Let's use a simpler polynomial approximation for accuracy within reasonable bounds
    # Abramowitz and Stegun formula 26.2.23
    if p < 0.5:
       sign = -1
       p_val = p
    else:
       sign = 1
       p_val = 1-p
    
    t = math.sqrt(-2*math.log(p_val))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    x = t - (c0 + c1*t + c2*t*t)/(1 + d1*t + d2*t*t + d3*t*t*t)
    return sign * x

def _calc_exp_profit(q, mu, sigma, price, cost, salvage):
    # E[Profit] = price*E[min(D,q)] + salvage*E[max(q-D,0)] - cost*q
    # E[min(D,q)] = integral from 0 to q of x f(x) dx + q * P(D>q)
    # For Normal distribution, we can use numerical integration or closed form with Phi/phi
    # Closed form:
    # E[min(D,q)] = mu * Phi((q-mu)/sigma) - sigma * phi((q-mu)/sigma) + q * (1 - Phi((q-mu)/sigma))
    # Wait, standard result: E[min(X,c)] = c - integral_c^inf (x-c)f(x)dx ...
    # Let's use the property: E[min(D,q)] = q - E[max(D-q, 0)]
    # E[max(D-q, 0)] = sigma * phi(z) + (mu-q)*(1-Phi(z)) where z=(q-mu)/sigma
    z = (q - mu) / sigma
    phi_z = math.exp(-0.5*z*z) / math.sqrt(2*math.pi)
    Phi_z = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    # Expected Sales = E[min(D, q)]
    # Formula: mu * Phi(z) - sigma * phi(z) + q * (1 - Phi(z)) is incorrect derivation above.
    # Correct: E[min(D,q)] = q - (mu-q)*Phi(z) - sigma*phi(z) ? No.
    # Let D ~ N(mu, sigma).
    # E[min(D,q)] = integral_{-inf}^{q} x f(x) dx + q * P(D>q)
    # integral_{-inf}^{q} x f(x) dx = mu * Phi(z) - sigma * phi(z)
    # So E[min(D,q)] = mu * Phi(z) - sigma * phi(z) + q * (1 - Phi(z))
    
    exp_sales = mu * Phi_z - sigma * phi_z + q * (1 - Phi_z)
    exp_leftover = q - exp_sales
    exp_profit = price * exp_sales + salvage * exp_leftover - cost * q
    return exp_profit

if __name__ == "__main__":
    main()
