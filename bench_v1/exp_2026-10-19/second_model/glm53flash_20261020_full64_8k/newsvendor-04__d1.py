import argparse, json, math, random, time, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=5)
    p.add_argument("--horizon", type=float, default=100000)
    p.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    mean, sd, price, cost, salvage = 60.0, 25.0, 30.0, 12.0, 4.0
    if pert == "lam_up": mean += 10.0
    elif pert == "mu_up": sd += 5.0
    elif pert == "c_up": cost += 2.0
    z = 18.0 / 26.0
    q_star = mean + sd * 1.0
    t0 = time.time()
    per_seed_exp, per_seed_q, seed_list = [], [], []
    qs = list(range(10, 131))
    for i in range(n_seeds):
        seed = S + i
        seed_list.append(seed)
        rng = random.Random(seed * 100003 + 7)
        warm = int(H * 0.25)
        best_q, best_pf, best_var_sum, best_n = 0, -1e18, 0.0, 0
        pf_acc = {}
        for q in qs:
            tot, n = 0.0, 0
            for d in range(int(H)):
                dem = rng.gauss(mean, sd)
                if dem < 0: dem = 0.0
                sold = min(q, dem)
                pf = price * sold + salvage * max(0.0, q - dem) - cost * q
                if d >= warm:
                    tot += pf; n += 1
                if q == 72:
                    pass
            pf_acc[q] = tot / n if n else 0.0
        bq = max(pf_acc, key=lambda k: pf_acc[k])
        rng2 = random.Random(seed * 100003 + 13)
        tot, n = 0.0, 0
        for d in range(int(H)):
            dem = rng2.gauss(mean, sd)
            if dem < 0: dem = 0.0
            sold = min(bq, dem)
            pf = price * sold + salvage * max(0.0, bq - dem) - cost * bq
            if d >= warm:
                tot += pf; n += 1
        per_seed_exp.append(tot / n if n else 0.0)
        per_seed_q.append(bq)
    q_hat = sum(per_seed_q) / len(per_seed_q)
    exp_pf = sum(per_seed_exp) / len(per_seed_exp)
    out = {
        "exp_profit": round(exp_pf, 4),
        "q": round(q_hat, 4),
        "runtime_units": round(time.time() - t0, 6),
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "hour",
        "per_seed_exp_profit": [round(x, 4) for x in per_seed_exp],
        "per_seed_q": [float(x) for x in per_seed_q],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
