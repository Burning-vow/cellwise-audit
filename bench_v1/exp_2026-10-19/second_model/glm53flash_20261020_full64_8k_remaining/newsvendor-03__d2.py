import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=100000)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    p, c, s = 30.0, 12.0, 4.0
    mu, sig = 60.0, 15.0
    if a.pert == "lam_up":
        mu *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c *= 1.1
    grid = list(range(int(mu - 4 * sig), int(mu + 4 * sig) + 1))
    per_seed_q, per_seed_profit, seeds_used = [], [], 0
    seed_list = []
    t0 = time.time()
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        n = max(1, int(a.horizon))
        warm = int(0.25 * n)
        best_q, best_v = None, -1e18
        for q in grid:
            tot = 0.0
            cnt = 0
            for d in range(n):
                D = rng.gauss(mu, sig)
                if d >= warm:
                    D = max(0.0, D)
                    tot += p * min(D, q) + s * max(0.0, q - D) - c * q
                    cnt += 1
            v = tot / cnt
            if v > best_v:
                best_v, best_q = v, q
        per_seed_q.append(best_q)
        rng2 = random.Random(seed + 1000000)
        tot = 0.0
        cnt = 0
        for d in range(n):
            D = max(0.0, rng2.gauss(mu, sig))
            if d >= warm:
                tot += p * min(D, best_q) + s * max(0.0, best_q - D) - c * best_q
                cnt += 1
        per_seed_profit.append(tot / cnt)
        seeds_used += 1
        seed_list.append(seed)
    exp_profit = sum(per_seed_profit) / seeds_used
    avg_q = sum(per_seed_q) / seeds_used
    cr = (p - c) / (p - c + c - s)
    z = 0.0
    lo, hi = -5.0, 5.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < cr:
            lo = mid
        else:
            hi = mid
    z = 0.5 * (lo + hi)
    q_theory = mu + z * sig
    out = {
        "exp_profit": exp_profit,
        "q": avg_q,
        "runtime_units": time.time() - t0,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "day",
        "per_seed_exp_profit": per_seed_profit,
        "per_seed_q": per_seed_q,
        "q_newsvendor_theory": q_theory,
        "critical_ratio": cr,
        "pert": a.pert,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
