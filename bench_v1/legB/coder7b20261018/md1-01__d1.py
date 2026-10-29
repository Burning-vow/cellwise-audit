import sys
import json
import random
from math import exp, factorial

def poisson(lam, k):
    return (lam ** k * exp(-lam)) / factorial(k)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1000)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        lam = 4 / 60
        mu = 1 / 6
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        arr = 0
        dep = 0
        blk = 0
        busy_time = 0
        total_time = 0
        last_arrival = 0
        next_departure = 0

        for t in range(int(args.horizon * 60)):
            if t == next_departure:
                busy_time += t - last_arrival
                last_arrival = t
                next_departure = t + 6
                dep += 1
            elif t == last_arrival:
                if next_departure > t:
                    arr += 1
                else:
                    blk += 1
                    last_arrival = next_departure
                    next_departure += 6

            total_time += 1

        L = arr / total_time
        W = busy_time / dep
        busy_frac = busy_time / total_time
        p_loss = blk / (arr + dep + blk)
        p_wait = (arr - dep) / arr

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    print(json.dumps({
        'L': sum(per_seed_L) / seeds_used,
        'W': sum(per_seed_W) / seeds_used,
        'busy_frac': sum(per_seed_busy_frac) / seeds_used,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': args.horizon,
        'arr': sum(per_seed_L) / seeds_used,
        'dep': sum(per_seed_L) / seeds_used,
        'blk': sum(per_seed_blk) / seeds_used,
        'dep_rate': sum(per_seed_L) / seeds_used,
        'lam_eff': sum(per_seed_L) / seeds_used,
        'p_loss': sum(per_seed_p_loss) / seeds_used,
        'p_wait': sum(per_seed_p_wait) / seeds_used,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
