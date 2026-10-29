import json, random, argparse

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

    q_star = (2.0 * D * K / h) ** 0.5
    cost_star = (2.0 * D * K * h) ** 0.5

    H = float(a.horizon)
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        lam = D / 365.0
        t = 0.0
        inv = q_star
        orders = 0
        while t < H:
            dt = rng.expovariate(lam) if lam > 0 else H
            t += dt
            if t >= H:
                break
            inv -= 1.0
            if inv <= 0.0:
                inv += q_star
                orders += 1
        per_seed_q.append(orders * q_star / H * 365.0 if H > 0 else q_star)

    out = {
        "cost": cost_star,
        "q": q_star,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "second",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
