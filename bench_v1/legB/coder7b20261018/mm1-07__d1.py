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
        lam = 8 / 60
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
        last_departure = 0
        queue = []

        for t in range(int(args.horizon * 60)):
            if random.expovariate(lam) + last_arrival <= t:
                arr += 1
                queue.append(t)
                last_arrival = t
            if queue and (not queue or random.expovariate(mu) + last_departure <= t):
                dep += 1
                last_departure = t
                busy_time += t - last_departure
                queue.pop(0)
            if queue and len(queue) > 1:
                blk += 1

        total_time += t
        per_seed_L.append(len(queue) / args.horizon)
        per_seed_W.append(busy_time / (args.horizon * 60))
        per_seed_busy_frac.append(busy_time / total_time)
        per_seed_p_loss.append(blk / arr)
        per_seed_p_wait.append(sum(t - last_arrival for t in queue) / arr)

    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used

    print(json.dumps({
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_wait": p_wait,
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": args.horizon,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
