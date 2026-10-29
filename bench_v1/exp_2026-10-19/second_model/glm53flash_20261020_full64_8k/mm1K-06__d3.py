import argparse, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=400.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    K, C = 4, 1
    lam, mu = 9.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    seeds = [a.seed_start + i for i in range(a.seeds)]
    warm = 0.25 * a.horizon
    win = a.horizon - warm
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    arrs, deps, blks = [], [], []
    tot_L, tot_bf, tot_pw, tot_W, tot_pl = 0.0, 0.0, 0.0, 0.0, 0.0
    for s in seeds:
        rng = random.Random(s)
        t, n = 0.0, 0
        at = rng.expovariate(lam)
        dep_t = math.inf
        servs, waits = [], []
        area, busy_t = 0.0, 0.0
        cnt_a, cnt_d, cnt_b = 0, 0, 0
        w_sum, w_cnt, waiters = 0.0, 0, 0
        while t < a.horizon:
            nxt = at if at < dep_t else dep_t
            if t >= warm:
                area += n * (nxt - t)
                if n > 0: busy_t += (nxt - t)
            t = nxt
            if at <= dep_t:
                if n < K:
                    st = rng.expovariate(mu)
                    waits.append(t)
                    if n == 0:
                        dep_t = t + st
                    else:
                        servs.append((t, st))
                    n += 1
                else:
                    cnt_b += 1
                at = t + rng.expovariate(lam)
            else:
                n -= 1
                cnt_d += 1
                if servs:
                    ts, st = servs.pop(0)
                    w_sum += dep_t_holder(ts, st, t)
                    w_cnt += 1
                elif waits:
                    pass
                if n > 0 and dep_t == math.inf:
                    if servs:
                        dep_t = t + servs.pop(0)[1]
                    elif waits:
                        pass
                if n == 0:
                    dep_t = math.inf
        per_L.append(area / win)
        per_bf.append(busy_t / win)
        per_pl.append(cnt_b / win / lam if cnt_b else 0.0)
        tot_L += area / win
        tot_bf += busy_t / win
    res = {
        "L": tot_L / a.seeds, "W": None, "busy_frac": tot_bf / a.seeds,
        "p_loss": None, "runtime_units": a.horizon, "seed_list": seeds,
        "seeds_used": a.seeds, "time_unit": "hour", "win": win,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(res))

def dep_t_holder(ts, st, t):
    return st

if __name__ == "__main__":
    main()
