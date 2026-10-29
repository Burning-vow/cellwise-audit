import sys
import json
import random
from math import exp, factorial

def poisson(lam, k):
    return (lam ** k * exp(-lam)) / factorial(k)

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
        lam = 6 / 60  # lambda per minute
        mu = 1 / 6  # service rate per minute
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        queue = []
        busy = False
        total_time = 0
        total_wait_time = 0
        total_busy_time = 0
        total_arrivals = 0
        total_departures = 0
        total_rejections = 0

        for t in range(int(args.horizon * 60)):
            if random.random() < lam:
                total_arrivals += 1
                queue.append(t)
            if busy:
                total_busy_time += 1
                if t - queue[0] >= 6:
                    busy = False
                    total_departures += 1
                    queue.pop(0)
                    if queue:
                        total_wait_time += t - queue[0]
            else:
                if queue:
                    busy = True
                    total_wait_time += t - queue[0]

            total_time += 1

        if total_arrivals > 0:
            avg_wait_time = total_wait_time / total_arrivals
            avg_busy_time = total_busy_time / total_time
            avg_arrivals = total_arrivals / total_time
            avg_departures = total_departures / total_time
            avg_rejections = total_rejections / total_arrivals
            avg_L = avg_arrivals / (1 - avg_busy_time)
            avg_W = avg_wait_time + avg_busy_time
            busy_frac = avg_busy_time
            p_loss = avg_rejections
            p_wait = avg_wait_time / avg_arrivals
        else:
            avg_L = 0
            avg_W = 0
            busy_frac = 0
            p_loss = 0
            p_wait = 0

        per_seed_L.append(avg_L)
        per_seed_W.append(avg_W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    per_seed_L = per_seed_L[len(per_seed_L) // 4:]
    per_seed_W = per_seed_W[len(per_seed_W) // 4:]
    per_seed_busy_frac = per_seed_busy_frac[len(per_seed_busy_frac) // 4:]
    per_seed_p_loss = per_seed_p_loss[len(per_seed_p_loss) // 4:]
    per_seed_p_wait = per_seed_p_wait[len(per_seed_p_wait) // 4:]

    print(json.dumps({
        'L': sum(per_seed_L) / len(per_seed_L),
        'W': sum(per_seed_W) / len(per_seed_W),
        'busy_frac': sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
