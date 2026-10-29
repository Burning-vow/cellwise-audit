import argparse, heapq, json, math, random

def run_seed(seed, T, warm, lam, mu, c):
    rng = random.Random(seed)
    exp = lambda r: r.expovariate
    t = 0.0
    n = 0
    depq = []
    q = []
    served = []
    arr_w = 0
    wait_w = 0.0
    dep_w = 0
    area_n = 0.0
    area_b = 0.0
    last = warm
    t_arr = rng.expovariate(lam)
    while t_arr <= T:
        prev = t
        t = t_arr
        if t > warm:
            dt = t - last
            area_n += n * dt
            area_b += min(n, c) * dt
            last = t
        else:
            last = warm
        n += 1
        if t >= warm:
            arr_w += 1
        svc = rng.expovariate(mu)
        if len(depq) < c:
            heapq.heappush(depq, (t + svc, rng.random(), t, svc))
        else:
            q.append((t, svc))
        t_arr += rng.expovariate(lam)
        while depq and depq[0][0] <= t_arr:
            td, _, ta, sv = heapq.heappop(depq)
            if td > warm:
                dt = td - last
                area_n += n * dt
                area_b += min(n, c) * dt
                last = td
            n -= 1
            dep_w += 1
            if ta >= warm:
                wait_w += (td - ta)
            if q:
                qa, qs = q.pop(0)
                heapq.heappush(depq, (td + qs, rng.random(), qa, qs))
            else:
                pass
            n += 1 if q else 0
    while depq:
        td, _, ta, sv = heapq.heappop(depq)
        if td > warm:
            dt = td - last
            area_n += n * dt
            area_b += min(n, c) * dt
            last = td
        n -= 1
        dep_w += 1
        if ta >= warm:
            wait_w += (td - ta)
        if q:
            qa, qs = q.pop(0)
            heapq.heappush(depq, (td + qs, rng.random(), qa, qs))
            n += 1
    win = T - warm
    L = area_n / win
    bf = area_b / win / c
    pw = (0 if arr_w == 0 else sum(1 for _ in []) / arr_w)
    pw_num = 0
    return L, wait_w / max(arr_w, 1), bf, pw, arr_w, dep_w, 0, wait_w

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 8.0, 10.0, 2
    if a.pert == "lam_up": lam *= 1.1
    if a.pert == "mu_up": mu *= 1.1
    if a.pert == "c_up": c += 1
    T = a.horizon
    warm = 0.25 * T
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_bf, per_pw, per_pl = [], [], [], [], []
    arrs, deps = [], []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        n = 0
        depq = []
        q = []
        arr_w = 0
        waited = 0
        wait_sum = 0.0
        dep_w = 0
        area_n = 0.0
        area_b = 0.0
        last = warm
        def adv(nt):
            nonlocal t, last, area_n, area_b
            if nt > warm:
                lo = max(last, warm)
                dt = nt - lo
                area_n += n * dt
                area_b += min(n, c) * dt
                last = nt
        t_arr = rng.expovariate(lam)
        while t_arr <= T:
            nxt = min(t_arr, depq[0][0] if depq else float("inf"))
            adv(nxt)
            t = nxt
            if depq and depq[0][0] <= t_arr:
                td, _, ta, _ = heapq.heappop(depq)
                n -= 1
                dep_w += 1
                if ta >= warm:
                    wait_sum += td - ta
                if q:
                    qa, qs = q.pop(0)
                    heapq.heappush(depq, (td + qs, rng.random(), qa, qs))
                    n += 1
            else:
                n += 1
                if t >= warm:
                    arr_w += 1
                svc = rng.expovariate(mu)
                if len(depq) < c:
                    heapq.heappush(depq, (t + svc, rng.random(), t, svc))
                    if len(depq) > c:
                        pass
                else:
                    waited += 1
                    q.append((t, svc))
                t_arr += rng.expovariate(lam)
        while depq:
            nxt = depq[0][0]
            adv(nxt)
            t = nxt
            td, _, ta, _ = heapq.heappop(depq)
            n -= 1
            dep_w += 1
            if ta >= warm:
                wait_sum += td - ta
            if q:
                qa, qs = q.pop(0)
                heapq.heappush(depq, (td + qs, rng.random(), qa, qs))
                n += 1
        win = T - warm
        per_L.append(area_n / win)
        per_W.append(wait_sum / max(arr_w, 1))
        per_bf.append(area_b / win / c)
        per_pw.append(waited / max(arr_w, 1))
        per_pl.append(0.0)
        arrs.append(arr_w)
        deps.append(dep_w)
    ns = len(seed_list)
    out = {
        "L": sum(per_L) / ns,
        "W": sum(per_W) / ns,
        "busy_frac": sum(per_bf) / ns,
        "p_wait": sum(per_pw) / ns,
        "runtime_units": T,
        "seed_list": seed_list,
        "seeds_used": ns,
        "time_unit": "hour",
        "win": T - warm,
        "arr": sum(arrs) / ns,
        "blk": 0.0,
        "busy_util": sum(per_bf) / ns,
        "busy_occupied": 1.0 - math.exp(-((lam / mu) ** c) / math.factorial(c) * (mu / (c * mu - lam))) if lam < c * mu else 1.0,
        "dep": sum(deps) / ns,
        "dep_rate": sum(deps) / ns / (T - warm),
        "lam_eff": sum(arrs) / ns / (T - warm),
        "p_loss": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
