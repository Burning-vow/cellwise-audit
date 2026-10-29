import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    D = 1000.0
    K = 200.0
    h = 2.0
    if a.pert == 'lam_up':
        D = D * 1.2
    elif a.pert == 'mu_up':
        K = K * 0.8
    elif a.pert == 'c_up':
        h = h * 1.2

    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    H = float(a.horizon)
    n = a.seeds
    seeds = [a.seed_start + i for i in range(n)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        # simulate inventory over horizon with (s,S)-like fixed order q_star, stochastic demand
        # demand rate D per year, time unit = day, horizon H days
        rate = D / 365.0
        inv = q_star
        t = 0.0
        orders = 0
        while t < H:
            # next demand event: exponential interarrival with rate
            dt = rng.expovariate(rate) if rate > 0 else H
            t += dt
            if t >= H:
                break
            inv -= 1.0
            if inv <= 0:
                orders += 1
                inv += q_star
        # estimate q from orders: total demand / orders
        total_demand = rate * H
        est_q = total_demand / orders if orders > 0 else q_star
        per_seed_q.append(est_q)

    q_est = sum(per_seed_q) / len(per_seed_q) if per_seed_q else q_star
    cost_est = (D / q_est) * K + (q_est / 2.0) * h if q_est > 0 else cost_star

    out = {
        "cost": cost_est,
        "q": q_est,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
