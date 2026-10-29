import sys
import json
import random
from math import exp, log

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
        lam = 10 / 60  # 到达率，每分钟
        mu = 1 / 6  # 服务率，每分钟
        if args.pert == 'lam_up':
            lam *= 1.1
        elif args.pert == 'mu_up':
            mu *= 1.1
        elif args.pert == 'c_up':
            mu *= 1.1

        N = 2  # 柜台数量
        Q = []  # 等待队列
        busy = [False] * N  # 柜台是否忙碌
        time = 0  # 当前时间
        total_wait = 0  # 总等待时间
        total_service = 0  # 总服务时间
        total_arrivals = 0  # 总到达人数
        total_departures = 0  # 总离开人数
        total_rejections = 0  # 总拒绝人数

        while time < args.horizon:
            if not busy and Q:
                i = random.randint(0, N - 1)
                busy[i] = True
                service_time = random.expovariate(mu)
                total_service += service_time
                time += service_time
                total_departures += 1
                Q.pop(0)
            elif not busy and not Q:
                time += random.expovariate(lam)
                total_arrivals += 1
            else:
                time += random.expovariate(lam)
                total_arrivals += 1
                if len(Q) < N:
                    Q.append(time)
                else:
                    total_rejections += 1

        if total_arrivals > 0:
            avg_wait = total_wait / total_arrivals
            avg_service = total_service / total_departures
            avg_L = total_arrivals / args.horizon
            busy_frac = sum(busy) / N
            p_wait = total_rejections / total_arrivals
        else:
            avg_wait = 0
            avg_service = 0
            avg_L = 0
            busy_frac = 0
            p_wait = 0

        per_seed_L.append(avg_L)
        per_seed_W.append(avg_wait)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(total_rejections / total_arrivals)
        per_seed_p_wait.append(p_wait)

    avg_L = sum(per_seed_L) / len(per_seed_L)
    avg_wait = sum(per_seed_W) / len(per_seed_W)
    avg_busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    avg_p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    avg_p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

    print(json.dumps({
        "L": avg_L,
        "W": avg_wait,
        "busy_frac": avg_busy_frac,
        "p_wait": avg_p_wait,
        "runtime_units": "minute",
        "seed_list": seeds,
        "seeds_used": args.seeds,
        "time_unit": "minute",
        "win": args.horizon,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }))

if __name__ == "__main__":
    main()
