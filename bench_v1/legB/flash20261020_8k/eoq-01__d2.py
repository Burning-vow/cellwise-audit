import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=365.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    D = 1000.0
    K = 50.0
    h = 2.0
    if a.pert == 'lam_up':
        D *= 1.2
    elif a.pert == 'mu_up':
        K *= 0.8
    elif a.pert == 'c_up':
        h *= 1.2

    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    H = float(a.horizon)
    n = a.seeds
    per_seed_q = []
    for i in range(n):
        seed = a.seed_start + i
        rng = random.Random(seed)
        rate = D / 365.0
        t = 0.0
        inv = q_star
        warm = 0.25 * H
        area = 0.0
        demand_acc = 0.0
        orders = 0
        while t < H:
            dt = rng.expovariate(rate) if rate > 0 else H
            nt = t + dt
            if nt > H:
                nt = H
            area += inv * (nt - t)
            inv -= rate * (nt - t)
            demand_acc += rate * (nt - t)
            if inv <= 0:
                inv += q_star
                orders += 1
            t = nt
        if H > 0:
            avg_inv = area / H
            d_rate = demand_acc / H
            q_est = math.sqrt(2.0 * d_rate * 365.0 * K / h) if d_rate > 0 else q_star
        else:
            q_est = q_star
        per_seed_q.append(q_est)

    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(n)],
        'seeds_used': n,
        'time_unit': 'day',
        'per_seed_q': per_seed_q,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
