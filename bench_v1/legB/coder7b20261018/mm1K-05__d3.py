import sys
import json
import random
from math import exp, factorial

def poisson(lam, t):
    return lam * t * exp(-lam * t) / factorial(int(t))

def gamma(mu, t):
    return (mu ** t * exp(-mu * t)) / factorial(int(t))

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
    lam = 9 / 60
    mu = 1 / 6
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
    elif args.pert == 'c_up':
        pass  # Capacity unchanged

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
                t += gamma(mu, 1)
                n -= 1
                dep += 1
                busy = False
            elif not busy and n < 4:
                t += poisson(lam, 1)
                n += 1
                arr += 1
                if n == 4:
                    busy = True
            elif busy and n < 4:
                t += gamma(mu, 1)
                n -= 1
                dep += 1
                busy = False
            elif busy and n == 4:
                t += gamma(mu, 1)
                n -= 1
                dep += 1
                busy = False
            elif n == 4:
                t += poisson(lam, 1)
                n += 1
                arr += 1
                if n == 4:
                    busy = True
                    p_loss += 1
            queue.append(t)
            if len(queue) > 1:
                W += queue[1] - queue[0]
            if n > 0:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n == 4:
                busy_frac += 1
            if n
