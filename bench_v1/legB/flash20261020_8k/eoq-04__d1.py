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
    per_seed_q = []
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        inv = 0.0
        area = 0.0
        orders = 0
        last_t = 0.0
        pending = []
        while t < H:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                nt = H
            if nt > warm:
                area += inv * (nt - max(t, warm))
            t = nt
            if t >= H:
                break
            q = math.sqrt(2.0 * K * lam / (h * c))
            inv += q
            orders += 1
        if H > warm:
            avg_inv = area / (H - warm)
        else:
            avg_inv = 0.0
        if orders > 0:
            q_est = (orders * math.sqrt(2.0 * K * lam / (h * c))) / max(orders, 1)
        else:
            q_est = math.sqrt(2.0 * K * lam / (h * c))
        per_seed_q.append(q_est)
    q = math.sqrt(2.0 * D * K / h)
    cost = math.sqrt(2.0 * D * K * h)
    out = {
        'cost': cost,
        'q': q,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': len(seed_list),
        'time_unit': 'hour',
        'per_seed_q': per_seed_q
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
