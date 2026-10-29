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
        lam = 10 / 60  # 顾客到达率（每分钟）
        mu = 1 / 10  # 服务率（每分钟）
        c = 2  # 柜台数量
        N = 0  # 当前顾客数量
        Q = []  # 等待队列
        busy_time = 0  # 忙碌时间
        total_time = 0  # 总时间
        total_wait_time = 0  # 总等待时间
        total_service_time = 0  # 总服务时间
        total_arrival_time = 0  # 总到达时间
        total_departure_time = 0  # 总离开时间
        total_loss_time = 0  # 总丢失时间

        for t in range(int(args.horizon * 60)):
            if random.random() < lam:
                N += 1
                total_arrival_time += t
                if N > c:
                    total_loss_time += 1
                else:
                    Q.append(t)

            if Q and busy_time == 0:
                start_time = Q.pop(0)
                end_time = start_time + int(exp(-mu * (t - start_time)))
                busy_time = end_time - t
                total_service_time += end_time - start_time

            if busy_time > 0:
                busy_time -= 1

            total_time += 1

        if total_time > 0:
            L = total_arrival_time / total_time
            W = total_wait_time / total_arrival_time
            busy_frac = busy_time / total_time
            p_wait = total_loss_time / total_arrival_time
        else:
            L = W = busy_frac = p_wait = 0

        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(busy_frac)
        per_seed_p_loss.append(total_loss_time / total_arrival_time)
        per_seed_p_wait.append(p_wait)

    L = sum(per_seed_L) / len(per_seed_L)
    W = sum(per_seed_W) / len(per_seed_W)
    busy_frac = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)

    print(json.dumps({
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "p_wait": p_wait,
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
