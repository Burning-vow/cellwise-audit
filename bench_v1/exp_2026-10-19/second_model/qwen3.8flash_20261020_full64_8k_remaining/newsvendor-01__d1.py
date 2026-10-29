import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = int(args.horizon) if args.horizon == int(args.horizon) else 1000
    S = args.seed_start
    pert = args.pert

    mu_d = 60.0
    sigma_d = 15.0
    price = 20.0
    cost = 12.0
    salvage = 7.0

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        if p <= 0: return -math.inf
        if p >= 1: return math.inf
        a = [-3.969181017e+01, 2.209460928e+02, -2.759285104e+02, 1.383577518e+02, -3.066479806e+01, 2.506628270e+00]
        b = [-5.447609879e+01, 1.615858368e+02, -1.556989598e+02, 6.680131188e+01, -1.328068155e+01]
        c = [-7.784894002e-03, -3.223964580e-01, -2.400758277e+00, -2.549732539e+00, 4.374664141e+00, 2.938163982e+00]
        d = [7.784695709e-03, 3.224671290e-01, 2.445134137e+00, 3.754408661e+00]
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

    z_opt = norm_ppf(critical_ratio)
    q_opt = mu_d + z_opt * sigma_d
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

    exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit)

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
