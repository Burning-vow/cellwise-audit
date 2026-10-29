import argparse, json, math, random, sys

def hyperexp_params(mean, cv):
    cv2 = cv * cv
    p1 = 0.5 * (1.0 + math.sqrt((cv2 - 1.0) / (cv2 + 1.0)))
    p2 = 1.0 - p1
    m1 = 2.0 * p1 * mean
    m2 = 2.0 * p2 * mean
    return p1, 1.0 / m1, p2, 1.0 / m2

def run_seed(seed, lam, svc_mean, svc_cv, c, horizon, warm):
    rng = random.Random(seed)
    p1, r1, p2, r2 = hyperexp_params(svc_mean, svc_cv)
    def draw_svc():
        if rng.random() < p1:
            return rng.expovariate(r1)
        return rng.expovariate(r2)
    t = 0.0
    busy = [None] * c
    queue = []
    nxt_arr = rng.expovariate(lam)
    area_N = 0.0
    area_busy = 0.0
    arrivals = 0
    waits = 0
    departs = 0
    lost = 0
    sum_wait = 0.0
    last = t
    while True:
        ev_t = nxt_arr
        for i, b in enumerate(busy):
            if b is not None and b[0] < ev_t:
                ev_t = b[0]
        if ev_t > horizon:
            break
        area_N += (ev_t - last) * (len(queue) + sum(1 for b in busy if b is not None))
        area_busy += (ev_t - last) * sum(1 for b in busy if b is not None)
        last = ev_t
        in_win = ev_t >= warm
        if nxt_arr <= ev_t:
            t = nxt_arr
            arrivals += in_win
            st = draw_svc()
            idle = None
            for i, b in enumerate(busy):
                if b is None:
                    idle = i
                    break
            if idle is not None:
                if in_win:
                    waits += 1
                busy[idle] = (t + st, st)
            else:
                queue.append((t, st))
                if in_win:
                    waits += 1
            nxt_arr = t + rng.expovariate(lam)
        else:
            done_i = None
            for i, b in enumerate(busy):
                if b is not None and b[0] == ev_t:
                    done_i = i
                    break
            t = ev_t
            departs += in_win
            if queue:
                a, st = queue.pop(0)
                if in_win:
                    sum_wait += t - a
                busy[done_i] = (t + st, st)
            else:
                busy[done_i] = None
    area_N += (horizon - last) * (len(queue) + sum(1 for b in busy if b is not None))
    area_busy += (horizon - last) * sum(1 for b in busy if b is not None)
    win = horizon - warm
    L = area_N / win
    busy_frac = area_busy / win
    lam_eff = arrivals / win
    W_min = (L / lam_eff * 60.0) if lam_eff > 0 else 0.0
    p_wait = waits / arrivals if arrivals > 0 else 0.0
    return dict(L=L, W=W_min, busy_frac=busy_frac, arr=arrivals, dep=departs,
                blk=lost, p_loss=lost / arrivals if arrivals else 0.0,
                p_wait=p_wait, busy_util=busy_frac, busy_occupied=busy_frac)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu_mean, cv, c = 3.0, 0.1, 1.5, 1
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu_mean /= 1.1
    elif a.pert == "c_up":
        c = 2
    warm = 0.25 * a.horizon
    res = [run_seed(s, lam, mu_mean, cv, c, a.horizon, warm) for s in range(a.seed_start, a.seed_start + a.seeds)]
    n = len(res)
    avg = lambda k: sum(r[k] for r in res) / n
    out = {
        "L": avg("L"), "W": avg("W"), "busy_frac": avg("busy_frac"),
        "runtime_units": "hour", "time_unit": "hour", "win": a.horizon - warm,
        "seed_list": list(range(a.seed_start, a.seed_start + n)),
        "seeds_used": n,
        "arr": avg("arr"), "dep": avg("dep"), "blk": avg("blk"),
        "dep_rate": avg("dep") / (a.horizon - warm),
        "lam_eff": avg("arr") / (a.horizon - warm),
        "p_loss": avg("p_loss"), "p_wait": avg("p_wait"),
        "busy_util": avg("busy_util"), "busy_occupied": avg("busy_occupied"),
        "per_seed_L": [r["L"] for r in res],
        "per_seed_W": [r["W"] for r in res],
        "per_seed_busy_frac": [r["busy_frac"] for r in res],
        "per_seed_p_loss": [r["p_loss"] for r in res],
        "per_seed_p_wait": [r["p_wait"] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
