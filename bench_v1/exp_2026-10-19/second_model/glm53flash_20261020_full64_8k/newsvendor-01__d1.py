import argparse, json, math, random
from statistics import NormalDist

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=10000)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()

    n_seeds = int(args.seeds)
    horizon = args.horizon
    seed_start = int(args.seed_start)
    pert = args.pert

    mu, sigma = 60.0, 15.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if pert == "lam_up":
        mu += 6.0
    elif pert == "mu_up":
        mu += 6.0
    elif pert == "c_up":
        cost += 1.0

    warmup_frac = 0.25
    cu = price - cost
    co = cost - salvage
    z = NormalDist().inv_cdf(cu / (cu + co))
    q_star = mu + z * sigma

    per_seed_profit = []
    per_seed_q = []
    seed_list = []
    nd = NormalDist(mu, sigma)

    for i in range(n_seeds):
        seed = seed_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        n_days = int(horizon)
        warm = int(n_days * warmup_frac)
        demands = [max(0.0, rng.gauss(mu, sigma)) for _ in range(n_days)]
        eval_days = demands[warm:]
        eval_days.sort()

        def profit_at(q):
            tot = 0.0
            for d in demands[warm:]:
                sold = min(q, d)
                tot += sold * price - q * cost + (q - sold) * salvage
            return tot / len(eval_days) if eval_days else 0.0

        best_q = q_star
        best_p = profit_at(q_star)
        lo = max(0.0, q_star - 5 * sigma)
        hi = q_star + 5 * sigma
        step = (hi - lo) / 400.0
        qs = [lo + k * step for k in range(401)]
        best_q, best_p = qs[0], profit_at(qs[0])
        for q in qs[1:]:
            p = profit_at(q)
            if p > best_p:
                best_p, best_q = p, q
        per_seed_q.append(best_q)
        per_seed_profit.append(best_p)

    exp_profit = sum(per_seed_profit) / len(per_seed_profit) if per_seed_profit else 0.0
    q_hat = sum(per_seed_q) / len(per_seed_q) if per_seed_q else 0.0

    out = {
        "exp_profit": exp_profit,
        "q": q_hat,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
