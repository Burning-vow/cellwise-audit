import sys
import json
import random
from math import exp, log

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100)
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
        lam = 6 / 60  # arrival rate in jobs per minute
        mu1 = 1 / 5  # service rate for process 1 in jobs per minute
        mu2 = 1 / 6  # service rate for process 2 in jobs per minute

        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu1 *= 1.1
            mu2 *= 1.1
        elif args.pert == 'c_up':
            mu1 *= 1.1
            mu2 *= 1.1

        Q1 = 0
        Q2 = 0
        W1 = 0
        W2 = 0
        L = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0

        t = 0
        next_arrival = random.expovariate(lam)
        next_service1 = float('inf')
        next_service2 = float('inf')

        while t < args.horizon:
            if next_arrival < next_service1 and next_arrival < next_service2:
                t = next_arrival
                next_arrival = t + random.expovariate(lam)
                Q1 += 1
                arr += 1
                if Q1 == 1:
                    next_service1 = t + random.expovariate(mu1)
                if Q2 > 0:
                    next_service2 = min(next_service2, t + random.expovariate(mu2))
            elif next_service1 < next_arrival and next_service1 < next_service2:
                t = next_service1
                next_service1 = float('inf')
                Q1 -= 1
                dep += 1
                if Q1 > 0:
                    next_service1 = t + random.expovariate(mu1)
                if Q2 > 0:
                    next_service2 = min(next_service2, t + random.expovariate(mu2))
            elif next_service2 < next_arrival and next_service2 < next_service1:
                t = next_service2
                next_service2 = float('inf')
                Q2 -= 1
                dep += 1
                if Q2 > 0:
                    next_service2 = t + random.expovariate(mu2)
                if Q1 > 0:
                    next_service1 = min(next_service1, t + random.expovariate(mu1))
            else:
                t = next_arrival
                next_arrival = float('inf')

            if Q1 > 0:
                W1 += (t - next_service1)
            if Q2 > 0:
                W2 += (t - next_service2)

            if Q1 + Q2 > 0:
                busy_frac += 1

            if Q1 + Q2 == 0:
                p_loss += 1

            if Q1 > 0:
                p_wait += 1

        L = (Q1 + Q2) / args.horizon
        W = (W1 + W2) / args.horizon
        busy_frac /= args.horizon
        p_loss /= args.horizon
        p_wait /= args.horizon
        dep_rate = dep / args.horizon

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    runtime_units = 'minute'
    win = args.horizon
    lam_eff = lam
    per_seed_L = per_seed_L[25:]
    per_seed_W = per_seed_W[25:]
    per_seed_busy_frac = per_seed_busy_frac[25:]
    per_seed_p_loss = per_seed_p_loss[25:]
    per_seed_p_wait = per_seed_p_wait[25:]

    print(json.dumps({
        'L': L,
        'W': W,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': runtime_units,
        'win': win,
        'arr': arr / seeds_used,
        'dep': dep / seeds_used,
        'blk': blk / seeds_used,
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
