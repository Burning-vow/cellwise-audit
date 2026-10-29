import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=24000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    mu, sd, price, cost, salvage = 60.0, 25.0, 30.0, 12.0, 7.0
    if a.pert == "lam_up":
        mu += 10.0
    elif a.pert == "mu_up":
        mu += 10.0
    elif a.pert == "c_up":
        cost += 2.0

    days = max(1, int(round(a.horizon / 24.0)))
    warm = days // 4
    eval_days = days - warm
    q_grid = [math.floor(mu - 4 * sd + i * 0.5) for i in range(int(8 * sd / 0.5) + 1)]

    per_seed_exp, per_seed_q = [], []
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    t0 = time.time()
    for s in seed_list:
        rng = random.Random(s * 7919 + 13)
        draws = [rng.gauss(mu, sd) for _ in range(days)]
        best_q, best_val = None, -1e18
        vals = {}
        for q in q_grid:
            tot = 0.0
            for d in draws[warm:]:
                if d >= 0:
                    sold = min(q, d)
                    tot += price * sold - cost * q + salvage * max(0.0, q - d)
            v = tot / eval_days
            vals[q] = v
            if v > best_val:
                best_val, best_q = v, q
        per_seed_exp.append(vals[best_q])
        per_seed_q.append(float(best_q))

    exp_profit = sum(per_seed_exp) / len(per_seed_exp)
    q_star = sum(per_seed_q) / len(per_seed_q)
    out = {
        "exp_profit": exp_profit,
        "q": q_star,
        "runtime_units": time.time() - t0,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "per_seed_exp_profit": per_seed_exp,
        "per_seed_q": per_seed_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
