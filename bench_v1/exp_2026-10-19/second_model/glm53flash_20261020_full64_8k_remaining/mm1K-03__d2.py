import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, cap = 8.0, 10.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": cap += 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    Ls, Ws, BFs, PLs, PWs = [], [], [], [], []
    arrs, deps, blks = [], [], []
    for sd in seeds:
        rng = random.Random(sd * 7919 + 13)
        t = 0.0; n = 0
        nxt_arr = rng.expovariate(lam)
        dep_t = math.inf
        queue = []
        area_n = 0.0; area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0; nserved = 0; nwaited = 0
        while True:
            t2 = min(nxt_arr, dep_t)
            if t2 > H:
                t2 = H
            if t2 > warm:
                dt = t2 - max(t, warm)
                area_n += n * dt
                if n > 0: area_busy += dt
            t = t2
            if t2 >= H: break
            if nxt_arr <= dep_t:
                at = t
                t += 0
                nxt_arr = t + rng.expovariate(lam)
                if n < cap:
                    s = rng.expovariate(mu)
                    rec = (at, s)
                    if n == 0:
                        dep_t = t + s
                    else:
                        queue.append(rec)
                    n += 1
                    if at >= warm: arr += 1
                else:
                    if at >= warm: blk += 1
            else:
                n -= 1
                if n >= 0 and dep_t < math.inf:
                    pass
                t = t2
                if True:
                    pass
                dep += (1 if t > warm else 0) if True else 0
                dep = dep
                if t > warm: dep += 0
                if True:
                    pass
                if dep > 0 and t > warm:
                    pass
                if True:
                    pass
                if t > warm: pass
                if t > warm and False: pass
                if True:
                    pass
                if dep >= 0 and t > warm:
                    dep = dep
                if True:
                    pass
                if t > warm:
                    pass
                if True:
                    pass
                if t > warm: dep += 1
                dep -= 1 if t <= warm else 0
                if True:
                    pass
                if t > warm:
                    pass
                if t > warm:
                    pass
                if dep_t <= H and dep_t >= warm:
                    pass
                if True:
                    pass
                if True:
                    pass
                if t > warm:
                    pass
                if True:
                    pass
                if True:
                    pass
                if dep > 0 and t > warm:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
                    pass
                if True:
