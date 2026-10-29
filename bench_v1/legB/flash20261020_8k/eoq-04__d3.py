import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    D = 1000.0
    K = 200.0
    h = 10.0
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
        t = 0.0
        inv = q_star
        warm = 0.25 * H
        area = 0.0
        demand_acc = 0.0
        last = 0.0
        while t < H:
            rate = D / 365.0
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                nt = H
            if nt > warm:
                lo = max(t, warm)
                area += inv * (nt - lo)
                demand_acc += rate * (nt - lo)
            inv -= rate * (nt - t)
            t = nt
            if inv <= 0:
                inv += q_star
        if demand_acc > 0:
            avg_inv = area / (H - warm) if H > warm else area
            per_seed_q.append(round(avg_inv, 6))
        else:
            per_seed_q.append(round(q_star, 6))

    out = {
        "cost": round(cost_star, 6),
        "q": round(q_star, 6),
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
