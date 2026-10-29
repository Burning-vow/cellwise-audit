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
    c = 2
    W = 0
    L = 0
    p_loss = 0
    arr = 0
    dep = 0
    blk = 0
    dep_rate = 0
    busy_util = 0
    busy_occupied = 0
    busy_frac = 0
    p_wait = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        t = 0
        queue = []
        lanes = [0] * c
        while t < args.horizon:
            if len(queue) < 4:
                inter_arrival = exponential(lam)
                t += inter_arrival
                if len(queue) < 4:
                    queue.append(t)
            else:
                t += exponential(lam)
            if queue and lanes[0] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if lanes[0] > 0:
                lanes[0] -= args.time_unit
                if lanes[0] <= 0:
                    lanes[0] = 0
            if lanes[1] > 0:
                lanes[1] -= args.time_unit
                if lanes[1] <= 0:
                    lanes[1] = 0
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[0] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] == 0:
                lanes[1] = exponential(mu)
                dep += 1
                arr += 1
                p_wait += len(queue) - 1
            if queue and lanes[0] == 0 and lanes[1] ==
