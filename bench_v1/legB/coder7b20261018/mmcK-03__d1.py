import sys
import json
import random
from math import exp, factorial

def poisson(lam, t):
    return lam * t * exp(-lam * t) / factorial(int(t))

def exponential(mu):
    return -1 / mu * log(random.random())

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    lam = 8 / 60
    mu = 1 / 12
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
    elif args.pert == 'c_up':
        pass  # No change in capacity

    time_unit = 'minute'
    win = args.horizon
    runtime_units = win / seeds_used

    L = []
    W = []
    busy_frac = []
    p_loss = []
    p_wait = []

    for seed in seed_list:
        random.seed(seed)
        queue = []
        lanes = [0, 0]
        time = 0
        total_time = 0
        total_busy = 0
        total_arr = 0
        total_dep = 0
        total_blk = 0

        while time < win:
            if not queue and all(l == 0 for l in lanes):
                next_arrival = exponential(lam)
                time += next_arrival
                total_arr += 1
                queue.append(time)
            else:
                if queue and sum(lanes) < 2:
                    next_departure = min(queue[0] + exponential(mu), time + 1)
                    if next_departure == queue[0] + exponential(mu):
                        lanes[queue[0] % 2] += 1
                        total_busy += 1
                    else:
                        lanes[queue[0] % 2] = 0
                        total_dep += 1
                        queue.pop(0)
                else:
                    next_departure = time + 1
                    total_blk += 1
                    queue.pop(0)

                time = next_departure

        L.append(total_arr / seeds_used)
        W.append(total_busy / seeds_used)
        busy_frac.append(1 - poisson(lam, win))
        p_loss.append(total_blk / total_arr)
        p_wait.append(total_blk / total_arr)

    per_seed_L = L
    per_seed_W = W
    per_seed_busy_frac = busy_frac
    per_seed_p_loss = p_loss
    per_seed_p_wait = p_wait

    output = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_loss": p_loss,
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
