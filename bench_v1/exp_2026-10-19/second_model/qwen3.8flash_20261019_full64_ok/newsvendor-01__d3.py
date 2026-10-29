import argparse, json, math, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=1.0)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    price = 20.0
    cost = 12.0
    salvage = 7.0

    if args.pert == "lam_up":
        mu_d *= 1.1
    elif args.pert == "mu_up":
        pass
    elif args.pert == "c_up":
        cost *= 1.1

    cu = price - cost
    co = cost - salvage
    critical_ratio = cu / (cu + co)

    def norm_ppf(p):
        return math.sqrt(2) * erfinv(2*p - 1)

    def erfinv(x):
        # Approximation for inverse error function
        a = 0.147
        ln_x = math.log(1 - x*x)
        t1 = 2/(math.pi*a) + ln_x/2
        t2 = ln_x/a
        return math.copysign(math.sqrt(math.sqrt(t1*t1 - t2) - t1), x)

    q_optimal = mu_d + sigma_d * norm_ppf(critical_ratio)
    q_int = int(round(q_optimal))

    per_seed_exp_profit = []
    per_seed_q = []
    seed_list = []

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        total_profit = 0.0
        n_days = max(1, int(args.horizon))
        
        for _ in range(n_days):
            demand = rng.gauss(mu_d, sigma_d)
            demand = max(0.0, demand)
            sold = min(demand, q_int)
            leftover = max(0.0, q_int - demand)
            profit = price * sold + salvage * leftover - cost * q_int
            total_profit += profit
        
        avg_profit = total_profit / n_days
        per_seed_exp_profit.append(avg_profit)
        per_seed_q.append(q_int)
        seed_list.append(seed)

    exp_profit = sum(per_seed_exp_profit) / len(per_seed_exp_profit) if per_seed_exp_profit else 0.0

    result = {
        "exp_profit": exp_profit,
        "q": q_int,
        "runtime_units": args.horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_exp_profit,
        "per_seed_q": per_seed_q
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()
