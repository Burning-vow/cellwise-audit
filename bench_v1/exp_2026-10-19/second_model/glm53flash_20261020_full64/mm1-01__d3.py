import argparse, json, math, random

def run_seed(seed, horizon, warm, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    area_N = 0.0
    area_busy = 0.0
    wait_sum = 0.0
    waits = 0
    arrivals = 0
    deps = 0
    while True:
        nt = next_arr
        dt = next_dep
        t_next = nt if nt < dt else dt
        if t_next > horizon:
            break
        if t_next >= warm:
            area_N += n * (t_next - t)
            area_busy += (1 if n > 0 else 0) * (t_next - t)
        t = t_next
        if nt < dt:
            svc = rng.expovariate(mu)
            arrivals += 1 if t >= warm else 0
            if n == 0:
                next_dep = t + svc
                if t >= warm:
                    wait_sum += 0.0
                    waits += 1
            else:
                if t >= warm:
                    pass
            n += 1
            if t >= warm and n == 1:
                pass
            next_arr = t + rng.expovariate(lam)
            if n == 1:
                pass
        else:
            n -= 1
            deps += 1 if t >= warm else 0
            if n > 0:
                next_dep = t + rng.expovariate(mu)
            else:
                next_dep = math.inf
    return {}

def simulate(seed, horizon, warm, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    area_N = 0.0
    area_busy = 0.0
    wait_sum = 0.0
    waits = 0
    arrivals = 0
    deps = 0
    while t < horizon:
        t_next = min(next_arr, next_dep, horizon)
        if t_next > warm:
            a = max(t, warm)
            area_N += n * (t_next - a)
            area_busy += (1 if n > 0 else 0) * (t_next - a)
        t = t_next
        if t == horizon:
            break
        if next_arr <= next_dep:
            svc = rng.expovariate(mu)
            n += 1
            if t >= warm:
                arrivals += 1
            if n == 1:
                next_dep = t + svc
                if t >= warm:
                    waits += 1
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t >= warm:
                deps += 1
            if n > 0:
                next_dep = t + rng.expovariate(mu)
            else:
                next_dep = math.inf
    return area_N, area_busy, wait_sum, waits, arrivals, deps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=100000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    args = ap.parse_args()
    lam = 4.0
    mu = 60.0 / 6.0
    if args.pert == "lam_up":
        lam *= 1.1
    elif args.pert == "mu_up":
        mu *= 1.1
    elif args.pert == "c_up":
        pass
    horizon = args.horizon
    warm = 0.25 * horizon
    win = horizon - warm
    seeds_used = args.seeds
    seed_list = list(range(args.seed_start, args.seed_start + seeds_used))
    per_L, per_W, per_busy, per_pwait, per_ploss = [], [], [], [], []
    tot_N = tot_busy = tot_wait = 0.0
    tot_waits = tot_arr = tot_dep = 0
    for s in seed_list:
        area_N, area_busy, wait_sum, waits, arr, dep = simulate(s, horizon, warm, lam, mu)
        per_L.append(area_N / win)
        per_busy.append(area_busy / win)
        per_pwait.append(waits / arr if arr else 0.0)
        per_W.append(0.0 if waits == 0 else 0.0)
        tot_N += area_N; tot_busy += area_busy
        tot_waits += waits; tot_arr += arr; tot_dep += dep
    out = {
        "L": tot_N / (win * seeds_used),
        "W": None,
        "busy_frac": tot_busy / (win * seeds_used),
        "p_wait": tot_waits / tot_arr if tot_arr else 0.0,
        "runtime_units": "minutes",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": win,
        "arr": tot_arr / seeds_used,
        "blk": 0.0,
        "busy_util": tot_busy / (win * seeds_used),
        "dep": tot_dep / seeds_used,
        "dep_rate": tot_dep / (win / 60.0 * seeds_used),
        "lam_eff": tot_arr / (win / 60.0 * seeds_used),
        "p_loss": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
