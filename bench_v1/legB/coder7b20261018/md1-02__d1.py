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
        lam = 4 / 60  # 4 cars per hour
        mu = 1 / 5  # 5 minutes per car
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 0.9
        elif args.pert == 'c_up':
            mu *= 0.9

        queue = []
        busy = False
        time = 0
        total_time = 0
        total_wait_time = 0
        total_busy_time = 0
        total_arrivals = 0
        total_departures = 0
        total_rejections = 0

        while time < args.horizon:
            if not busy and queue:
                busy = True
                service_time = random.expovariate(mu)
                total_busy_time += service_time
                time += service_time
            else:
                inter_arrival_time = random.expovariate(lam)
                time += inter_arrival_time
                total_arrivals += 1

                if busy:
                    queue.append(time)
                else:
                    busy = True
                    service_time = random.expovariate(mu)
                    total_busy_time += service_time
                    time += service_time

            if queue and time >= queue[0]:
                queue.pop(0)
                total_departures += 1
                busy = False

            if time > args.horizon * 0.25:
                per_seed_L.append(len(queue))
                per_seed_W.append(total_wait_time / total_departures)
                per_seed_busy_frac.append(total_busy_time / total_time)
                per_seed_p_loss.append(total_rejections / total_arrivals)
                per_seed_p_wait.append(total_wait_time / total_departures)

    L = sum(per_seed_L) / seeds_used
    W = sum(per_seed_W) / seeds_used
    busy_frac = sum(per_seed_busy_frac) / seeds_used
    p_loss = sum(per_seed_p_loss) / seeds_used
    p_wait = sum(per_seed_p_wait) / seeds_used

    print(json.dumps({
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': args.horizon,
        'per_seed_L': per_seed_L,
        'per_seed_W': per_seed_W,
        'per_seed_busy_frac': per_seed_busy_frac,
        'per_seed_p_loss': per_seed_p_loss,
        'per_seed_p_wait': per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
