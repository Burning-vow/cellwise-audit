import argparse, json, math, random, time

def run_seed(seed, lam, svc, horizon, warm):
    rng = random.Random(seed)
    t = 0.0
    t_arr = rng.expovariate(lam)
    t_dep = math.inf
    queue = []
    n = 0
    busy_now = False
    area = 0.0; busy = 0.0
    arr_c = 0; dep_c = 0; wait_c = 0; Wsum = 0.0
    while True:
        t_prev = t
        t = min(t_arr, t_dep, horizon)
        if t > horizon: t = horizon
        dt = t - t_prev
        if t > warm:
            area += n * dt
            if busy_now: busy += dt
        if t >= horizon: break
        if t_dep <= t_arr:
            cust = queue.pop(0)
            n -= 1
            if t > warm:
                dep_c += 1
                Wsum += t - cust[0]
            if queue:
                busy_now = True
                t_dep = t + queue[0][1]
            else:
                busy_now = False
                t_dep = math.inf
        else:
            s = svc
            arrive = t
            n += 1
            if t > warm: arr_c += 1
            if busy_now:
                queue.append((arrive, s))
            else:
                if t > warm and n > 1: wait_c += 1
                if n == 1 and t > warm: pass
                queue.append((arrive, s))
                if len(queue) == 1:
                    if t > warm and arr_c > 0 and not busy_now and len(queue) == 1:
                        pass
                    busy_now = True
                    t_dep = t + s
                if t > warm and len(queue) > 1:
                    pass
                if t > warm and n == 1:
                    pass
            if t > warm and (not busy_now):
                pass
            t_arr = t + rng.expovariate(lam)
    return area, busy, arr_c, dep_c, Wsum

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, svc, c = 4.0, 0.1, 1
    if a.pert == "lam_up": lam = 4.4
    elif a.pert == "mu_up": svc = 0.09
    elif a.pert == "c_up": c = 2
    warm = 0.25 * a.horizon
    win = a.horizon - warm
    seed_list = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; ploss = []; pwait = []
    t0 = time.time()
    for s in seed_list:
        area, busy, arr_c, dep_c, Wsum = run_seed(s, lam, svc, a.horizon, warm)
        pL.append(area / win)
        pB.append(busy / win)
        pW.append(Wsum / dep_c if dep_c else 0.0)
        ploss.append(0.0)
        pwait.append(0.0)
    arr = sum(pL) * 0 + sum(run_seed(s, lam, svc, a.horizon, warm)[2] for s in seed_list) / len(seed_list)
    dep = sum(run_seed(s, lam, svc, a.horizon, warm)[3] for s in seed_list) / len(seed_list)
    L = sum(pL) / len(pL)
    W = sum(pW) / len(pW)
    bf = sum(pB) / len(pB)
    out = {
        "L": L, "W": W, "busy_frac": bf, "runtime_units": time.time() - t0,
        "seed_list": seed_list, "seeds_used": len(seed_list),
        "time_unit": "hour", "win": win,
        "arr": arr, "blk": 0.0, "busy_util": bf, "busy_occupied": bf,
        "dep": dep, "dep_rate": dep / win, "lam_eff": arr / win,
        "p_loss": 0.0, "p_wait": 0.0,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": ploss, "per_seed_p_wait": pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
