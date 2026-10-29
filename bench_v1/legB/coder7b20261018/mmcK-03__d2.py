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
    parser.add_argument('--horizon', type=float, default=1)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + args.seeds))
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        lam = 8 / 60
        mu = 1 / 12
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        c = 2
        Q = 4
        W = 0
        L = 0
        p_loss = 0
        p_wait = 0
        busy_util = 0
        busy_occupied = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        time_unit = 'minute'
        win = args.horizon

        t = 0
        queue = []
        lanes = [0] * c

        while t < win:
            if len(queue) < Q:
                inter_arrival = exponential(lam)
                t += inter_arrival
                arr += 1
                if sum(lanes) < c:
                    lanes[lanes.index(0)] = exponential(mu)
                else:
                    p_loss += 1
                    blk += 1
            else:
                t += exponential(lam)

            for i in range(c):
                if lanes[i] > 0:
                    lanes[i] -= 1
                    dep += 1
                    busy_util += 1
                    busy_occupied += 1
                else:
                    if queue:
                        lanes[i] = exponential(mu)
                        queue.pop(0)

            if t >= win:
                break

            if len(queue) > 0:
                p_wait += 1

        L = arr / seeds_used
        W = W / seeds_used
        busy_frac = 1 - exp(-lam * win)
        p_loss /= seeds_used
        p_wait /= seeds_used

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': time_unit,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
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
