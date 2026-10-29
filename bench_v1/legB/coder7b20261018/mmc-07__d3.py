import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds = range(args.seed_start, args.seed_start + args.seeds)
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seeds:
        random.seed(seed)
        lam = 8 / 60
        mu = 1 / 12
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 0.9
        elif args.pert == 'c_up':
            mu *= 1.1

        N = 3
        time_unit = 'minute'
        win = args.horizon
        runtime_units = win / args.seeds

        arr = 0
        dep = 0
        blk = 0
        busy_util = 0
        busy_occupied = 0
        p_loss = 0
        p_wait = 0
        total_time = 0
        total_wait_time = 0
        total_busy_time = 0
        total_customers = 0

        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        queue = []
        busy = [False] * N

        while total_time < win:
            if next_arrival < next_departure:
                total_time += next_arrival
                next_arrival = float('inf')
                if len(queue) < N:
                    queue.append(total_time)
                    total_customers += 1
                    if len(queue) == 1:
                        next_departure = total_time + random.expovariate(mu)
                else:
                    blk += 1
            else:
                total_time += next_departure - total_time
                next_departure = float('inf')
                if queue:
                    dep += 1
                    wait_time = queue.pop(0)
                    total_wait_time += total_time - wait_time
                    if queue:
                        next_departure = total_time + random.expovariate(mu)
                else:
                    busy = [False] * N

            if total_time < win:
                next_arrival = total_time + random.expovariate(lam)

            for i in range(N):
                if not busy[i]:
                    if queue:
                        busy[i] = True
                        busy_util += 1
                        next_departure = total_time + random.expovariate(mu)

        arr = total_customers / args.seeds
        dep = dep / args.seeds
        blk = blk / args.seeds
        dep_rate = dep * 60 / win
        lam_eff = lam * N / win
        p_loss = blk / total_customers
        p_wait = total_wait_time / total_customers
        busy_frac = busy_util / (N * win)
        L = total_customers / win
        W = total_wait_time / total_customers

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_wait": p_wait,
        "runtime_units": runtime_units,
        "seed_list": seeds,
        "seeds_used": args.seeds,
        "time_unit": time_unit,
        "win": win,
        "arr": arr,
        "blk": blk,
        "busy_util": busy_util,
        "dep": dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
