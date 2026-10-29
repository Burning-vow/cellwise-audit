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
    lam = 9 / 60
    mu = 1 / 5
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
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
        t = 0
        n = 0
        busy = False
        queue = []
        while t < args.horizon:
            if not busy and queue:
                t += exponential(mu)
                n -= 1
                dep += 1
                busy = False
            elif n < 4:
                t += exponential(lam)
                n += 1
                arr += 1
                if n == 4:
                    busy = True
                else:
                    queue.append(t)
            else:
                t += exponential(lam)
                p_loss += 1
                blk += 1

        if n > 0:
            t += exponential(mu * n)
            dep += n
            busy = False

        W += sum(t - q for q in queue)
        L += n
        busy_frac += n / 4
        p_wait += sum(t - q for q in queue) / len(queue) if queue else 0

        per_seed_L.append(L / seeds_used)
        per_seed_W.append(W / seeds_used)
        per_seed_busy_frac.append(busy_frac / seeds_used)
        per_seed_p_loss.append(p_loss / seeds_used)
        per_seed_p_wait.append(p_wait / seeds_used)

    W /= seeds_used
    L /= seeds_used
    busy_frac /= seeds_used
    p_loss /= seeds_used
    p_wait /= seeds_used
    arr /= seeds_used
    dep /= seeds_used
    blk /= seeds_used
    dep_rate = dep / args.horizon
    lam_eff = lam * (1 - p_loss)

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
