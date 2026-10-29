import json, argparse, math, random, heapq

def hyperexp_service(rng, mean_h, cv):
    scv = cv*cv
    p1 = 0.5*(1.0 + math.sqrt((scv-1.0)/(scv+1.0)))
    m1 = 2.0*p1*mean_h
    m2 = 2.0*(1.0-p1)*mean_h
    if rng.random() < p1:
        return rng.expovariate(1.0/m1)
    return rng.expovariate(1.0/m2)

def run_seed(seed, lam, mean_h, cv, horizon):
    rng = random.Random(seed)
    t = 0.0
    next_arr = rng.expovariate(lam)
    dep_end = None
    queue = []
    warm = 0.25*horizon
    area_N = 0.0; area_busy = 0.0
    last = 0.0
    arr = 0; dep = 0; blk = 0; waited = 0
    sum_soj = 0.0; sum_wait = 0.0
    def integ(t_new):
        nonlocal area_N, area_busy, last
        a = max(last, warm); b = min(t_new, horizon)
        if b > a:
            n = (1 if dep_end is not None else 0) + len(queue)
            area_N += n*(b-a)
            if dep_end is not None:
                area_busy += (b-a)
        last = t_new
    while t < horizon:
        t_arr = next_arr
        t_dep = dep_end if dep_end is not None else float('inf')
        t_new = min(t_arr, t_dep)
        integ(t_new)
        t = t_new
        if t_arr <= t_dep:
            next_arr = t + rng.expovariate(lam)
            svc = hyperexp_service(rng, mean_h, cv)
            if t >= warm:
                arr += 1
            if dep_end is None:
                w = 0.0
                dep_end = t + svc
                if t >= warm:
                    waited += 0
                    sum_wait += 0.0
            else:
                heapq.heappush(queue, (t, svc))
        else:
            if t >= warm:
                dep += 1
            dep_end = None
            if queue:
                a0, svc = heapq.heappop(queue)
                w = t - a0
                if t >= warm:
                    waited += 1
                    sum_wait += w
                dep_end = t + svc
    if horizon > warm:
        area_N += 0.0
    win = horizon - warm
    if win <= 0 or dep == 0:
        return dict(L=0.0, W=0.0, busy_frac=0.0, arr=0, dep=0, blk=0, p_wait=0.0)
    L = area_N/win
    busy = area_busy/win
    W = (sum_soj + sum_wait)/dep if dep else 0.0
    return dict(L=L, W=W*60.0, busy_frac=busy, arr=arr, dep=dep, blk=blk,
                p_wait=waited/arr if arr else 0.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 5.0; mean_h = 6.0/60.0; cv = 3.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mean_h /= 1.1
    elif a.pert == "c_up": mean_h /= 1.1
    per = []
    seed_list = []
    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        per.append(run_seed(s, lam, mean_h, cv, a.horizon))
    n = len(per)
    win = a.horizon - 0.25*a.horizon
    arr = sum(p["arr"] for p in per)/n
    dep = sum(p["dep"] for p in per)/n
    blk = sum(p["blk"] for p in per)/n
    L = sum(p["L"] for p in per)/n
    W = sum(p["W"] for p in per)/n
    busy_frac = sum(p["busy_frac"] for p in per)/n
    p_wait = sum(p["p_wait"] for p in per)/n
    p_loss = blk/arr if arr else 0.0
    dep_rate = dep/win if win > 0 else 0.0
    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "busy_util": busy_frac, "busy_occupied": busy_frac,
        "runtime_units": a.horizon, "seed_list": seed_list,
        "seeds_used": n, "time_unit": "hour", "win": win,
        "arr": arr, "blk": blk, "dep": dep,
        "dep_rate": dep_rate, "lam_eff": dep_rate,
        "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy_frac"] for p in per],
        "per_seed_p_loss": [0.0]*n,
        "per_seed_p_wait": [p["p_wait"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
