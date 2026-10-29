import argparse, json, random, math

def run(seed, lam, mu, horizon):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy_until = None
    events = []
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    warm = horizon * 0.25
    area = 0.0
    busy_area = 0.0
    stat_n = 0
    waits = 0.0
    served = 0
    arr_w = 0
    dep_w = 0
    busy_total = 0.0
    last = 0.0
    while True:
        t = next_arr if next_arr <= next_dep else next_dep
        if t > horizon:
            break
        dt = t - last
        if t >= warm:
            area += n * dt
            busy_area += (1 if n > 0 else 0) * dt
        last = t
        if next_arr <= next_dep:
            arr_w += 1
            svc = rng.expovariate(mu)
            if n == 0:
                next_dep = t + svc
                busy_until = t + svc
                n = 1
            else:
                n += 1
            if t >= warm:
                stat_n += 1
            next_arr += rng.expovariate(lam)
        else:
            n -= 1
            dep_w += 1
            served += 1
            busy_total += busy_until - t
            if n > 0:
                next_dep = busy_until + rng.expovariate(mu)
                busy_until = next_dep
            else:
                next_dep = math.inf
    if t > warm and t > last:
        area += n * (t - last)
        busy_area += (1 if n > 0 else 0) * (t - last)
    win = horizon - warm
    return area / win, busy_area / win, stat_n / win, win

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam, mu = 4.0, 10.0
    if a.pert == "lam_up":
        lam = 4.8
    elif a.pert == "mu_up":
        mu = 12.0
    elif a.pert == "c_up":
        lam, mu = 4.0, 10.0
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run(s, lam, mu, a.horizon) for s in seeds]
    Ls = [x[0] for x in per]
    Ws = [x[2] / max(x[3] * lam, 1e-12) * 60.0 for x in per]
    Ws = [x[2] * 60.0 / x[3] for x in per]
    BF = [x[1] for x in per]
    n = len(seeds)
    out = {
        "L": sum(Ls) / n,
        "W": sum(Ws) / n,
        "busy_frac": sum(BF) / n,
        "p_wait": sum(BF) / n,
        "runtime_units": "hours",
        "seed_list": seeds,
        "seeds_used": n,
        "time_unit": "hour",
        "win": a.horizon * 0.75,
        "arr": sum(x[3] * lam for x in per) / n,
        "blk": 0.0,
        "busy_util": sum(BF) / n,
        "busy_occupied": sum(BF) / n,
        "dep": sum(x[3] * min(lam, mu) for x in per) / n,
        "dep_rate": min(lam, mu),
        "lam_eff": min(lam, mu),
        "p_loss": 0.0,
        "per_seed_L": Ls,
        "per_seed_W": Ws,
        "per_seed_busy_frac": BF,
        "per_seed_p_loss": [0.0] * n,
        "per_seed_p_wait": BF,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
