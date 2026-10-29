import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=42)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    mu, sigma, price, cost, salvage = 60.0, 25.0, 30.0, 12.0, 7.0
    if args.pert == "lam_up":
        mu = 66.0
    elif args.pert == "mu_up":
        mu = 66.0
    elif args.pert == "c_up":
        cost = 15.0

    n_days = max(int(args.horizon), 100)
    warm = int(n_days * 0.25)
    use_days = n_days - warm

    z = 0.7797602693709942
    q_star = mu + sigma * z
    grid = [max(0, int(q_star) + d) for d in range(-15, 16)]
    grid.append(int(round(q_star)))

    per_q, per_qbest, seed_list = [], [], []
    for k in range(args.seeds):
        seed = args.seed_start + k
        rng = random.Random(seed)
        demands = [max(0.0, rng.gauss(mu, sigma)) for _ in range(n_days)]
        best_q, best_p, per_seed_p = None, -1e18, None
        for q in grid:
            tot = 0.0
            for d in demands[warm:]:
                sold = min(d, q)
                tot += price * sold + salvage * max(0.0, q - d) - cost * q
            p = tot / use_days
            per_seed_p = p
            if p > best_p:
                best_p, best_q = p, q
        per_q.append(per_seed_p)
        per_qbest.append(best_q)
        per_q[-1] = best_p
        seed_list.append(seed)

    exp_profit = sum(per_q) / len(per_q)
    q_mean = sum(per_qbest) / len(per_qbest)

    out = {
        "exp_profit": exp_profit,
        "q": q_mean,
        "runtime_units": "day",
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_exp_profit": per_q,
        "per_seed_q": per_qbest,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
