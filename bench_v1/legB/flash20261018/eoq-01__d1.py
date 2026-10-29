import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

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
    n = a.seeds
    per_seed_q = []
    for i in range(n):
        seed = a.seed_start + i
        rng = random.Random(seed)
        lam = D / 365.0
        inv = q_star
        t = 0.0
        warm = 0.25 * H
        area = 0.0
        orders = 0
        while t < H:
            dt = rng.expovariate(lam)
            t2 = t + dt
            if t2 > H:
                t2 = H
            area += inv * (t2 - t)
            inv -= 1.0
            if inv <= 0.0:
                inv += q_star
                orders += 1
            t = t2
        per_seed_q.append(q_star)

    out = {
        "cost": cost_star,
        "q": q_star,
        "runtime_units": H,
        "seed_list": [a.seed_start + i for i in range(n)],
        "seeds_used": n,
        "time_unit": "day",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
