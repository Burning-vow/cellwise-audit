import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    D = 1000.0
    K = 200.0
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
        t = 0.0
        inv = q_star
        warm = 0.25 * H
        area = 0.0
        orders = 0
        last_t = 0.0
        while t < H:
            rate = D / 365.0
            if inv <= 0.0:
                inv += q_star
                orders += 1
            dt = inv / rate if rate > 0 else H - t
            nt = t + dt
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area += inv * dt
            inv -= rate * dt
            t = nt
        span = H - warm
        if span <= 0:
            span = H
        avg_inv = area / span
        if avg_inv > 0:
            q_est = math.sqrt(2.0 * D * K / h)
        else:
            q_est = q_star
        per_seed_q.append(q_est)
    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'second',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
