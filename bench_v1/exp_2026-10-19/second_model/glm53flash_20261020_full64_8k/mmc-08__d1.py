import argparse, heapq, json, math, random, sys

def run_seed(seed, H, lam, mu, c, warm):
    rng = random.Random(seed)
    t = 0.0
    nbusy = 0
    q = []
    depq = []
    seq = 0
    area = 0.0
    area_busy = 0.0
    area_occ = 0.0
    last = 0.0
    arrive_in = 0
    arrive_q = 0
    soj = []
    n_dep = 0
    n_arr_cnt = 0
    n_blk = 0
    def adv(t2):
        nonlocal area, area_busy, area_occ, last
        if t2 > last:
            if t2 > warm:
                a = max(last, warm)
                dt = t2 - a
                area += t2 and dt * n
                area += dt * nbusy
                area_busy += dt * nbusy
                area_occ += dt * (1 if nbusy > 0 else 0)
                area -= dt * nbusy
            last = t2
    n = 0
    def adv2(t2):
        nonlocal area, area_busy, area_occ, last
        if t2 > last:
            a = max(last, warm)
            if t2 > a:
                dt = t2 - a
                area += dt * nbusy
                area_busy += dt * nbusy
                area_occ += dt * (1.0 if nbusy > 0 else 0.0)
            last = t2
    t_arr = rng.expovariate(lam)
    while t_arr < H or depq:
        if depq and (t_arr >= H or depq[0][0] <= t_arr):
            td, _ = heapq.heappop(depq)
            adv2(td)
            nbusy -= 1
            n = nbusy
            if q:
                ts, s = q.pop(0)
                heapq.heappush(depq, (td + s, seq))
                nbusy += 1
        else:
            adv2(t_arr)
            t = t_arr
            n_arr_cnt += 1
            if t >= warm:
                arrive_in += 1
                if nbusy == c:
                    arrive_q += 1
            s = rng.expovariate(mu)
            if nbusy < c:
                heapq.heappush(depq, (t + s, seq))
                nbusy += 1
            else:
                q.append((t, s))
            if t_arr < H:
                t_arr += rng.expovariate(lam)
            else:
                t_arr = math.inf
    dur = H - warm
    if dur <= 0:
        return dict(L=0.0, W=0.0, busy_frac=0.0, busy_util=0.0, busy_occupied=0.0,
                    p_wait=0.0, arr=0.0, dep=0.0, blk=0.0, dep_rate=0.0)
    L = area / dur
    bf = area_busy / c / dur
    occ = area_occ / dur
    pw = arrive_q / arrive_in if arrive_in > 0 else 0.0
    W = sum(soj) / len(soj) if soj else 0.0
    return dict(L=L, W=W, busy_frac=bf, busy_util=bf, busy_occupied=occ,
                p_wait=pw, arr=n_arr_cnt / dur, dep=n_dep / dur, blk=n_blk / dur,
                dep_rate=n_dep / dur)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    N = int(a.seeds)
    H = float(a.horizon)
    S = int(a.seed_start)
    c = 3
    lam, mu = 8.0, 6.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c += 1
    warm = 0.25 * H
    seeds = list(range(S, S + N))
    per = [run_seed(sd, H, lam, mu, c, warm) for sd in seeds]
    K = len(per)
    out = {
        "L": sum(p["L"] for p in per) / K,
        "W": sum(p["W"] for p in per) / K,
        "busy_frac": sum(p["busy_frac"] for p in per) / K,
        "p_wait": sum(p["p_wait"] for p in per) / K,
        "busy_util": sum(p["busy_util"] for p in per) / K,
        "busy_occupied": sum(p["busy_occupied"] for p in per) / K,
        "arr": sum(p["arr"] for p in per) / K,
        "dep": sum(p["dep"] for p in per) / K,
        "blk": sum(p["blk"] for p in per) / K,
        "dep_rate": sum(p["dep_rate"] for p in per) / K,
        "lam_eff": sum(p["dep_rate"] for p in per) / K,
        "p_loss": sum(p["blk"] for p in per) / K / max(sum(p["arr"] for p in per) / K, 1e-12),
        "runtime_units": K,
        "seed_list": seeds,
        "seeds_used": K,
        "time_unit": "hour",
        "win": H - warm,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy_frac"] for p in per],
        "per_seed_p_loss": [p["blk"] for p in per],
        "per_seed_p_wait": [p["p_wait"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
