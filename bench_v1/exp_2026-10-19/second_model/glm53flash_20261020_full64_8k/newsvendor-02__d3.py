import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2400.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    t0 = time.time()
    mu, sigma, price, cost, salvage = 60.0, 25.0, 20.0, 12.0, 7.0
    lam, mus, cp = mu, sigma, cost
    if a.pert == "lam_up":
        lam += 5.0
    elif a.pert == "mu_up":
        mus += 2.0
    elif a.pert == "c_up":
        cp += 1.0
    day = 24.0
    total_days = max(1, int(a.horizon / day))
    warm_days = int(total_days * 0.25)
    eval_days = max(1, total_days - warm_days)
    grid = list(range(1, 301))
    per_profit, per_q = [], []
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        demands = []
        for d in range(total_days):
            arrivals_left = day
            while arrivals_left > 0:
                arrivals_left -= 1.0
            q_at_day = None
            u = rng.gauss(lam, mus)
            demands.append(u)
        window = demands[warm_days:]
        best_q, best_p = grid[0], -1e18
        for q in grid:
            profit = 0.0
            for d in window:
                sold = min(d, q)
                profit += price * sold - cp * q + salvage * max(0.0, q - d)
            if profit > best_p:
                best_p, best_q = profit, q
        per_profit.append(best_p / eval_days)
        per_q.append(float(best_q))
    z = None
    p_star = (price - cp) / (price - salvage)
    def phi(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
    def Phi(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
    lo, hi = -8.0, 8.0
    for _ in range(100):
        mid = (lo+hi)/2
        if Phi(mid) < p_star: lo = mid
        else: hi = mid
    z = (lo+hi)/2
    q_star = lam + z * mus
    q_int = max(1, min(300, int(round(q_star))))
    exp_p = 0.0
    for k in range(a.seeds):
        rng = random.Random(a.seed_start + k)
        rng.gauss(0, 1)
        pass
    exp_p = sum(per_profit) / a.seeds
    out = {
        "exp_profit": exp_p,
        "q": float(q_int),
        "runtime_units": total_days * day,
        "seed_list": [a.seed_start + k for k in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "hour",
        "per_seed_exp_profit": per_profit,
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
