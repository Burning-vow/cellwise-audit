import sys
import json
import random
from math import exp, factorial

def poisson(lam, t):
    return lam * t * exp(-lam * t) / factorial(int(t))

def exponential(mu):
    return -1 / mu * log(random.random())

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100)
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
        lam = 6 if args.pert == 'lam_up' else 6
        mu = 6 if args.pert == 'mu_up' else 6
        c = 1
        N = 0
        W = 0
        busy_frac = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0
        t = 0
        next_arrival = exponential(lam)
        next_departure = float('inf')

        while t < args.horizon:
            if next_arrival < next_departure:
                t = next_arrival
                N += 1
                arr += 1
                if N == 1:
                    next_departure = t + exponential(mu)
                else:
                    next_departure = float('inf')
            else:
                t = next_departure
                N -= 1
                dep += 1
                if N > 0:
                    next_departure = t + exponential(mu)
                else:
                    next_departure = float('inf')

            if N > 0:
                busy_frac += 1
                busy_util += 1
                busy_occupied += 1
            else:
                busy_util += 0
                busy_occupied += 0

            if N > c:
                blk += 1

            next_arrival = t + exponential(lam)

        if t > args.horizon:
            t = args.horizon

        if t > 0:
            W = W / t
            busy_frac = busy_frac / t
            p_wait = p_wait / t
            dep_rate = dep / t
            busy_util = busy_util / t
            busy_occupied = busy_occupied / t

        per_seed_L.append(N / t)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(blk / t)
        per_seed_p_wait.append(p_wait)

    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
