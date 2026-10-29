import argparse, json, random, math

def run_seed(seed, lam, mu, K, H):
    rng = random.Random(seed)
    warm = 0.25 * H
    t = 0.0
    na = rng.expovariate(lam)
    nd = math.inf
    cur_at = None
    q = []
    area_win = 0.0
    busy_win = 0.0
    last = 0.0
    arr = blk = dep = waited = 0
    sumW = 0.0

    def adv(newt):
        nonlocal last, area_win, busy_win
        lo, hi = max(last, warm), min(newt, H)
        n = (1 + len(q)) if cur_at is not None else 0
        if hi > lo:
            area_win += n * (hi - lo)
            if n > 0:
                busy_win += hi - lo
        last = newt

    while min(na, nd) < H:
        if na <= nd:
            t = na
            adv(t)
            na = t + rng.expovariate(lam)
            n = (1 + len(q)) if cur_at is not None else 0
            if n == K:
                if t >= warm:
                    blk += 1
            else:
                st = rng.expovariate(mu)
                if t >= warm:
                    arr += 1
                    if n >= 1:
                        waited += 1
                if n == 0:
                    cur_at = t
                    nd = t + st
                else:
                    q.append((t, st))
        else:
            t = nd
            adv(t)
            if t >= warm:
                dep += 1
                sumW += t - cur_at
            if q:
                a, st = q.pop(0)
                cur_at = a
                nd = t + st
            else:
                cur_at = None
                nd = math.inf
    adv(H)
    win = H - warm
    L = area_win / win
    busy_frac = busy_win / win
    served = arr - blk
    acc = arr
    W = (sumW / dep) if dep > 0 else 0.0
    p_loss = (blk / acc) if acc > 0 else 0.0
    p_wait = (waited / acc) if acc > 0 else 0.0
    dep_rate = dep / win
    return dict(L=L, W=W, busy_frac=busy_frac, p_loss=p_loss,
                p_wait=p_wait, arr=arr, blk=blk, dep=dep, dep_rate=dep_rate)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=lambda x: float(x), default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, K = 8.0, 12.0, 4
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        K += 1
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run_seed(s, lam, mu, K, a.horizon) for s in seed_list]
    n = len(per)
    win = a.horizon * 0.75
    out = {
        "L": sum(p["L"] for p in per) / n,
        "W": sum(p["W"] for p in per) / n,
        "busy_frac": sum(p["busy_frac"] for p in per) / n,
        "p_loss": sum(p["p_loss"] for p in per) / n,
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win,
        "arr": sum(p["arr"] for p in per) / n,
        "blk": sum(p["blk"] for p in per) / n,
        "busy_util": sum(p["busy_frac"] for p in per) / n,
        "busy_occupied": sum(p["busy_frac"] for p in per) / n,
        "dep": sum(p["dep"] for p in per) / n,
        "dep_rate": sum(p["dep_rate"] for p in per) / n,
        "lam_eff": sum(p["dep_rate"] for p in per) / n,
        "p_wait": sum(p["p_wait"] for p in per) / n,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [p["W"] for p in per],
        "per_seed_busy_frac": [p["busy_frac"] for p in per],
        "per_seed_p_loss": [p["p_loss"] for p in per],
        "per_seed_p_wait": [p["p_wait"] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
