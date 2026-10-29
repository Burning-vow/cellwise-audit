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
        # Poisson demand process
        while t < H:
            # time to next demand
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            if t + dt > H:
                # integrate remaining
                if t >= warm:
                    area += inv * (H - t)
                else:
                    if H > warm:
                        area += inv * (H - max(t, warm))
                break
            # integrate area up to t+dt
            seg_end = t + dt
            if t >= warm:
                area += inv * dt
            elif seg_end > warm:
                area += inv * (seg_end - warm)
            t = seg_end
            inv -= 1.0
            if inv <= 0:
                inv += q_star
        # average inventory over post-warm window
        window = H - warm
        if window <= 0:
            window = H
        avg_inv = area / window if window > 0 else 0.0
        # estimate q from cycle: q = 2*avg_inv (sawtooth average = q/2)
        q_est = 2.0 * avg_inv
        per_seed_q.append(q_est)

    mean_q = sum(per_seed_q) / len(per_seed_q) if per_seed_q else q_star
    # cost using estimated q
    cost_est = K * D / mean_q + h * mean_q / 2.0 if mean_q > 0 else cost_star

    out = {
        "cost": cost_est,
        "q": mean_q,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
