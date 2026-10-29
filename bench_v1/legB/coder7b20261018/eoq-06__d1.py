import sys
import json
import random
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=5000)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_q = []
    per_seed_cost = []

    for seed in seed_list:
        random.seed(seed)
        demand_rate = 5000 / args.horizon
        order_cost = 200
        holding_cost = 2

        if args.pert == 'lam_up':
            demand_rate *= 1.1
        elif args.pert == 'mu_up':
            order_cost *= 1.1
        elif args.pert == 'c_up':
            holding_cost *= 1.1

        q = (2 * order_cost * demand_rate) ** 0.5 / holding_cost
        cost = (order_cost * args.horizon / q + holding_cost * q / 2) * demand_rate

        per_seed_q.append(q)
        per_seed_cost.append(cost)

    cost = sum(per_seed_cost) / seeds_used
    q = sum(per_seed_q) / seeds_used

    print(json.dumps({
        "cost": cost,
        "q": q,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q,
        "per_seed_cost": per_seed_cost
    }))

if __name__ == "__main__":
    main()
