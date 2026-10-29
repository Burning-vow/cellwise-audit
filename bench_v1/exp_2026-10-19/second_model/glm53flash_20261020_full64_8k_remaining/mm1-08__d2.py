import argparse, json, math, random

def run_seed(seed, lam, mu, H):
    rng = random.Random(seed)
    warm = 0.25 * H
    t = 0.0
    next_arr = rng.expovariate(lam)
    dep_until = None
    queue = []
    n = 0
    area_L = 0.0
    area_busy = 0.0
    wait_sum = 0.0
    n_waited = 0
    n_served = 0
    n_arr = 0
    n_dep = 0
    while True:
        t_dep = dep_until if dep_until is not None else math.inf
        t_next = min(next_arr, t_dep, H)
        seg = t_next - t
        if seg > 0 and t_next > warm:
            lo = max(t, warm)
            area_L += n * (t_next - lo)
            area_busy += min(n, 1) * (t_next - lo)
        t = t_next
        if t >= H:
            break
        if next_arr <= t_dep:
            st = rng.expovariate(mu)
            n += 1
            if t >= warm:
                n_arr += 1
            if dep_until is None:
                if t >= warm:
                    n_served += 1
                    if t > next_arr or True:
                        pass
                dep_until = t + st
            else:
                queue.append((t, st))
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t >= warm:
                n_dep += 1
            if queue:
                a, st = queue.pop(0)
                if t >= warm:
                    wait_sum += t - a
                    n_served += 1
                    if t > a:
                        n_waited += 1
                dep_until = t + st
            else:
                dep_until = None
    win = H - warm
    L = area_L / win
    busy = area_busy / win
    W = wait_sum / n_served if n_served else 0.0
    p_wait = n_waited / n_served if n_served else 0.0
    return L, W, busy, p_wait, n_arr, n_dep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 8.0, 12.0, 1
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c = 2
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [run_seed(s, lam, mu, a.horizon) for s in seeds]
    win = a.horizon - 0.25 * a.horizon
    per = list(zip(*res))
    L = sum(per[0]) / len(seeds)
    W = sum(per[1]) / len(seeds)
    busy = sum(per[2]) / len(seeds)
    arr = sum(per[4]) / len(seeds)
    dep = sum(per[5]) / len(seeds)
    p_wait = sum(per[3]) / len(seeds)
    out = {
        "L": L, "W": W, "busy_frac": busy, "p_wait": p_wait,
        "runtime_units": "minute", "seed_list": seeds, "seeds_used": len(seeds),
        "time_unit": "hour", "win": win,
        "arr": arr, "dep": dep, "blk": 0.0,
        "busy_util": busy, "busy_occupied": busy,
        "dep_rate": dep / win, "lam_eff": arr / win,
        "p_loss": 0.0,
        "per_seed_L": list(per[0]), "per_seed_W": list(per[1]),
        "per_seed_busy_frac": list(per[2]), "per_seed_p_wait": list(per[3]),
        "per_seed_p_loss": [0.0] * len(seeds),
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
