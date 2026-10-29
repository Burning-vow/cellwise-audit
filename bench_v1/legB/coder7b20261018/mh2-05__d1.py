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
        mu = 6 / (1 + 3**2)
        sigma = sqrt(mu * (1 + 3**2) - mu**2)
        W = mu + sigma**2 / (2 * mu)
        L = lam / (mu - lam)

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        busy_frac = 0

        t = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        busy = False

        while t < args.horizon:
            if next_arrival < next_departure:
                t = next_arrival
                if busy:
                    dep += 1
                    busy_util += 1
                    busy_occupied += 1
                else:
                    busy = True
                    busy_util += 1
                    busy_occupied += 1
                next_arrival = t + random.expovariate(lam)
                next_departure = t + random.expovariate(mu)
            else:
                t = next_departure
                busy = False
                busy_util += 1
                busy_occupied += 1
                next_departure = float('inf')

            arr += 1
            if busy:
                dep_rate = dep / t
                p_loss = 0
                p_wait = 0
            else:
                dep_rate = 0
                p_loss = 0
                p_wait = 0

            busy_frac = busy_occupied / t

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": args.horizon,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
