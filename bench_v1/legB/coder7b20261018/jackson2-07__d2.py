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
        mu = 6 / 60  # service rate in jobs per minute
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            lam *= 1.1
            mu *= 1.1

        Q1 = 0
        Q2 = 0
        W1 = 0
        W2 = 0
        L1 = 0
        L2 = 0
        busy_time = 0
        total_time = 0
        last_arrival = 0
        last_departure = 0

        for t in range(int(args.horizon * 60)):
            if random.expovariate(lam) + last_arrival <= t:
                Q1 += 1
                L1 += Q1
                last_arrival = t
                if Q2 > 0:
                    Q2 -= 1
                    W2 += t - last_departure
                    last_departure = t
                    busy_time += t - last_departure
                else:
                    Q1 -= 1
                    W1 += t - last_departure
                    last_departure = t
                    busy_time += t - last_departure

            if random.expovariate(mu) + last_departure <= t:
                Q2 += 1
                L2 += Q2
                last_departure = t
                busy_time += t - last_departure

            total_time += 1

        L = (L1 + L2) / total_time
        W = (W1 + W2) / total_time
        busy_frac = busy_time / total_time
        p_loss = 0
        p_wait = 0

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
