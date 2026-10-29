import sys
import json
import random
import math

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
            mu *= 0.9
        elif args.pert == 'c_up':
            mu *= 1.1

        N = 3
        Q = []
        S = [0] * N
        t = 0
        L = 0
        W = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0

        while t < args.horizon:
            if not Q and random.expovariate(lam) < args.horizon - t:
                Q.append(random.expovariate(mu))
                p_wait += 1
            if Q and S[0] <= t:
                S[0] = t + Q.pop(0)
                dep += 1
                dep_rate = dep / t
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0] = min(S[0], t + random.expovariate(mu))
                p_loss += 1
            if Q and S[0] > t:
                S[0
