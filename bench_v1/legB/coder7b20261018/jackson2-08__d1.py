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
                arr += 1
                if Q1 == 0:
                    Q1 = 1
                    next_service1 = t + random.expovariate(mu1)
                elif Q2 == 0:
                    Q2 = 1
                    next_service2 = t + random.expovariate(mu2)
                else:
                    blk += 1
            elif next_service1 < next_arrival and next_service1 < next_service2:
                t = next_service1
                dep += 1
                Q1 -= 1
                if Q2 > 0:
                    Q2 -= 1
                    next_service2 = t + random.expovariate(mu2)
                else:
                    next_service2 = float('inf')
            elif next_service2 < next_arrival and next_service2 < next_service1:
                t = next_service2
                dep += 1
                Q2 -= 1
                if Q1 > 0:
                    Q1 -= 1
                    next_service1 = t + random.expovariate(mu1)
                else:
                    next_service1 = float('inf')

            if Q1 > 0:
                W1 += (t - next_arrival)
            if Q2 > 0:
                W2 += (t - next_arrival)

            L += Q1 + Q2
            busy_frac += (t - next_arrival) * (Q1 > 0 or Q2 > 0)
            p_loss += blk / arr
            p_wait += W1 / arr + W2 / arr

            next_arrival = float('inf') if Q1 == 0 and Q2 == 0 else t + random.expovariate(lam)
            if Q1 > 0:
                next_service1 = t + random.expovariate(mu1)
            if Q2 > 0:
                next_service2 = t + random.expovariate(mu2)

        per_seed_L.append(L / args.horizon)
        per_seed_W.append((W1 + W2) / args.horizon)
        per_seed_busy_frac.append(busy_frac / args.horizon)
        per_seed_p_loss.append(p_loss / args.horizon)
        per_seed_p_wait.append(p_wait / args.horizon)

    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used

    win = args.horizon
    time_unit = 'minute'
    runtime_units = seeds_used

    print(json.dumps({
        'L': L,
        'W': W,
        'runtime_units': runtime_units,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': win,
        'arr': arr / seeds_used,
        'dep': dep / seeds_used,
        'blk': blk / seeds_used,
        'dep_rate': dep / args.horizon,
        'lam_eff': lam,
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
