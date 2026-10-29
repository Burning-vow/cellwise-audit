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
        order_cost = 50
        holding_cost = 2

        if args.pert == 'lam_up':
            demand_rate *= 1.1
        elif args.pert == 'mu_up':
            order_cost *= 1.1
        elif args.pert == 'c_up':
            holding_cost *= 1.1

        EOQ = (2 * order_cost * demand_rate / holding_cost) ** 0.5
        cost = EOQ * order_cost + (args.horizon / EOQ) * holding_cost

        per_seed_q.append(EOQ)
        per_seed_cost.append(cost)

    runtime_units = 'hour'
    cost = sum(per_seed_cost) / seeds_used
    q = sum(per_seed_q) / seeds_used

    output = {
        'cost': cost,
        'q': q,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': runtime_units,
        'per_seed_q': per_seed_q,
        'per_seed_cost': per_seed_cost
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
