import json, random, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=365.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    D = 5000.0
    K = 200.0
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
        # demand uniform: interarrival exponential with rate D per year
        # time unit: year
        t = 0.0
        inv = q_star
        area = 0.0
        last = 0.0
        warm = 0.25 * H
        area_warm = 0.0
        while t < H:
            rate = D
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                nt = H
            # integrate inventory area before state change
            if t >= warm:
                area_warm += inv * (nt - t)
            elif nt > warm:
                area_warm += inv * (nt - warm)
            inv -= (nt - t) * rate
            t = nt
            if inv <= 0 and t < H:
                inv += q_star
        window = H - warm
        avg_inv = area_warm / window if window > 0 else 0.0
        # estimate q from cycle: q = sqrt(2*D*K/h) but per-seed estimate via avg inv
        # use Little-like: avg_inv = q/2 => q_est = 2*avg_inv
        q_est = 2.0 * avg_inv
        per_seed_q.append(q_est)

    out = {
        "cost": cost_star,
        "q": q_star,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "year",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
