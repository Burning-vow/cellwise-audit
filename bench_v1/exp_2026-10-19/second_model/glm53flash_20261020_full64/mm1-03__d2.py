import argparse, json, random, math

def run_seed(seed, horizon, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    t_next_arr = rng.expovariate(lam)
    t_next_dep = math.inf
    warm = horizon * 0.25
    area = 0.0
    busy_area = 0.0
    wait_sum = 0.0
    served = 0
    waited = 0
    arrivals = 0
    lost = 0
    win_time = 0.0
    while True:
        if t_next_arr <= t_next_dep:
            t_next = t_next_arr
        else:
            t_next = t_next_dep
        if t_next > horizon:
            t_next = horizon
        dt = t_next - t
        if t >= warm:
            area += n * dt
            busy_area += min(n, 1) * dt
            win_time += dt
        t = t_next
        if t >= horizon:
            break
        if t_next_arr <= t_next_dep:
            arrivals += 1
            svc = rng.expovariate(mu)
            if n == 0:
                t_next_dep = t + svc
                if t >= warm:
                    served += 1
                    wait_sum += 0.0
                n = 1
            else:
                n += 1
                if t >= warm:
                    served += 1
                    waited += 1
                    wait_sum += svc
            t_next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if n > 0:
                svc = rng.expovariate(mu)
                t_next_dep = t + svc
                if t >= warm:
                    served += 1
                    waited += 1
                    wait_sum += svc
            else:
                t_next_dep = math.inf
    win = horizon - warm
    L = area / win if win > 0 else 0.0
    busy = busy_area / win if win > 0 else 0.0
    W = wait_sum / served if served > 0 else 0.0
    pw = waited / served if served > 0 else 0.0
    pl = lost / arrivals if arrivals > 0 else 0.0
    return L, W, busy, pw, pl, arrivals, served, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    ns = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu = 6.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.05
    seed_list = [S + i for i in range(ns)]
    per_L, per_W, per_b, per_pw, per_pl = [], [], [], [], []
    tot_arr = tot_dep = 0.0
    for s in seed_list:
        L, W, b, pw, pl, arr, dep, win = run_seed(s, H, lam, mu)
        per_L.append(L); per_W.append(W); per_b.append(b)
        per_pw.append(pw); per_pl.append(pl)
        tot_arr += arr; tot_dep += dep
    k = len(seed_list)
    win = H * 0.75
    out = {
        "L": sum(per_L)/k, "W": sum(per_W)/k, "busy_frac": sum(per_b)/k,
        "p_wait": sum(per_pw)/k, "runtime_units": "hour",
        "seed_list": seed_list, "seeds_used": k, "time_unit": "hour", "win": win,
        "arr": tot_arr/k, "blk": 0.0, "busy_util": sum(per_b)/k,
        "busy_occupied": sum(per_b)/k, "dep": tot_dep/k,
        "dep_rate": tot_arr/(k*win), "lam_eff": lam,
        "p_loss": sum(per_pl)/k,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_b, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
