import argparse, json, math, random, sys

def parse_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    return p.parse_args(argv)

def main():
    a = parse_args(sys.argv[1:])
    mu, sd, price, cost, salvage = 60.0, 25.0, 30.0, 12.0, 7.0
    lam = 1.0
    if a.pert == "lam_up":
        lam = 1.2
    elif a.pert == "mu_up":
        mu = 66.0
    elif a.pert == "c_up":
        cost = 14.0
    days = max(1, int(a.horizon))
    warm = int(days * 0.25)
    n_seed = max(1, a.seeds)
    seed_list = list(range(a.seed_start, a.seed_start + n_seed))
    qs = [q * 1.0 for q in range(0, 201)]
    per_seed_exp = []
    per_seed_q = []
    for s in seed_list:
        rng = random.Random(s * 7919 + 13)
        g = random.Random(s * 104729 + 7)
        best_q, best_pf = 0.0, -1e18
        for q in qs:
            tot = 0.0
            cnt = 0
            for d in range(days):
                dem = max(0.0, g.gauss(mu, sd))
                sold = min(q, dem)
                prof = sold * price - q * cost + (q - sold) * salvage
                if d >= warm:
                    tot += prof
                    cnt += 1
            avg = tot / cnt
            if avg > best_pf:
                best_pf = avg
                best_q = q
        per_seed_exp.append(best_pf)
        per_seed_q.append(best_q)
    exp_profit = sum(per_seed_exp) / len(per_seed_exp)
    q_star = per_seed_q[len(per_seed_q) // 2] if len(set(per_seed_q)) > 1 else per_seed_q[0]
    z = None
    out = {
        "exp_profit": round(exp_profit, 4),
        "q": q_star,
        "runtime_units": days,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp],
        "per_seed_q": per_seed_q,
        "lam": lam,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
