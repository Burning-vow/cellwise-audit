import argparse, heapq, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c, K = 8.0, 10.0, 3, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    H = float(a.horizon)
    warm = 0.25 * H
    T = H - warm
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    S_L = S_W = S_bf = S_pl = S_pw = 0.0
    S_arr = S_blk = S_dep = S_bu = 0.0
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed * 2654435761 % (2**31) + 12345)
        t = 0.0
        n = 0
        heap = []
        ta = rng.expovariate(lam)
        aN = aM = aP = a0 = 0.0
        entered = blocked = departed = waited = 0
        while t < H:
            td = heap[0] if heap else math.inf
            tn = min(ta, td, H)
            dt = tn - t
            lo, hi = max(t, warm), min(tn, H)
            if hi > lo:
                d = hi - lo
                aN += d * n
                aM += d * min(n, c)
                a0 += d * (1 if n > 0 else 0)
                aP += d * (1 if n >= c else 0)
            t = tn
            if t >= H:
                break
            if ta <= td:
                if n < K:
                    if n >= c:
                        waited += 1
                    s = rng.expovariate(mu)
                    heapq.heappush(heap, t + s)
                    n += 1
                    entered += 1
                else:
                    blocked += 1
                ta = t + rng.expovariate(lam)
            else:
                heapq.heappop(heap)
                n -= 1
                departed += 1
        lam_eff = entered / T
        L = aN / T
        W = (L / lam_eff) * 60.0 if lam_eff > 0 else 0.0
        bf = a0 / T
        bu = aM / T / c
        pl = blocked / (entered + blocked) if (entered + blocked) > 0 else 0.0
        pw = waited / entered if entered > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        S_L += L; S_W += W; S_bf += bf; S_pl += pl; S_pw += pw
        S_arr += entered + blocked; S_blk += blocked
        S_dep += departed; S_bu += bu
    m = a.seeds
    arr = S_arr / m
    blk = S_blk / m
    dep = S_dep / m
    out = {
        "L": S_L / m,
        "W": S_W / m,
        "busy_frac": S_bf / m,
        "p_loss": S_pl / m,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": m,
        "time_unit": "hour",
        "win": T,
        "arr": arr,
        "blk": blk,
        "busy_util": S_bu / m,
        "busy_occupied": S_bf / m,
        "dep": dep,
        "dep_rate": dep / T,
        "lam_eff": arr / T,
        "p_wait": S_pw / m,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
