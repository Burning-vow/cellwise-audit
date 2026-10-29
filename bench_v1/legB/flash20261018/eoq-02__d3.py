import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=365.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
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
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        T = a.horizon
        t = 0.0
        inv = q_star
        orders = 0
        demand_acc = 0.0
        while t < T:
            rate = D / 365.0
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            if t + dt > T:
                demand_acc += rate * (T - t)
                t = T
                break
            demand_acc += rate * dt
            inv -= rate * dt
            t += dt
            if inv <= 0:
                inv += q_star
                orders += 1
        if demand_acc > 0:
            per_seed_q.append(demand_acc / max(orders, 1))
        else:
            per_seed_q.append(q_star)
    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': a.horizon,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'day',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
