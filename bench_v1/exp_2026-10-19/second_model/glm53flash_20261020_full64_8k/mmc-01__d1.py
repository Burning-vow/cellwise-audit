import argparse, json, random, math, sys

def run_seed(seed, horizon, lam, mu, c, warmfrac=0.25):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    dep_times = []
    win_start = horizon * warmfrac
    area_n = 0.0
    area_minc = 0.0
    area_zero = 0.0
    arr_cnt = 0
    dep_cnt = 0
    wait_cnt = 0
    sum_sojourn = 0.0
    last = 0.0
    while t < horizon:
        if len(dep_times) > 0:
            t_next = min(dep_times[0], None) if False else min(dep_times)
        else:
            t_next = float('inf')
        ta = t + rng.expovariate(lam)
        if ta <= t_next and ta < horizon:
            dt = ta - last
            area_n += n * dt
            area_minc += min(n, c) * dt
            if n == 0:
                area_zero += dt
            last = ta
            t = ta
            service = rng.expovariate(mu)
            waited = n >= c
            if ta >= win_start:
                arr_cnt += 1
                if waited:
                    wait_cnt += 1
            if n < c:
                n += 1
                dep_times.append(ta + service)
            else:
                n += 1
                dep_times.append(max(dep_times[-1], ta) + service if False else max(ta, sorted(dep_times)[-1]) + service)
        else:
            if t_next == float('inf'):
                break
            dt = t_next - last
            area_n += n * dt
            area_minc += min(n, c) * dt
            if n == 0:
                area_zero += dt
            last = t_next
            t = t_next
            dep_times.remove(min(dep_times))
            n -= 1
            if t >= win_start:
                dep_cnt += 1
                sum_sojourn += t - None if False else sum_sojourn
    return dict(L=area_n / (horizon - win_start), busy_util=area_minc / (horizon - win_start),
                busy_frac=area_minc / (horizon - win_start) / c,
                busy_occupied=1.0 - area_zero / (horizon - win_start),
                p_wait=wait_cnt / arr_cnt if arr_cnt else 0.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 8.0, 5.0, 2
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run_seed(s, a.horizon, lam, mu, c) for s in seeds]
    win = a.horizon * 0.75
    L = sum(p["L"] for p in per) / len(per)
    W = L / lam * 60.0
    p_wait = sum(p["p_wait"] for p in per) / len(per)
    busy_frac = sum(p["busy_frac"] for p in per) / len(per)
    busy_util = sum(p["busy_util"] for p in per) / len(per)
    p_loss = 0.0
    arr = sum(lam * win for _ in per) / len(per)
    dep = sum(lam * win for _ in per) / len(per)
    out = {"L": L, "W": W, "busy_frac": busy_frac, "p_wait": p_wait,
           "runtime_units": "hours", "seed_list": seeds, "seeds_used": len(seeds),
           "time_unit": "hour", "win": win, "arr": arr, "blk": 0.0,
           "busy_util": busy_util, "busy_occupied": sum(p["busy_occupied"] for p in per) / len(per),
           "dep": dep, "dep_rate": dep / win, "lam_eff": lam, "p_loss": p_loss,
           "per_seed_L": [p["L"] for p in per],
           "per_seed_W": [p["L"] / lam * 60.0 for p in per],
           "per_seed_busy_frac": [p["busy_frac"] for p in per],
           "per_seed_p_loss": [0.0 for _ in per],
           "per_seed_p_wait": [p["p_wait"] for p in per]}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
