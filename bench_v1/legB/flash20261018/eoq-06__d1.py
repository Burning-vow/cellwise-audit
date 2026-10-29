import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=8760.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    D = 5000.0
    K = 200.0
    h = 2.0
    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    lam = D / 8760.0
    mu = 1.0
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
        inv = q_star
        on_order = 0.0
        area = 0.0
        orders = 0
        last = 0.0
        while t < H:
            if on_order <= 0.0:
                dt = rng.expovariate(lam)
                t2 = t + dt
                if t2 > H:
                    t2 = H
                if t2 > warm:
                    lo = max(t, warm)
                    if t2 > lo:
                        area += inv * (t2 - lo)
                t = t2
                if t >= H:
                    break
                on_order = q_star
                orders += 1
            else:
                dt = rng.expovariate(mu)
                t2 = t + dt
                if t2 > H:
                    t2 = H
                if t2 > warm:
                    lo = max(t, warm)
                    if t2 > lo:
                        area += inv * (t2 - lo)
                t = t2
                if t >= H:
                    break
                inv += q_star
                on_order = 0.0
        win = H - warm
        if win <= 0:
            per_seed_q.append(q_star)
        else:
            avg_inv = area / win
            per_seed_q.append(avg_inv)

    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
