import sys
import json
import random
import math

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
        lam = 6
        mu = 6 / 60
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            lam *= 1.1
            mu *= 1.1

        W = 0
        L = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0
        time_unit = 'minute'
        win = args.horizon

        queue = []
        time = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while time < win:
            if next_arrival < next_departure:
                time = next_arrival
                if len(queue) < 6:
                    queue.append(time)
                    next_arrival = time + random.expovariate(lam)
                    arr += 1
                else:
                    p_loss += 1
                    next_arrival = time + random.expovariate(lam)
            else:
                time = next_departure
                dep += 1
                if queue:
                    next_departure = time + random.expovariate(mu)
                    busy_util += 1
                    busy_occupied += 1
                else:
                    next_departure = float('inf')

            if queue:
                p_wait += len(queue) * (time - queue[0])
                busy_frac += 1

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    per_seed_L = per_seed_L[25:]
    per_seed_W = per_seed_W[25:]
    per_seed_busy_frac = per_seed_busy_frac[25:]
    per_seed_p_loss = per_seed_p_loss[25:]
    per_seed_p_wait = per_seed_p_wait[25:]

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': time_unit,
        'seed_list': seeds,
        'seeds_used': args.seeds,
        'time_unit': time_unit,
        'win': win,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
