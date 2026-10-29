import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = int(args.horizon) if args.horizon == int(args.horizon) else 100
    S = args.seed_start
    pert = args.pert

    mu_d = 60.0
    sigma_d = 15.0
    p = 30.0
    c = 12.0
    s = 7.0

    if pert == 'lam_up':
        mu_d *= 1.1
    elif pert == 'mu_up':
        pass
    elif pert == 'c_up':
        c *= 1.1

    cu = p - c
    co = c - s
    critical_ratio = cu / (cu + co)

    from statistics import NormalDist
    nd = NormalDist(mu_d, sigma_d)
    q_opt = nd.inv_cdf(critical_ratio)
    q_opt = max(0, round(q_opt))

    def expected_profit(q):
        total = 0.0
        for i in range(H):
            rng = random.Random(S + i * 1000 + 1)
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(q, demand)
            leftover = max(0, q - demand)
            profit = p * sold + s * leftover - c * q
            total += profit
        return total / H

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []

    for k in range(N):
        seed_val = S + k
        rng = random.Random(seed_val)
        profits = []
        for day in range(H):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0, demand)
            sold = min(q_opt, demand)
            leftover = max(0, q_opt - demand)
            profit = p * sold + s * leftover - c * q_opt
            profits.append(profit)
        
        warmup = int(H * 0.25)
        valid_profits = profits[warmup:] if warmup < len(profits) else profits
        avg_profit = sum(valid_profits) / len(valid_profits) if valid_profits else 0.0
        
        per_seed_exp_profit.append(round(avg_profit, 4))
        per_seed_q.append(q_opt)
        seed_list.append(seed_val)

    exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": round(exp_profit, 4),
        "q": q_opt,
        "runtime_units": H * N,
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()
