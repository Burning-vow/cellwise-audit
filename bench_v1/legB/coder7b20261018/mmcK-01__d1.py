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
    lam = 6
    mu = 1 / (12 / 60)
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
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
        lanes = [0, 0]
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
            if queue and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if lanes[0] > 0:
                lanes[0] -= args.horizon
                if lanes[0] <= 0:
                    lanes[0] = 0
            if lanes[1] > 0:
                lanes[1] -= args.horizon
                if lanes[1] <= 0:
                    lanes[1] = 0
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[0] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                W += lanes[1]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait += lanes[1] * (len(queue) > 0)
            if len(queue) > 0 and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                W += lanes[0]
                dep += 1
                dep_rate += 1 / args.horizon
                p_wait
