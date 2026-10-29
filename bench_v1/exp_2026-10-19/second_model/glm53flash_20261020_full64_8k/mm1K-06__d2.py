import sys, json, math, random, argparse

def run_seed(seed, horizon, warm, lam, mu, K):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy_until = None
    arr_t = None
    next_arr = rng.expovariate(lam)
    next_dep = None
    Wt = 0.0; Narea = 0.0; Barea = 0.0
    arr = 0; dep = 0; blk = 0; waited = 0
    end = warm
    while True:
        t_next = next_arr
        ev = 'a'
        if next_dep is not None and next_dep < t_next:
            t_next = next_dep; ev = 'd'
        if t_next >= horizon:
            t_next = horizon; ev = 'end'
        if t >= warm:
            dt = t_next - t
            Narea += n * dt
            Barea += (1 if n > 0 else 0) * dt
        t = t_next
        if ev == 'end':
            break
        if ev == 'a':
            if n < K:
                n += 1
                svc = rng.expovariate(mu)
                if n == 1:
                    next_dep = t + svc
                else:
                    if busy_until is None:
                        busy_until = svc
                if t >= warm:
                    arr += 1
                    arr_t = t
                    if n > 1:
                        waited += 1
                st = (t, svc, t >= warm)
            else:
                if t >= warm:
                    blk += 1
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t >= warm:
                dep += 1
                if arr_t is not None and arr_t >= warm:
                    Wt += t - arr_t
                    arr_t = None
            if n > 0:
                next_dep = t + busy_until
                busy_until = None
            else:
                next_dep = None
    span = horizon - warm
    L = Narea / span
    busy = Barea / span
    served = dep
    W = (Wt / served * 60.0) if served > 0 else 0.0
    p_loss = blk / (arr + blk) if (arr + blk) > 0 else 0.0
    p_wait = waited / arr if arr > 0 else 0.0
    return L, W, busy, p_loss, p_wait, arr, blk, dep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=1)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, K = 9.0, 12.0, 4
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': K += 1
    warm = 0.25 * a.horizon
    res = [run_seed(s, a.horizon, warm, lam, mu, K) for s in range(a.seed_start, a.seed_start + a.seeds)]
    ns = len(res)
    L = sum(r[0] for r in res) / ns
    W = sum(r[1] for r in res) / ns
    busy = sum(r[2] for r in res) / ns
    p_loss = sum(r[3] for r in res) / ns
    p_wait = sum(r[4] for r in res) / ns
    arr = sum(r[5] for r in res) / ns
    blk = sum(r[6] for r in res) / ns
    dep = sum(r[7] for r in res) / ns
    out = {
        "L": L, "W": W, "busy_frac": busy, "p_loss": p_loss,
        "runtime_units": a.horizon, "seed_list": list(range(a.seed_start, a.seed_start + ns)),
        "seeds_used": ns, "time_unit": "hour", "win": a.horizon - warm,
        "arr": arr, "blk": blk, "busy_util": busy, "busy_occupied": busy,
        "dep": dep, "dep_rate": dep / (a.horizon - warm),
        "lam_eff": (arr + blk) / (a.horizon - warm), "p_wait": p_wait,
        "per_seed_L": [r[0] for r in res], "per_seed_W": [r[1] for r in res],
        "per_seed_busy_frac": [r[2] for r in res], "per_seed_p_loss": [r[3] for r in res],
        "per_seed_p_wait": [r[4] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
