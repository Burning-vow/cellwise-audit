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
        lam = 7 / 60
        mu = 1 / 6
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        t = 0
        L = 0
        W = 0
        busy_frac = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0

        while t < args.horizon:
            if L == 0:
                inter_arrival_time = exponential(lam)
                t += inter_arrival_time
                if t >= args.horizon:
                    break
                L += 1
                service_time = exponential(mu)
                W += service_time
                busy_frac += service_time
                busy_util += service_time
                busy_occupied += 1
                dep += 1
                dep_rate = dep / t
                arr += 1
            else:
                inter_arrival_time = exponential(lam)
                t += inter_arrival_time
                if t >= args.horizon:
                    break
                L += 1
                service_time = exponential(mu)
                W += service_time
                busy_frac += service_time
                busy_util += service_time
                busy_occupied += 1
                dep += 1
                dep_rate = dep / t
                arr += 1

        per_seed_L.append(L)
        per_seed_W.append(W / dep)
        per_seed_busy_frac.append(busy_frac / t)
        per_seed_p_loss.append(blk / arr)
        per_seed_p_wait.append(p_wait / arr)

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
        'per_seed_p_wait': per_seed_p_wait,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': p_loss,
        'p_wait': p_wait
    }))

if __name__ == "__main__":
    main()
