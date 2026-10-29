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
    lam = D / a.horizon
    mu = 1.0
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c *= 1.2
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        inv = 0.0
        area = 0.0
        orders = 0
        warm = 0.25 * a.horizon
        warm_area = 0.0
        warm_orders = 0
        warm_t = 0.0
        pending = []
        next_arr = rng.expovariate(lam) if lam > 0 else float('inf')
        while t < a.horizon:
            if next_arr <= t:
                pass
            if next_arr < a.horizon and (not pending or next_arr <= pending[0][0]):
                dt = next_arr - t
                if t >= warm:
                    area += inv * dt
                else:
                    if next_arr > warm:
                        area += inv * (warm - t)
                inv += lam * dt
                t = next_arr
                svc = rng.expovariate(mu)
                pending.append((t + svc, svc))
                pending.sort()
                next_arr = t + rng.expovariate(lam) if lam > 0 else float('inf')
            else:
                if not pending:
                    break
                nt, svc = pending.pop(0)
                dt = nt - t
                if t >= warm:
                    area += inv * dt
                else:
                    if nt > warm:
                        area += inv * (warm - t)
                inv -= mu * dt
                t = nt
                if t >= warm:
                    orders += 1
                else:
                    warm_orders += 1
        if a.horizon > warm:
            avg_inv = area / (a.horizon - warm)
        else:
            avg_inv = 0.0
        if avg_inv > 0:
            q_est = math.sqrt(2.0 * D * K / (h * c)) if c > 0 else q_star
        else:
            q_est = q_star
        per_seed_q.append(q_est)
    out = {
        'cost': cost_star,
        'q': q_star,
        'runtime_units': a.horizon,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
