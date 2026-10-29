import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    D = 5000.0
    K = 50.0
    h = 2.0
    if a.pert == 'lam_up':
        D = D * 1.2
    elif a.pert == 'mu_up':
        K = K * 0.8
    elif a.pert == 'c_up':
        h = h * 1.25

    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    H = float(a.horizon)
    n = a.seeds
    seeds = [a.seed_start + i for i in range(n)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        # simulate inventory with (q_star) policy over horizon H (days)
        # demand uniform: interarrival exponential with rate D/365 per day
        lam = D / 365.0
        t = 0.0
        inv = q_star
        # warmup 25%
        warm = 0.25 * H
        area = 0.0
        orders = 0
        while t < H:
            dt = rng.expovariate(lam) if lam > 0 else float('inf')
            nxt = t + dt
            # integrate area before state change
            seg_end = min(nxt, H)
            area += inv * (seg_end - t)
            if nxt >= H:
                t = H
                break
            t = nxt
            inv -= 1.0
            if inv <= 0:
                inv += q_star
                orders += 1
        # estimate q from average inventory: avg_inv = q/2 => q = 2*avg_inv
        avg_inv = area / H if H > 0 else 0.0
        per_seed_q.append(2.0 * avg_inv)

    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'day',
        'per_seed_q': per_seed_q,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
