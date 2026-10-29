import argparse, json, random, math

def simulate(seed, lam, mean_svc, H, warm):
    rng = random.Random(seed)
    t = 0.0
    busy = False
    t_arr = rng.expovariate(lam)
    t_dep = math.inf
    queue = []
    area_n = 0.0
    area_b = 0.0
    arrivals = 0
    departures = 0
    w_sum = 0.0
    w_cnt = 0
    wait_cnt = 0
    started = 0
    while t < H:
        t_e = t_arr if t_arr < t_dep else t_dep
        lo = max(t, warm)
        if t_e > lo:
            seg = t_e - lo
            area_n += seg * (1 if busy else 0)
            area_n += seg * len(queue)
            if busy:
                area_b += seg
        t = t_e
        if t_arr <= t_dep:
            svc = rng.expovariate(1.0 / mean_svc)
            if t >= warm:
                arrivals += 1
            if not busy:
                busy = True
                if t >= warm:
                    started += 1
                t_dep = t + svc
            else:
                queue.append((t, svc))
            t_arr = t + rng.expovariate(lam)
        else:
            if t >= warm:
                departures += 1
            if t_arr > H:
                pass
            if queue:
                a, s = queue.pop(0)
                if a >= warm:
                    w_sum += t - a
                    w_cnt += 1
                    started += 1
                t_dep = t + s
            else:
                busy = False
                t_dep = math.inf
    win = H - warm
    L = area_n / win
    W = w_sum / w_cnt if w_cnt else 0.0
    bf = area_b / win
    pw = wait_cnt / arrivals if arrivals else 0.0
    return {
        "L": L, "W": W, "busy_frac": bf, "p_wait": pw,
        "arr": arrivals / win * 60.0, "dep": departures / win * 60.0,
        "busy_util": bf, "busy_occupied": bf,
        "blk": 0.0, "p_loss": 0.0, "dep_rate": departures / win * 60.0,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=200000)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds)
    H = float(a.horizon)
    lam = 8.0
    mean_svc = 6.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mean_svc /= 1.1
    elif a.pert == "c_up":
        mean_svc /= 1.2
    seed_list = list(range(a.seed_start, a.seed_start + n_seeds))
    warm = 0.25 * H
    per = []
    for s in seed_list:
        per.append(simulate(s, lam, mean_svc, H, warm))
    win = H - warm
    k = len(per)
    out = {
        "L": sum(p["L"] for p in per) / k,
        "W": sum(p["W"] for p in per) / k,
        "busy_frac": sum(p["busy_frac"] for p in per) / k,
        "p_wait": sum(p["p_wait"] for p in per) / k,
        "busy_util": sum(p["busy_util"] for p in per) / k,
        "busy_occupied": sum(p["busy_occupied"] for p in per) / k,
        "arr": sum(p["arr"] for p in per) / k,
        "dep": sum(p["dep"] for p in per) / k,
        "blk": 0.0,
        "p_loss": 0.0,
        "dep_rate": sum(p["dep_rate"] for p in per) / k,
        "lam_eff": sum(p["dep_rate"] for p in per) / k,
        "runtime_units": win,
        "seed_list": seed_list,
        "seeds_used": k,
        "time_unit": "minute",
        "win": win,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy_frac"] for p in per],
        "per_seed_p_loss": [p["p_loss"] for p in per],
        "per_seed_p_wait": [p["p_wait"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
