import argparse, json, math, random, time

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=10000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    t0 = time.time()
    mu, sd = 60.0, 25.0
    price, cost, salvage = 20.0, 12.0, 7.0
    if a.pert == "lam_up": mu *= 1.2
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": cost *= 1.1
    H = int(a.horizon)
    warm = int(H * 0.25)
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per_profit, per_q = [], []
    for s in seed_list:
        rng = random.Random(s * 7919 + 13)
        demands = [max(0.0, rng.gauss(mu, sd)) for _ in range(H)]
        best_q, best_p = 0, -1e18
        for q in range(0, 220):
            tot = 0.0
            for d in demands[warm:]:
                sold = min(d, q)
                tot += price * sold + salvage * max(0.0, q - d) - cost * q
            avg = tot / (H - warm)
            if avg > best_p:
                best_p, best_q = avg, q
        per_profit.append(best_p)
        per_q.append(float(best_q))
    exp_profit = sum(per_profit) / len(per_profit)
    q_opt = sum(per_q) / len(per_q)
    z = 0.0
    target = (price - cost) / (price - salvage)
    lo, hi = -10.0, 10.0
    for _ in range(200):
        z = (lo + hi) / 2
        if 0.5 * (1 + math.erf(z / math.sqrt(2))) < target: lo = z
        else: hi = z
    q_analytic = mu + z * sd
    out = {
        "exp_profit": exp_profit,
        "q": q_opt,
        "q_analytic_fractile": q_analytic,
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "day",
        "per_seed_exp_profit": per_profit,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
