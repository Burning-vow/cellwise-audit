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
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    lam = 8 / 60
    mu = 1 / 6
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 0.9
    elif args.pert == 'c_up':
        pass

    W = 0
    L = 0
    p_loss = 0
    busy_frac = 0
    arr = 0
    dep = 0
    blk = 0
    dep_rate = 0
    lam_eff = 0
    p_wait = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        queue = []
        lanes = [0] * 3
        time = 0
        while time < args.horizon:
            if random.random() < lam * args.horizon:
                queue.append(time)
            if queue and lanes[0] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            elif queue and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            elif queue and lanes[2] == 0:
                lanes[2] = exponential(mu)
                W += lanes[2]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[2] * (len(queue) > 0)
            elif queue:
                blk += 1
                p_loss += 1 / args.horizon
            lanes = [max(0, lane - args.horizon) for lane in lanes]
            time += args.horizon

        arr += len(queue)
        L += len(queue)
        busy_frac += sum(lanes) / (3 * args.horizon)
        per_seed_L.append(L / seeds_used)
        per_seed_W.append(W / seeds_used)
        per_seed_busy_frac.append(busy_frac / seeds_used)
        per_seed_p_loss.append(p_loss / seeds_used)
        per_seed_p_wait.append(p_wait / seeds_used)

    L /= seeds_used
    W /= seeds_used
    busy_frac /= seeds_used
    p_loss /= seeds_used
    p_wait /= seeds_used
    busy_util = sum(min(len(queue), 3) for queue in queue) / (3 * seeds_used)
    busy_occupied = 1 - poisson(lam, args.horizon)

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait,
        'arr': arr / seeds_used,
        'dep': dep / seeds_used,
        'blk': blk / seeds_used,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait / seeds_used,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied
    }))

if __name__ == "__main__":
    main()
