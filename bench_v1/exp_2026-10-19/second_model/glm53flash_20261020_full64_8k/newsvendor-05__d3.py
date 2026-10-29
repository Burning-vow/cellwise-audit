import argparse, json, math, random, time

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=lambda x: float(x), default=3650.0)
    p.add_argument("--seed-start", dest="seed_start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    return p.parse_args()

def day_profit(q, demand, price, cost, salvage):
    sold = min(q, demand)
    return sold * price + (q - sold) * salvage - q * cost

def run_seed(seed, horizon, mu, sigma, price, cost, salvage, warm_frac=0.25):
    rng = random.Random(seed)
    n_days = int(horizon)
    warm = int(n_days * warm_frac)
    q_grid = list(range(10, 121, 2))
    best_q, best_prof = None, -1e18
    demands = [max(0.0, rng.gauss(mu, sigma)) for _ in range(n_days)]
    for q in q_grid:
        tot = 0.0
        for t in range(warm, n_days):
            tot += day_profit(q, demands[t], price, cost, salvage)
        avg = tot / (n_days - warm)
        if avg > best_prof:
            best_prof, best_q = avg, q
    prof_sum = 0.0
    for t in range(warm, n_days):
        prof_sum += day_profit(best_q, demands[t], price, cost, salvage)
    return best_prof, best_q, prof_sum / (n_days - warm)

def main():
    t0 = time.time()
    a = parse_args()
    n_seeds = a.seeds
    horizon = float(a.horizon)
    S = a.seed_start
    pert = a.pert
    price, cost, salvage = 30.0, 12.0, 7.0
    mu, sigma = 60.0, 15.0
    if pert == "lam_up":
        mu += 6.0
    elif pert == "mu_up":
        mu += 6.0
    elif pert == "c_up":
        cost += 2.0
    per_prof, per_q, seed_list = [], [], []
    for i in range(n_seeds):
        seed = S + i
        seed_list.append(seed)
        ep, q, _ = run_seed(seed, horizon, mu, sigma, price, cost, salvage)
        per_prof.append(round(ep, 6))
        per_q.append(q)
    exp_profit = sum(per_prof) / n_seeds if n_seeds else 0.0
    q_mean = sum(per_q) / n_seeds if n_seeds else 0
    out = {
        "exp_profit": round(exp_profit, 4),
        "q": round(q_mean, 2),
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "day",
        "per_seed_exp_profit": per_prof,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
