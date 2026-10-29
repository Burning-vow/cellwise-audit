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
        lam = 6 / 60  # 6 vehicles per hour
        mu = 1 / 5  # 5 minutes per vehicle
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 0.9
        elif args.pert == 'c_up':
            mu *= 0.9

        queue = []
        busy = False
        time = 0
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
                total_departures += 1
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
                    total_departures += 1

            if queue and time >= queue[0]:
                queue.pop(0)
                busy = False

            if time >= args.horizon:
                break

        if total_arrivals > 0:
            avg_wait_time = total_wait_time / total_arrivals
            avg_busy_time = total_busy_time / args.horizon
            avg_queue_length = total_arrivals - total_departures
            busy_frac = avg_busy_time / args.horizon
            p_loss = total_rejections / total_arrivals
            p_wait = avg_wait_time / args.horizon
        else:
            avg_wait_time = 0
            avg_busy_time = 0
            avg_queue_length = 0
            busy_frac = 0
            p_loss = 0
            p_wait = 0

        per_seed_L.append(avg_queue_length)
        per_seed_W.append(avg_wait_time)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    avg_L = sum(per_seed_L) / seeds_used
    avg_W = sum(per_seed_W) / seeds_used
    avg_busy_frac = sum(per_seed_busy_frac) / seeds_used
    avg_p_loss = sum(per_seed_p_loss) / seeds_used
    avg_p_wait = sum(per_seed_p_wait) / seeds_used

    print(json.dumps({
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_busy_frac,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": args.horizon,
        "arr": avg_arrivals / seeds_used,
        "blk": avg_rejections / seeds_used,
        "busy_util": avg_busy_time / args.horizon,
        "dep": avg_departures / seeds_used,
        "dep_rate": avg_departures / args.horizon,
        "lam_eff": lam,
        "p_loss": avg_p_loss,
        "p_wait": avg_p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
