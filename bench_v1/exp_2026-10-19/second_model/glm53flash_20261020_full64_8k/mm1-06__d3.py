import argparse, json, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=2000.0)
    p.add_argument("--seed-start", type=int, default=12345)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam, mu = 7.0, 12.0
    if a.pert == "lam_up": lam = 8.0
    elif a.pert == "mu_up": mu = 13.2
    elif a.pert == "c_up": lam, mu = 7.0, 12.0
    t0 = 0.25 * a.horizon
    results = []
    seeds_used = 0
    seed_list = []
    for k in range(a.seeds):
        seed = a.seed_start + k
        rnd = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0.0
        area = 0.0
        wsum = 0.0
        n_arr = 0
        n_dep = 0
        n_wait = 0
        n_loss = 0
        queue = []
        next_arr = rnd.expovariate(lam)
        next_dep = None
        while t < a.horizon:
            if next_dep is None or next_arr <= next_dep:
                te = next_arr
            else:
                te = next_dep
            if te > a.horizon:
                te = a.horizon
            dt = te - t
            if te >= t0:
                area += n * dt
                busy += min(n, 1) * dt
            t = te
            if t >= a.horizon:
                break
            if next_dep is None or next_arr <= next_dep:
                svc = rnd.expovariate(mu)
                n_arr += 1
                waited = n > 0
                if t >= t0:
                    if waited: n_wait += 1
                n += 1
                queue.append(svc)
                next_arr = t + rnd.expovariate(lam)
                if next_dep is None:
                    next_dep = t + queue.pop(0)
            else:
                n -= 1
                n_dep += 1
                if queue:
                    next_dep = t + queue.pop(0)
                else:
                    next_dep = None
        win = a.horizon - t0
        L = area / win
        bf = busy / win
        W = L / lam * 60.0
        results.append((L, W, bf, n_wait, n_loss))
        seeds_used += 1
        seed_list.append(seed)
    L = sum(r[0] for r in results) / seeds_used
    W = sum(r[1] for r in results) / seeds_used
    bf = sum(r[2] for r in results) / seeds_used
    pw = sum(r[3] for r in results) / seeds_used
    pl = sum(r[4] for r in results) / seeds_used
    out = {
        "L": L, "W": W, "busy_frac": bf, "busy_util": bf,
        "busy_occupied": bf, "p_wait": pw, "p_loss": pl,
        "arr": 0.0, "dep": 0.0, "blk": 0.0,
        "dep_rate": lam, "lam_eff": lam,
        "time_unit": "hour", "runtime_units": "hour",
        "win": a.horizon - 0.25 * a.horizon,
        "seed_list": seed_list, "seeds_used": seeds_used,
        "per_seed_L": [r[0] for r in results],
        "per_seed_W": [r[1] for r in results],
        "per_seed_busy_frac": [r[2] for r in results],
        "per_seed_p_loss": [r[4] for r in results],
        "per_seed_p_wait": [r[3] for r in results],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
