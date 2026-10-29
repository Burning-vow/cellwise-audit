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
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        inv = q_star
        on_order = 0.0
        area = 0.0
        orders = 0
        while t < H:
            rate = D / 365.0
            if inv > 0:
                dt = inv / rate
            else:
                dt = 0.0
            nxt = t + dt
            if nxt > H:
                nxt = H
            if nxt > warm:
                lo = max(t, warm)
                if nxt > lo:
                    area += inv * (nxt - lo)
            t = nxt
            if t >= H:
                break
            inv = 0.0
            q = q_star
            inv += q
            orders += 1
        span = H - warm
        if span <= 0:
            span = H
        avg_inv = area / span if span > 0 else 0.0
        if orders > 0:
            est_q = D * (span / 365.0) / orders
        else:
            est_q = q_star
        per_seed_q.append(est_q)

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
