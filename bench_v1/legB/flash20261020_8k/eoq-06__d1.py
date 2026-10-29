import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=365.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    D = 5000.0
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
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        inv = q_star
        demand_rate = D / 365.0
        warm = 0.25 * H
        area = 0.0
        orders = 0
        last_t = 0.0
        while t < H:
            dt = rng.expovariate(demand_rate) if demand_rate > 0 else H
            nt = t + dt
            if nt > H:
                nt = H
            if t >= warm:
                area += inv * (nt - t)
            inv -= demand_rate * (nt - t)
            t = nt
            if inv <= 0.0 and t < H:
                inv += q_star
                if t >= warm:
                    orders += 1
        win = H - warm
        if win > 0 and orders > 0:
            avg_inv = area / win
            q_est = 2.0 * orders * K / (avg_inv * h) if avg_inv > 0 else q_star
            q_est = math.sqrt(max(q_est, 1e-9))
        else:
            q_est = q_star
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
