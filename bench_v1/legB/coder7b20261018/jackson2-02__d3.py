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
                Q1 += 1
                if Q1 == 1:
                    next_service1 = t + random.expovariate(mu1)
                if Q2 > 0:
                    next_service2 = min(next_service2, t + random.expovariate(mu2))
            elif next_service1 < next_arrival and next_service1 < next_service2:
                t = next_service1
                dep += 1
                Q1 -= 1
                if Q1 > 0:
                    next_service1 = t + random.expovariate(mu1)
                if Q2 > 0:
                    next_service2 = min(next_service2, t + random.expovariate(mu2))
            elif next_service2 < next_arrival and next_service2 < next_service1:
                t = next_service2
                dep += 1
                Q2 -= 1
                if Q2 > 0:
                    next_service2 = t + random.expovariate(mu2)
                if Q1 > 0:
                    next_service1 = min(next_service1, t + random.expovariate(mu1))
            else:
                t = next_arrival
                arr += 1
                Q1 += 1
                if Q1 == 1:
                    next_service1 = t + random.expovariate(mu1)
                if Q2 > 0:
                    next_service2 = min(next_service2, t + random.expovariate(mu2))

            if Q1 > 0:
                W1 += (t - next_arrival)
            if Q2 > 0:
                W2 += (t - next_arrival)

            if Q1 == 0 and Q2 == 0:
                busy_frac += 0
            elif Q1 == 0:
                busy_frac += (t - next_arrival) / (t - next_arrival + (1 / mu2))
            elif Q2 == 0:
                busy_frac += (t - next_arrival) / (t - next_arrival + (1 / mu1))
            else:
                busy_frac += (t - next_arrival) / (t - next_arrival + (1 / mu1) + (1 / mu2))

            if Q1 > 0:
                p_wait += (t - next_arrival) / Q1
            if Q2 > 0:
                p_wait += (t - next_arrival) / Q2

            if Q1 == 0:
                p_loss += 1

            next_arrival = t + random.expovariate(lam)

        L = (W1 + W2) / (2 * args.horizon)
        W = (W1 + W2) / arr
        busy_frac /= args.horizon
        p_loss /= arr
        p_wait /= arr

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        "L": L,
        "W": W,
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": args.horizon,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
