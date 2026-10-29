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
        # demand per unit time ~ Poisson with rate D/H per time unit
        rate = D / H
        t = 0.0
        inv = q_star
        orders = 0
        total_demand = 0.0
        while t < H:
            dt = rng.expovariate(rate) if rate > 0 else H
            if t + dt > H:
                dt = H - t
            # demand during dt
            dem = rate * dt
            total_demand += dem
            inv -= dem
            t += dt
            if inv <= 0:
                orders += 1
                inv += q_star
        # estimate q from orders: q_est = total_demand / orders
        if orders > 0:
            q_est = total_demand / orders
        else:
            q_est = q_star
        per_seed_q.append(q_est)

    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'day',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
