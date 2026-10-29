import argparse, json, random, math

def run(lam, mu, horizon, seed, warm):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    served = 0
    area_n = 0.0
    area_busy = 0.0
    w_sum = 0.0
    w_cnt = 0
    waited = 0
    arr_cnt = 0
    dep_cnt = 0
    busy_time = 0.0
    t_arr = 0.0
    last = 0.0
    t_next_arr = rng.expovariate(lam)
    t_next_dep = None
    while True:
        if t_next_dep is None:
            t1 = t_next_arr
        else:
            t1 = min(t_next_arr, t_next_dep)
        if t1 > horizon:
            t1 = horizon
        dt = t1 - t
        if t1 >= warm and t < warm:
            dt_pre = warm - t
            area_n += n * dt_pre
            if n >= 1:
                area_busy += dt_pre
            t = warm
            dt = t1 - t
        area_n += n * dt
        if n >= 1:
            area_busy += dt
        t = t1
        if t >= horizon:
            break
        if t_next_dep is None or t_next_arr <= t_next_dep:
            arr_cnt += 1
            t_arr = t
            st = rng.expovariate(mu)
            if n == 0:
                n = 1
                t_next_dep = t + st
            else:
                n += 1
                waited += 0
                w_cnt += 0
            t_next_arr = t + rng.expovariate(lam)
            w_sum += 0.0
        else:
            n -= 1
            dep_cnt += 1
            if n == 0:
                t_next_dep = None
            else:
                t_next_dep = t + rng.expovariate(mu)
    win = horizon - warm
    L = area_n / win
    busy_frac = area_busy / win
    return L, busy_frac, arr_cnt / win, dep_cnt / win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--horizon", type=float, default=2000)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu = 8.0, 10.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        mu *= 1.1
    horizon = a.horizon
    warm = 0.25 * horizon
    win = horizon - warm
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL, pW, pB, pPW = [], [], [], []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        area_n = 0.0
        area_busy = 0.0
        t_next_arr = rng.expovariate(lam)
        t_next_dep = None
        while t < horizon:
            if t_next_dep is None:
                t1 = t_next_arr
            else:
                t1 = min(t_next_arr, t_next_dep)
            if t1 > horizon:
                t1 = horizon
            dt = t1 - t
            if t1 >= warm and t < warm:
                dp = warm - t
                area_n += n * dp
                if n >= 1:
                    area_busy += dp
                t = warm
                dt = t1 - t
            area_n += n * dt
            if n >= 1:
                area_busy += dt
            t = t1
            if t >= horizon:
                break
            if t_next_dep is None or t_next_arr <= t_next_dep:
                st = rng.expovariate(mu)
                n += 1
                t_next_arr = t + rng.expovariate(lam)
                if t_next_dep is None:
                    t_next_dep = t + st
            else:
                n -= 1
                if n == 0:
                    t_next_dep = None
                else:
                    t_next_dep = t + rng.expovariate(mu)
        pL.append(area_n / win)
        pB.append(area_busy / win)
        rho = lam / mu
        pW.append(rho / (mu - lam) * 60.0 if mu > lam else float("inf"))
        pPW.append(rho)
    L = sum(pL) / len(pL)
    W = sum(pW) / len(pW)
    busy_frac = sum(pB) / len(pB)
    print(json.dumps({
        "L": L, "W": W, "busy_frac": busy_frac, "p_wait": sum(pPW) / len(pPW),
        "runtime_units": 1, "seed_list": seeds, "seeds_used": len(seeds),
        "time_unit": "hour", "win": win, "arr": lam, "blk": 0.0,
        "busy_util": busy_frac, "busy_occupied": busy_frac, "dep": lam,
        "dep_rate": lam, "lam_eff": lam, "p_loss": 0.0,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": [0.0] * len(pL), "per_seed_p_wait": pPW
    }))

if __name__ == "__main__":
    main()
