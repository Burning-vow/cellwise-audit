import sys
import json
import random
from math import exp, log

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
        mu = 1 / 5
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        busy_frac = 0
        time_unit = 'minute'
        win = args.horizon
        start_time = 0
        end_time = win
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        busy = False

        while next_arrival < end_time:
            if next_arrival < next_departure:
                current_time = next_arrival
                next_arrival = random.expovariate(lam)
                if busy:
                    dep += 1
                    busy_util += 1
                    busy_occupied += 1
                else:
                    busy = True
                    next_departure = current_time + random.expovariate(mu)
                    p_wait += 1
            else:
                current_time = next_departure
                next_departure = float('inf')
                busy = False
                p_loss += 1

            arr += 1
            busy_frac += busy

        per_seed_L.append(arr / seeds_used)
        per_seed_W.append(p_wait / seeds_used)
        per_seed_busy_frac.append(busy_frac / seeds_used)
        per_seed_p_loss.append(p_loss / seeds_used)
        per_seed_p_wait.append(p_wait / seeds_used)

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
        'runtime_units': time_unit,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': arr / seeds_used,
        'blk': blk / seeds_used,
        'busy_util': busy_util / seeds_used,
        'dep': dep / seeds_used,
        'dep_rate': dep / (seeds_used * win * 60),
        'lam_eff': lam * (1 - p_loss),
        'p_loss': p_loss,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
