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
        mu = 1 / 6
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        N = 2
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

        t = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        queue = []
        busy = [False, False]

        while t < win:
            if next_arrival < next_departure:
                t = next_arrival
                if len(queue) < N:
                    queue.append(t)
                    if not busy[0]:
                        busy[0] = True
                        next_departure = t + random.expovariate(mu)
                    elif not busy[1]:
                        busy[1] = True
                        next_departure = t + random.expovariate(mu)
                    else:
                        blk += 1
                else:
                    p_wait += 1
                next_arrival = t + random.expovariate(lam)
            else:
                t = next_departure
                dep += 1
                if queue:
                    next_departure = t + random.expovariate(mu)
                    queue.pop(0)
                    if queue:
                        if not busy[0]:
                            busy[0] = True
                        elif not busy[1]:
                            busy[1] = True
                    else:
                        busy[0] = False
                        busy[1] = False
                else:
                    busy[0] = False
                    busy[1] = False

            arr += len(queue)
            busy_util += sum(busy)
            busy_occupied += sum(busy)

        L = arr / (win * args.seeds)
        W = (arr + dep_rate * win) / (win * args.seeds)
        busy_frac = busy_util / (win * args.seeds * N)
        p_loss = blk / (win * args.seeds)
        p_wait /= (win * args.seeds)

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    print(json.dumps({
        'L': sum(per_seed_L) / len(per_seed_L),
        'W': sum(per_seed_W) / len(per_seed_W),
        'busy_frac': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'p_wait': sum(per_seed_p_wait) / len(per_seed_p_wait),
        'runtime_units': runtime_units,
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
