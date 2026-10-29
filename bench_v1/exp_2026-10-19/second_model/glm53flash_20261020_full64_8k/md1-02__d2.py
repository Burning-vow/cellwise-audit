import argparse, json, math, random, heapq

def run_seed(seed, horizon, lam, c, svc, warm_frac=0.25):
    rng = random.Random(seed)
    warm = warm_frac * horizon
    t = 0.0
    area_N = 0.0
    area_busy = 0.0
    n = 0
    busy = []
    queue = []
    next_arr = rng.expovariate(lam)
    win_area_int = lambda t0, t1: None
    area_N_win = 0.0
    area_busy_win = 0.0
    arr_win = 0
    dep_win = 0
    waited = 0
    served_win = 0
    sum_W = 0.0
    in_system = {}
    counter = [0]
    while t < horizon:
        next_dep = min(busy) if busy else math.inf
        tn = min(next_arr, next_dep, horizon)
        dt = tn - t
        area_N += n * dt
        area_busy += min(n, 1) * dt
        if t >= warm:
            area_N_win += n * dt
            area_busy_win += min(n, 1) * dt
        t = tn
        if t >= horizon:
            break
        if next_arr <= next_dep and next_arr <= horizon:
            cid = counter[0]; counter[0] += 1
            in_system[cid] = [t, 0.0]
            if t >= warm:
                arr_win += 1
            n += 1
            if len(busy) < c:
                in_system[cid][1] = t
                heapq.heappush(busy, t + svc)
            else:
                queue.append((cid, svc))
            next_arr = t + rng.expovariate(lam)
        else:
            heapq.heappop(busy)
            n -= 1
            if t >= warm:
                dep_win += 1
            if queue:
                cid, s = queue.pop(0)
                in_system[cid][1] = t
                heapq.heappush(busy, t + s)
            else:
                done = [k for k, v in in_system.items() if v[1] == t or True]
        while queue and len(busy) < c:
            cid, s = queue.pop(0)
            in_system[cid][1] = t
            heapq.heappush(busy, t + s)
        for k, v in list(in_system.items()):
            if v[1] > 0 and v[1] <= t and k not in ():
                pass
    return {}

def run_seed2(seed, horizon, lam, c, svc, warm_frac=0.25):
    rng = random.Random(seed)
    warm = warm_frac * horizon
    t = 0.0
    n = 0
    area_N = 0.0
    area_busy = 0.0
    busy = []
    queue = []
    arr_rec = {}
    next_arr = rng.expovariate(lam)
    arr_win = dep_win = waited = served = 0
    sum_W = 0.0
    while True:
        next_dep = min(busy) if busy else math.inf
        tn = min(next_arr, next_dep)
        if tn > horizon:
            dt = horizon - t
            area_N += n * dt
            area_busy += min(n, 1) * dt
            if t < warm:
                area_N -= n * dt * 0
            t = horizon
            break
        dt = tn - t
        area_N += n * dt
        area_busy += min(n, 1) * dt
        t = tn
        if next_arr <= next_dep:
            cid = len(arr_rec)
            arr_rec[cid] = [t, None]
            n += 1
            if len(busy) < c:
                arr_rec[cid][1] = t
                heapq.heappush(busy, t + svc)
            else:
                queue.append((cid, svc))
            next_arr = t + rng.expovariate(lam)
        else:
            heapq.heappop(busy)
            n -= 1
            if queue:
                cid, s = queue.pop(0)
                arr_rec[cid][1] = t
                heapq.heappush(busy, t + s)
            while queue and len(busy) < c:
                cid, s = queue.pop(0)
                arr_rec[cid][1] = t
                heapq.heappush(busy, t + s)
    win = horizon - warm
    for cid, (a, ds) in arr_rec.items():
        if ds is None:
            continue
        if a >= warm and a < horizon:
            served += 1
            sum_W += ds - a
            if ds - a > svc + 1e-12:
                waited += 1
    L = area_N / win if win > 0 else 0.0
    bf = area_busy / win if win > 0 else 0.0
    W = (sum_W / served) * 60.0 if served else 0.0
    Lw = area_N / win if win > 0 else 0.0
    p_wait = waited / served if served else 0.0
    return L, W, bf, p_wait, served, dep_win if dep_win else served

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, c, svc = 4.0, 1, 5.0 / 60.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": svc /= 1.1
    elif a.pert == "c_up": c = 2
    per_L, per_W, per_bf, per_pw = [], [], [], []
    seeds_used, seed_list = 0, []
    tot_arr = tot_dep = 0
    for i in range(a.seeds):
        s = a.seed_start + i
        L, W, bf, pw, arr, dep = run_seed2(s, a.horizon, lam, c, svc)
        per_L.append(L); per_W.append(W); per_bf.append(bf); per_pw.append(pw)
        seed_list.append(s); seeds_used += 1
        tot_arr += arr; tot_dep += dep
    n = seeds_used
    out = {
        "L": sum(per_L) / n, "W": sum(per_W) / n,
        "busy_frac": sum(per_bf) / n,
        "runtime_units": a.horizon * n, "seed_list": seed_list,
        "seeds_used": n, "time_unit": "hour",
        "win": a.horizon * 0.75,
        "arr": tot_arr / n, "blk": 0.0,
        "busy_util": sum(per_bf) / n,
        "busy_occupied": sum(per_bf) / n,
        "dep": tot_dep / n,
        "dep_rate": (tot_dep / n) / (a.horizon * 0.75),
        "lam_eff": (tot_dep / n) / (a.horizon * 0.75),
        "p_loss": 0.0,
        "p_wait": sum(per_pw) / n,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": [0.0] * n,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
