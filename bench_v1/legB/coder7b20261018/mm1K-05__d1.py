import sys
import json
import random
from math import exp, factorial

def poisson(lam, t):
    return lam * t * exp(-lam * t) / factorial(int(t))

def gamma(mu, t):
    return (mu ** t * exp(-mu * t)) / factorial(int(t))

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=1.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    lam = 9 / 60
    mu = 1 / 6
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        mu *= 1.1
    elif args.pert == 'c_up':
        pass  # Capacity unchanged

    W = 0
    L = 0
    busy_frac = 0
    p_loss = 0
    arr = 0
    dep = 0
    blk = 0
    dep_rate = 0
    lam_eff = 0
    p_wait = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []

    for seed in seed_list:
        random.seed(seed)
        t = 0
        queue = []
        busy = False
        while t < args.horizon:
            if not busy:
                if queue:
                    dep += 1
                    busy = True
                    t += gamma(mu, 1)
                else:
                    t += poisson(lam, 1)
            else:
                if queue:
                    dep += 1
                    busy = True
                    t += gamma(mu, 1)
                else:
                    busy = False
                    t += poisson(lam, 1)
            if len(queue) < 4:
                queue.append(t)
            else:
                blk += 1
        W += sum(queue) / len(queue)
        L += len(queue)
        busy_frac += busy / args.horizon
        p_loss += blk / (dep + blk)
        arr += len(queue)
        dep += dep
        dep_rate += dep / args.horizon
        lam_eff += lam * (1 - p_loss)
        p_wait += sum(queue) / len(queue) / args.horizon

    W /= seeds_used
    L /= seeds_used
    busy_frac /= seeds_used
    p_loss /= seeds_used
    p_wait /= seeds_used

    per_seed_L = [L] * seeds_used
    per_seed_W = [W] * seeds_used
    per_seed_busy_frac = [busy_frac] * seeds_used
    per_seed_p_loss = [p_loss] * seeds_used
    per_seed_p_wait = [p_wait] * seeds_used

    print(json.dumps({
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_loss": p_loss,
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": args.horizon,
        "arr": arr / seeds_used,
        "dep": dep / seeds_used,
        "blk": blk / seeds_used,
        "dep_rate": dep_rate / seeds_used,
        "lam_eff": lam_eff / seeds_used,
        "p_wait": p_wait / seeds_used,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
