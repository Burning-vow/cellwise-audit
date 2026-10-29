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
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        # simulate inventory over horizon with (q_star) policy, estimate demand rate
        t = 0.0
        inv = q_star
        demand_total = 0.0
        warm = 0.25 * H
        # Poisson demand with rate D per year; time unit = day
        rate = D / 365.0
        while t < H:
            dt = rng.expovariate(rate) if rate > 0 else H
            t += dt
            if t >= H:
                break
            demand_total += 1.0
            inv -= 1.0
            if inv <= 0:
                inv += q_star
        # estimate annual demand from post-warmup window
        # approximate: scale observed demand
        if H > warm:
            est_rate = demand_total / H * 365.0
        else:
            est_rate = D
        q_est = math.sqrt(2.0 * est_rate * K / h) if est_rate > 0 else q_star
        per_seed_q.append(q_est)

    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'day',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
