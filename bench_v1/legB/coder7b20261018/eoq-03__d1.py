import sys
import json
import random
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1000)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_q = []
    per_seed_cost = []

    for seed in seed_list:
        random.seed(seed)
        demand_rate = 1000 / args.horizon
        order_cost = 50
        holding_cost = 10

        q = (2 * order_cost * demand_rate) ** 0.5 / holding_cost
        cost = (order_cost * demand_rate / q + holding_cost * q / 2) * args.horizon

        per_seed_q.append(q)
        per_seed_cost.append(cost)

    output = {
        "cost": per_seed_cost,
        "q": per_seed_q,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour"
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
