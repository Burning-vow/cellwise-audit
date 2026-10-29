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
        # simulate inventory with (q_star) policy over horizon, measure avg inventory
        # time unit: day; demand rate per day
        rate = D / 365.0
        t = 0.0
        inv = q_star
        area = 0.0
        warm = 0.25 * H
        warm_area = 0.0
        warm_time = 0.0
        while t < H:
            # time to next order arrival: exponential with mean q_star/rate
            dt = rng.expovariate(rate / q_star) if rate > 0 else H
            if t + dt > H:
                dt = H - t
            # integrate area before state change
            if t >= warm:
                area += inv * dt
                warm_time += dt
            elif t + dt > warm:
                part = (t + dt - warm)
                area += inv * part
                warm_time += part
            inv -= rate * dt
            t += dt
            if inv <= 0 and t < H:
                inv += q_star
        avg_inv = area / warm_time if warm_time > 0 else 0.0
        # estimate q from cycle: q = avg_inv * 2 (sawtooth average = q/2)
        q_est = 2.0 * avg_inv
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
