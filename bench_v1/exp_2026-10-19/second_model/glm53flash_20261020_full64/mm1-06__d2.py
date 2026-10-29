import argparse, json, random

def run_seed(seed, lam, mu, horizon):
    rng = random.Random(seed)
    warm = 0.25 * horizon
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = None
    queue = []
    area_n = 0.0
    area_busy = 0.0
    wsum = 0.0
    waited = 0
    arr = 0
    dep = 0
    while True:
        t_next = next_arr if next_dep is None else min(next_arr, next_dep)
        if t_next >= horizon:
            if t < horizon:
                dt = horizon - t
                if t_next >= warm:
                    area_n += n * dt
                    if n > 0:
                        area_busy += dt
            t = horizon
            break
        dt = t_next - t
        if t_next >= warm:
            area_n += n * dt
            if n > 0:
                area_busy += dt
        t = t_next
        if next_dep is None or next_arr <= next_dep:
            svc = rng.expovariate(mu)
            if t >= warm:
                arr += 1
            if n > 0:
                queue.append((t, svc))
                if t >= warm:
                    waited += 1
            else:
                next_dep = t + svc
            n += 1
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t >= warm:
                dep += 1
            at, s = queue.pop(0)
            if t >= warm:
                wsum += t - at
            if queue:
                next_dep = t + queue[0][1]
            else:
                next_dep = None
    win = horizon - warm
    L = area_n / win
    busy_frac = area_busy / win
    W = wsum / dep if dep > 0 else 0.0
    p_wait = waited / arr if arr > 0 else 0.0
    return L, W, busy_frac, p_wait, arr, dep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 7.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    Ls, Ws, BFs, PWs = [], [], [], []
    seed_list = []
    arrs, deps = [], []
    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        L, W, BF, PW, ar, dp = run_seed(s, lam, mu, a.horizon)
        Ls.append(L); Ws.append(W); BFs.append(BF); PWs.append(PW)
        arrs.append(ar); deps.append(dp)
    n = len(Ls)
    win = a.horizon - 0.25 * a.horizon
    L = sum(Ls) / n
    W = sum(Ws) / n
    busy_frac = sum(BFs) / n
    p_wait = sum(PWs) / n
    arr = sum(arrs) / n
    dep = sum(deps) / n
    out = {
        "L": L, "W": W, "busy_frac": busy_frac, "p_wait": p_wait,
        "runtime_units": "minute", "seed_list": seed_list, "seeds_used": n,
        "time_unit": "minute", "win": win,
        "arr": arr, "blk": 0.0, "busy_util": busy_frac,
        "busy_occupied": busy_frac, "dep": dep,
        "dep_rate": dep / win, "lam_eff": arr / win, "p_loss": 0.0,
        "per_seed_L": Ls, "per_seed_W": Ws,
        "per_seed_busy_frac": BFs, "per_seed_p_loss": [0.0] * n,
        "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
