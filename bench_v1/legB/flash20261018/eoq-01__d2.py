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
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        inv = q_star
        area = 0.0
        orders = 0
        while t < H:
            rate = D / 365.0
            if inv <= 0.0:
                inv += q_star
                orders += 1
            dt = inv / rate if rate > 0 else H - t
            nxt = t + dt
            if nxt > H:
                nxt = H
            if t >= warm:
                area += inv * (nxt - t)
            inv -= rate * (nxt - t)
            t = nxt
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
        'time_unit': 'day',
        'per_seed_q': per_seed_q,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
