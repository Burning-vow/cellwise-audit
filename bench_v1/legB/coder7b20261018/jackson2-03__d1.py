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
        lam = 4 / 60  # arrival rate in jobs per minute
        mu = 1 / 6  # service rate in jobs per minute
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
        total_jobs = 0
        lost_jobs = 0
        dep_jobs = 0

        for t in range(int(args.horizon * 60)):
            if random.random() < lam:
                total_jobs += 1
                if Q1 == 0:
                    Q1 = 1
                    W1 += t
                else:
                    Q2 += 1
                    W2 += t

            if Q1 > 0:
                Q1 -= 1
                busy_time += 1
                W1 += t
                if Q2 > 0:
                    Q2 -= 1
                    busy_time += 1
                    W2 += t
                else:
                    dep_jobs += 1

            if Q1 == 0 and Q2 == 0:
                lost_jobs += 1

            L1 += Q1
            L2 += Q2
            total_time += 1

        per_seed_L.append((L1 + L2) / total_time)
        per_seed_W.append((W1 + W2) / total_jobs)
        per_seed_busy_frac.append(busy_time / total_time)
        per_seed_p_loss.append(lost_jobs / total_jobs)
        per_seed_p_wait.append(W1 / total_jobs + W2 / total_jobs)

    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used

    print(json.dumps({
        "L": L,
        "W": W,
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": args.horizon,
        "arr": total_jobs / args.horizon,
        "blk": lost_jobs / args.horizon,
        "busy_frac": busy_frac,
        "busy_util": busy_frac,
        "dep": dep_jobs / args.horizon,
        "dep_rate": dep_jobs / args.horizon,
        "lam_eff": lam,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
