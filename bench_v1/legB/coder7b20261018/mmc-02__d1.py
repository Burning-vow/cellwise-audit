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
        mu = 1 / 10
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        N = 2
        time_unit = 'minute'
        win = args.horizon
        runtime_units = win / args.horizon

        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        lam_eff = 0
        p_loss = 0
        p_wait = 0
        busy_util = 0
        busy_occupied = 0
        busy_frac = 0

        t = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')
        queue = []
        busy = [False, False]

        while t < win:
            if next_arrival < next_departure:
                t = next_arrival
                next_arrival = t + random.expovariate(lam)
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
                    blk += 1
            else:
                t = next_departure
                next_departure = float('inf')
                dep += 1
                if queue:
                    next_departure = t + random.expovariate(mu)
                    busy[queue.pop(0)] = False
                    if queue:
                        if not busy[0]:
                            busy[0] = True
                            next_departure = min(next_departure, t + random.expovariate(mu))
                        elif not busy[1]:
                            busy[1] = True
                            next_departure = min(next_departure, t + random.expovariate(mu))
                else:
                    busy = [False, False]

            arr += len(queue)
            busy_util += sum(busy)
            busy_occupied += sum(busy)
            p_wait += len(queue) > 0

        L = arr / (win * runtime_units)
        W = (arr * mu + dep * mu) / (win * runtime_units)
        busy_frac = busy_util / (win * runtime_units * N)
        p_loss = blk / (win * runtime_units)
        p_wait /= (win * runtime_units)

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

    print(json.dumps({
        'L': sum(per_seed_L) / len(per_seed_L),
        'W': sum(per_seed_W) / len(per_seed_W),
        'busy_frac': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'p_wait': sum(per_seed_p_wait) / len(per_seed_p_wait),
        'runtime_units': runtime_units,
        'seed_list': seeds,
        'seeds_used': len(seeds),
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
