import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    D = 1000.0
    K = 50.0
    h = 10.0
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
        # simulate demand arrivals as Poisson with rate D per year, time unit = day
        rate = D / 365.0
        t = 0.0
        # EOQ policy: order q_star when inventory hits 0
        q = q_star
        inv = q
        # accumulate cost over horizon
        total_cost = 0.0
        # integrate holding cost over time
        last_t = 0.0
        while t < H:
            # time to next demand
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            if t + dt >= H:
                total_cost += h * inv * (H - t) / 365.0
                t = H
                break
            total_cost += h * inv * dt / 365.0
            t += dt
            inv -= 1.0
            if inv <= 0:
                total_cost += K
                inv += q
        per_seed_q.append(q)

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
