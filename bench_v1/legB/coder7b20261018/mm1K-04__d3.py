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
    mu = 1 / 5
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 0.9
    elif args.pert == 'c_up':
        pass

    W = 0
    L = 0
    busy_frac = 0
    p_loss = 0
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
        time = 0
        busy = False
        busy_time = 0
        loss_count = 0
        total_arrivals = 0
        total_departures = 0

        while time < args.horizon:
            if not busy:
                if queue:
                    busy = True
                    busy_time = exponential(mu)
                    busy_time += time
                    dep += 1
                    total_departures += 1
                else:
                    time += exponential(lam)
                    total_arrivals += 1
            else:
                if time >= busy_time:
                    busy = False
                    time = busy_time
                else:
                    if len(queue) < 3:
                        queue.append(exponential(mu))
                        time += exponential(lam)
                        total_arrivals += 1
                    else:
                        loss_count += 1
                        time += exponential(lam)

            if queue:
                W += time - queue[0]
                p_wait += 1

        W /= total_departures
        L = total_arrivals / args.horizon
        busy_frac = 1 - poisson(lam, args.horizon)
        p_loss = loss_count / total_arrivals
        arr = total_arrivals / seeds_used
        dep = total_departures / seeds_used
        blk = loss_count / seeds_used
        dep_rate = total_departures / args.horizon
        lam_eff = lam * (1 - busy_frac)
        p_wait /= total_departures

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
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': args.horizon,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
