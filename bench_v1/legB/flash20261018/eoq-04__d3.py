import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=8760.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    D = 1000.0
    K = 200.0
    h = 10.0
    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)
    lam = D / 8760.0
    mu = 1.0 / 24.0
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c *= 1.2
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        inv = 0.0
        pending = []
        area = 0.0
        orders = 0
        last = 0.0
        while t < H:
            dt = rng.expovariate(lam)
            t_next = t + dt
            if t_next > H:
                t_next = H
            if t_next > warm:
                lo = max(t, warm)
                area += inv * (t_next - lo)
            t = t_next
            if t >= H:
                break
            inv += 1.0
            if inv >= q_star:
                orders += 1
                inv -= q_star
        per_seed_q.append(orders if orders > 0 else 0)
    runtime_units = H
    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': runtime_units,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
