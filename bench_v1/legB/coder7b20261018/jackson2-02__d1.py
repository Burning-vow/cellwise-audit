import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1000)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        lam = 4 / 60  # arrival rate in jobs per minute
        mu1 = 1 / 7.5  # service rate for process 1 in jobs per minute
        mu2 = 1 / 5  # service rate for process 2 in jobs per minute
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu1 *= 1.1
            mu2 *= 1.1
        elif args.pert == 'c_up':
            mu1 *= 1.1
            mu2 *= 1.1

        Q1 = 0  # queue length for process 1
        Q2 = 0  # queue length for process 2
        S1 = 0  # service start time for process 1
        S2 = 0  # service start time for process 2
        L = 0  # total number of jobs in the system
        W = 0  # total waiting time for all jobs
        busy_frac = 0  # total busy fraction of the system
        p_loss = 0  # total loss probability
        p_wait = 0  # total waiting probability

        for t in range(int(args.horizon * 60)):
            if random.expovariate(lam) <= 1:
                L += 1
                if S1 == 0:
                    S1 = t + random.expovariate(mu1)
                elif S2 == 0:
                    S2 = t + random.expovariate(mu2)
                else:
                    Q1 += 1
                    if S2 == 0:
                        S2 = t + random.expovariate(mu2)
            if S1 <= t:
                L -= 1
                W += t - S1
                S1 = 0
                if Q1 > 0:
                    Q1 -= 1
                    S1 = t + random.expovariate(mu1)
            if S2 <= t:
                L -= 1
                W += t - S2
                S2 = 0
                if Q2 > 0:
                    Q2 -= 1
                    S2 = t + random.expovariate(mu2)

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append((S1 + S2) / (args.horizon * 60))
        per_seed_p_loss.append(0)
        per_seed_p_wait.append(W / (L * args.horizon * 60))

    arr = sum(per_seed_L) / seeds_used
    dep = sum(per_seed_L) / seeds_used
    blk = sum(per_seed_p_loss) / seeds_used
    dep_rate = dep / args.horizon
    lam_eff = lam * (1 - sum(per_seed_p_loss) / seeds_used)
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    busy_util = busy_frac * args.horizon * 60
    win = args.horizon * 60

    print(json.dumps({
        'L': sum(per_seed_L) / seeds_used,
        'W': sum(per_seed_W) / seeds_used,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_frac': busy_frac,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
