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
    mu = 1 / (5 / 60)
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
        N = 0
        busy = False
        queue = []
        while t < args.horizon:
            if not busy and queue:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif busy and N == 6:
                t += exponential(mu)
                N -= 1
                dep += 1
                busy = True
            elif not busy and queue:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif not busy and N < 6:
                t += exponential(lam)
                N += 1
                arr += 1
                if N == 6:
                    p_loss += 1
            elif busy and N < 6:
                t += exponential(mu)
                N -= 1
                dep += 1
