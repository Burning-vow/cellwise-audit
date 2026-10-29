import argparse, json, random, math

def sweep(A, D, a, b, indicator):
    i = j = 0
    while i < len(A) and A[i] <= a: i += 1
    while j < len(D) and D[j] <= a: j += 1
    ca, cd = i, j
    t = a; acc = 0.0
    while t < b:
        ta = A[i] if i < len(A) else math.inf
        td = D[j] if j < len(D) else math.inf
        t2 = min(ta, td, b)
        N = ca - cd
        if indicator:
            acc += (1.0 if N >= 1 else 0.0) * (t2 - t)
        else:
            acc += N * (t2 - t)
        while i < len(A) and A[i] <= t2: i += 1; ca += 1
        while j < len(D) and D[j] <= t2: j += 1; cd += 1
        t = t2
    return acc

def run_seed(seed, H, pert):
    rng = random.Random(seed)
    lam = 4.0
    mu1 = 60.0 / 6.0
    mu2 = 60.0 / 5.0
    if pert == "lam_up": lam *= 1.1
    if pert == "mu_up": mu1 *= 1.1
    if pert == "c_up": mu1 *= 2.0
    A = []; D1 = []; D2 = []
    t = 0.0; f1 = 0.0; f2 = 0.0
    waits = 0; arr_n = 0
    while True:
        t += rng.expovariate(lam)
        if t >= H: break
        A.append(t); arr_n += 1
        s1 = rng.expovariate(mu1)
        d1 = max(t, f1) + s1; f1 = d1; D1.append(d1)
        if t < f1: waits += 1
        s2 = rng.expovariate(mu2)
        d2 = max(d1, f2) + s2; f2 = d2; D2.append(d2)
    a = 0.25 * H; b = H; win = b - a
    L = sweep(A, D2, a, b, False) / win
    busy1 = sweep(A, D1, a, b, True) / win
    dep = sum(1 for d in D2 if a <= d < b)
    arrw = sum(1 for x in A if a <= x < b)
    soj = [d - x for x, d in zip(A, D2) if a <= d < b]
    W = (sum(soj) / len(soj)) * 60.0 if soj else (L * 60.0 / (dep / win if dep > 0 else 1e-9))
    pw = waits / arr_n if arr_n else 0.0
    return L, W, arrw, dep, busy1, 0.0, pw, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()
    n = int(args.seeds); H = float(args.horizon); s0 = int(args.seed_start)
    pert = args.pert
    res = [run_seed(s0 + k, H, pert) for k in range(n)]
    win = res[0][7]
    per_L = [r[0] for r in res]; per_W = [r[1] for r in res]
    per_bf = [r[4] for r in res]; per_pl = [r[5] for r in res]; per_pw = [r[6] for r in res]
    arr = sum(r[2] for r in res) / n; dep = sum(r[3] for r in res) / n
    m = lambda xs: sum(xs) / len(xs)
    out = {
        "L": m(per_L), "W": m(per_W),
        "runtime_units": H, "seed_list": [s0 + k for k in range(n)],
        "seeds_used": n, "time_unit": "hour", "win": win,
        "arr": arr, "dep": dep, "blk": 0.0,
        "busy_frac": m(per_bf), "busy_util": m(per_bf),
        "lam_eff": arr / win, "dep_rate": dep / win,
        "p_loss": 0.0, "p_wait": m(per_pw),
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
