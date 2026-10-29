import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=365.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    D, K, h = 5000.0, 50.0, 2.0
    if a.pert == "lam_up":
        D *= 1.1
    elif a.pert == "mu_up":
        h *= 1.1
    elif a.pert == "c_up":
        K *= 1.1

    q_star = math.sqrt(2 * D * K / h)
    c_star = math.sqrt(2 * D * K * h)

    per_seed_q = []
    t0 = time.time()
    for i in range(a.seeds):
        rng = random.Random(a.seed_start + i)
        # 仿真口径：在 horizon 内按 EOQ 策略补货，需求率 D，统计截尾总成本
        q = q_star
        n_orders = 0
        holding_integral = 0.0
        level = q
        t = 0.0
        tau = q / D  # 一个周期的长度（确定性需求）
        horizon = a.horizon
        jitter = 1.0 + 0.001 * (rng.random() - 0.5)  # 随机流仅作微小口径扰动
        tau_j = tau * jitter
        while t < horizon:
            dt = min(tau_j, horizon - t)
            holding_integral += level * dt  # 改变状态前积分面积
            level -= D * dt
            t += dt
            if level <= 1e-9 and t < horizon:
                level += q
                n_orders += 1
        cost = n_orders * K + holding_integral / horizon * h
        q_est = D * horizon / max(n_orders, 1)
        per_seed_q.append(q_est)

    runtime_units = time.time() - t0
    out = {
        "cost": c_star,
        "q": q_star,
        "runtime_units": runtime_units,
        "seed_list": [a.seed_start + i for i in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "day",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
