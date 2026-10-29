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
        D *= 1.2
    elif a.pert == 'mu_up':
        h *= 1.2
    elif a.pert == 'c_up':
        K *= 1.2

    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    H = float(a.horizon)
    n = a.seeds
    seeds = [a.seed_start + i for i in range(n)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        # simulate inventory over horizon with (q_star) policy, measure avg inventory
        # demand uniform: interarrival exponential with rate D per year
        t = 0.0
        inv = q_star
        area = 0.0
        warm = 0.25 * H
        last = 0.0
        while t < H:
            rate = D
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                nt = H
            # integrate area before state change
            if t >= warm:
                seg_end = min(nt, H)
                if seg_end > t:
                    area += inv * (seg_end - t)
            # demand arrives
            if nt < H:
                inv -= 1.0
                if inv <= 0:
                    inv += q_star
            t = nt
        window = H - warm
        avg_inv = area / window if window > 0 else 0.0
        # estimate q from avg inventory: avg_inv ~ q/2 => q ~ 2*avg_inv
        per_seed_q.append(2.0 * avg_inv)

    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'year',
        'per_seed_q': per_seed_q,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
