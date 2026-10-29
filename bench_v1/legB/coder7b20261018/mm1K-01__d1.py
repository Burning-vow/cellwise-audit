import sys
import json
import random
from math import exp, factorial

def poisson(lam, t):
    return lam * t * exp(-lam * t) / factorial(int(t))

def gamma(k, theta):
    return (theta ** k) * exp(-theta) / factorial(int(k))

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds = range(args.seed_start, args.seed_start + args.seeds)
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seeds:
        random.seed(seed)
        lam = 6
        mu = 6
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            pass  # Capacity remains 4

        W = 0
        L = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0
        busy_util = 0
        busy_occupied = 0
        time_unit = 'minute'
        win = args.horizon

        t = 0
        n = 0
        next_arrival = random.expovariate(lam)
        next_departure = float('inf')

        while t < win:
            if next_arrival < next_departure:
                t = next_arrival
                if n < 4:
                    n += 1
                    next_arrival = t + random.expovariate(lam)
                    next_departure = t + random.expovariate(mu)
                    W += next_departure - t
                    arr += 1
                    p_wait += max(0, next_departure - t)
                else:
                    p_loss += 1
                    blk += 1
            else:
                t = next_departure
                n -= 1
                next_departure = float('inf')
                if n > 0:
                    next_departure = t + random.expovariate(mu)
                dep += 1
                dep_rate = dep / win

            if n > 0:
                busy_frac += 1
                busy_util += n
                busy_occupied += 1

        if n > 0:
            busy_frac += 1
            busy_util += n
            busy_occupied += 1

        L = arr / win
        p_wait /= win
        busy_frac /= win
        p_loss /= win
        busy_util /= win
        busy_occupied /= win

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)

    output = {
        "L": sum(per_seed_L) / len(per_seed_L),
        "W": sum(per_seed_W) / len(per_seed_W),
        "busy_frac": sum(per_seed_busy_frac) / len(per_seed_busy_frac),
        "p_loss": sum(per_seed_p_loss) / len(per_seed_p_loss),
        "runtime_units": time_unit,
        "seed_list": seeds,
        "seeds_used": args.seeds,
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
