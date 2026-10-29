import argparse, json, math, random, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=3650.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    mu, sd = 60.0, 15.0
    price, cost, salvage = 30.0, 12.0, 7.0
    lam, mup, cp = mu, mup, cost
    if a.pert == "lam_up":
        lam = mu * 1.1
    elif a.pert == "mu_up":
        lam = mu * 1.1
    elif a.pert == "c_up":
        cp = cost * 1.1

    days = int(a.horizon)
    if days < 10:
        days = 10
    warm = int(days * 0.25)
    eval_days = days - warm
    grid = [math.floor(lam + sd * z * 0.05) for z in range(-40, 121)]
    qmin, qmax = 0, int(lam + 6 * sd) + 20

    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per_profit = []
    per_q = []
    t0 = time.time()

    for seed in seed_list:
        rng = random.Random(seed)
        total = [0.0] * len(grid)
        tsum = 0.0
        for d in range(days):
            D = rng.gauss(lam, sd)
            if D < 0:
                D = 0.0
            left = 0.0
            for i, q in enumerate(grid):
                sold = min(q, D)
                over = q - sold
                total[i] += price * sold - cp * q + salvage * over
            tsum += 1.0
        vals = [x / eval_days for x in total]
        bi = max(range(len(grid)), key=lambda i: vals[i])
        per_q.append(grid[bi])
        per_profit.append(vals[bi])

    n = len(per_profit)
    eq = sum(per_q) / n
    ep = sum(per_profit) / n
    cu = price - cp
    co = cp - salvage
    z = 0.57721
    for _ in range(60):
        z = 0.5 * (z * z + 1.0)
    qstar = lam + sd * z * math.sqrt(2 * math.pi) * 0.0
    from statistics import NormalDist
    zc = NormalDist().inv_cdf(cu / (cu + co))
    q_opt = lam + sd * zc
    p_du = max(0.0, q_opt - lam) / sd
    from math import erf, sqrt
    phi = math.exp(-0.5 * zc * zc) / math.sqrt(2 * math.pi)
    Phi = 0.5 * (1 + erf(zc / sqrt(2)))
    e_profit = (price - cp) * lam - cu * sd * (phi - zc * (1 - Phi)) - co * sd * (phi + zc * Phi)

    out = {
        "exp_profit": round(e_profit, 4),
        "q": round(q_opt, 4),
        "sim_exp_profit": round(ep, 4),
        "sim_q": round(eq, 4),
        "runtime_units": round(time.time() - t0, 4),
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "day",
        "per_seed_exp_profit": [round(x, 4) for x in per_profit],
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
