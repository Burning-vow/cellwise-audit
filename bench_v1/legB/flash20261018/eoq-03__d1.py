import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=365.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    D = 1000.0
    K = 50.0
    h = 10.0
    if a.pert == "lam_up":
        D = D * 1.2
    elif a.pert == "mu_up":
        K = K * 0.8
    elif a.pert == "c_up":
        h = h * 1.2
    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_seed_q = []
    for s in seeds:
        rng = random.Random(s)
        T = a.horizon
        warm = 0.25 * T
        t = 0.0
        inv = q_star
        area = 0.0
        demand_total = 0.0
        orders = 0
        while t < T:
            rate = D / 365.0
            dt = rng.expovariate(rate) if rate > 0 else float("inf")
            nxt = t + dt
            if nxt > T:
                nxt = T
            seg = nxt - t
            if t >= warm:
                area += inv * seg
            inv -= rate * seg
            if t >= warm:
                demand_total += rate * seg
            t = nxt
            if inv <= 0.0 and t < T:
                inv += q_star
                if t >= warm:
                    orders += 1
        win = T - warm
        if win <= 0:
            per_seed_q.append(q_star)
        else:
            avg_inv = area / win
            if avg_inv > 0:
                per_seed_q.append(2.0 * demand_total / max(orders, 1) if orders > 0 else q_star)
            else:
                per_seed_q.append(q_star)
    out = {
        "cost": cost_star,
        "q": q_star,
        "runtime_units": a.horizon,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
