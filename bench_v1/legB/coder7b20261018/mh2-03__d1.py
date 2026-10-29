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
        lam = 3
        mu = 6 / (1 + 2**2)
        sigma = sqrt(mu * (1 + 2**2) - mu**2)
        rho = lam / mu
        pi_0 = 1 / (1 + rho)
        busy_frac = 1 - pi_0
        busy_util = 1 - pi_0
        busy_occupied = 1 - pi_0
        p_loss = 0
        p_wait = 0
        L = 0
        W = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        time_unit = 'minute'
        win = args.horizon

        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        t = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        busy = False

        while t < win:
            if next_arrival < next_departure:
                t = next_arrival
                if not busy:
                    busy = True
                    service_time = random.expovariate(1 / mu)
                    next_departure = t + service_time
                    W += service_time
                    dep += 1
                else:
                    blk += 1
                    p_loss += 1
            else:
                t = next_departure
                busy = False
                next_arrival = t + random.expovariate(lam)

            if t >= win / 4:
                L += 1
                arr += 1

        per_seed_L.append(L)
        per_seed_W.append(W / dep)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss / arr)
        per_seed_p_wait.append(p_wait / arr)

    output = {
        'L': sum(per_seed_L) / seeds_used,
        'W': sum(per_seed_W) / seeds_used,
        'busy_frac': sum(per_seed_busy_frac) / seeds_used,
        'runtime_units': time_unit,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait,
        'arr': arr / seeds_used,
        'dep': dep / seeds_used,
        'blk': blk / seeds_used,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': p_loss / arr,
        'p_wait': p_wait / arr,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
