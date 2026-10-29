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

        lam = 6 / 60  # arrival rate in jobs per minute
        mu1 = 1 / 7.5  # service rate for process 1 in jobs per minute
        mu2 = 1 / 6  # service rate for process 2 in jobs per minute

        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu1 *= 1.1
            mu2 *= 1.1
        elif args.pert == 'c_up':
            mu1 *= 1.1
            mu2 *= 1.1

        W = 0
        L = 0
        busy_frac = 0
        p_loss = 0
        p_wait = 0
        arr = 0
        dep = 0
        blk = 0
        dep_rate = 0

        t = 0
        t_next_arrival = random.expovariate(lam)
        t_next_end_process1 = float('inf')
        t_next_end_process2 = float('inf')
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False

        while t < args.horizon:
            t_next = min(t_next_arrival, t_next_end_process1, t_next_end_process2)

            if t_next == t_next_arrival:
                arr += 1
                if busy1:
                    queue1.append(t_next)
                else:
                    busy1 = True
                    t_next_end_process1 = t + random.expovariate(mu1)
                t_next_arrival = t + random.expovariate(lam)

            elif t_next == t_next_end_process1:
                dep += 1
                if queue1:
                    t_next_end_process1 = t + random.expovariate(mu1)
                else:
                    busy1 = False
                if queue2:
                    t_next_end_process2 = t + random.expovariate(mu2)
                else:
                    busy2 = False

            elif t_next == t_next_end_process2:
                dep += 1
                if queue2:
                    t_next_end_process2 = t + random.expovariate(mu2)
                else:
                    busy2 = False

            t = t_next

            if t >= args.horizon * 0.25:
                W += dep_rate * (t - args.horizon * 0.25)
                L += dep_rate * (t - args.horizon * 0.25)
                busy_frac += busy1 + busy2
                p_loss += blk
                p_wait += sum(t - t_arr for t_arr in queue1 + queue2)

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac / args.horizon)
        per_seed_p_loss.append(p_loss / args.horizon)
        per_seed_p_wait.append(p_wait / args.horizon)

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
        "win": args.horizon * 0.75,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "arr": arr / args.horizon,
        "blk": blk / args.horizon,
        "dep": dep / args.horizon,
        "dep_rate": dep_rate,
        "lam_eff": lam,
        "p_loss": p_loss,
        "p_wait": p_wait
    }))

if __name__ == "__main__":
    main()
