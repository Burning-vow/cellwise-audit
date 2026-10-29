import sys
import json
import random
from math import exp, sqrt

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
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
        lam = 5 / 60
        mu = 6 / 60
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.2

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        time_unit = 'minute'
        win = args.horizon
        busy_frac = 0

        t = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        busy = False

        while t < win:
            if next_arrival < next_departure:
                t = next_arrival
                arr += 1
                if busy:
                    dep += 1
                    busy_util += 1
                else:
                    busy = True
                    next_departure = t + random.expovariate(mu)
            else:
                t = next_departure
                dep += 1
                busy = False
                next_arrival = t + random.expovariate(lam)

            if busy:
                busy_occupied += 1

        L = arr / win
        W = busy_util / busy_occupied if busy_occupied > 0 else 0
        p_loss = blk / arr if arr > 0 else 0
        p_wait = p_loss + (1 - p_loss) * (W / mu) if W > 0 else 0
        busy_frac = busy_occupied / win

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    print(json.dumps({
        'L': sum(per_seed_L) / seeds_used,
        'W': sum(per_seed_W) / seeds_used,
        'busy_frac': sum(per_seed_busy_frac) / seeds_used,
        'runtime_units': time_unit,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
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
