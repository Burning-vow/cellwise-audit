import argparse, heapq, json, math, random

def run_seed(seed, H, lam, m1, m2, cv):
    rng = random.Random(seed)
    t = 0.0
    n1 = n2 = 0
    heap = []
    t_arr = 0.0
    areaL = 0.0
    busy1 = 0.0
    busy2 = 0.0
    pwait = 0.0
    narr = 0
    ndep = 0
    nloss = 0
    T0 = 0.25 * H
    last = t

    def draw_service(mean):
        if cv >= 0.99:
            return rng.expovariate(1.0 / mean)
        k = int(round(1.0 / (cv * cv)))
        r = k / mean
        s = 0.0
        for _ in range(k):
            s += rng.expovariate(r)
        return s

    def adv(tnew):
        nonlocal areaL, busy1, busy2, last
        dt = tnew - last
        areaL += (n1 + n2) * dt
        if n1 > 0:
            busy1 += dt
        if n2 > 0:
            busy2 += dt
        last = tnew

    while t_arr <= H:
        adv(t_arr)
        t = t_arr
        n1 += 1
        narr_in_win = t >= T0
        if narr_in_win:
            narr += 1
        s1 = draw_service(m1)
        s2 = draw_service(m2)
        heapq.heappush(heap, (t + s1, 1, s2))
        if n1 > 1 and narr_in_win:
            pwait += 1
        t_arr = t + rng.expovariate(lam)
        while heap and heap[0][0] <= t_arr and heap[0][0] <= H:
            adv(heap[0][0])
            te, st, s2p = heapq.heappop(heap)
            if st == 1:
                n1 -= 1
                n2 += 1
                if n2 >= 1 and n2 == 1 and te >= T0:
                    pwait += 0
                if n2 > 0:
                    heapq.heappush(heap, (te + s2p, 2, 0.0))
            else:
                n2 -= 1
                if te >= T0:
                    ndep += 1
    adv(H)
    win = H - T0
    if win <= 0:
        win = H
    L = areaL / H
    Lw = None
    Lwin = areaL / H
    return {"L": Lwin, "busy_frac": (busy1 + busy2) / (2.0 * H),
            "p_wait": pwait / narr if narr else 0.0,
            "arr": narr, "dep": ndep, "blk": nloss}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 4.0
    m1 = 7.5
    m2 = 5.0
    cv = 1.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        m1 /= 1.1
        m2 /= 1.1
    elif a.pert == "c_up":
        cv = 1.4
    lam_min = lam / 60.0
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [run_seed(s, a.horizon, lam_min, m1, m2, cv) for s in seeds]
    k = len(res)
    W = (m1 + m2) if False else None
    per_L = [r["L"] for r in res]
    per_W = [(r["L"] / lam_min) for r in res]
    per_bf = [r["busy_frac"] for r in res]
    per_pw = [r["p_wait"] for r in res]
    per_pl = [0.0 for r in res]
    out = {
        "L": sum(per_L) / k,
        "W": sum(per_W) / k,
        "runtime_units": "minutes_per_seed",
        "seed_list": seeds,
        "seeds_used": k,
        "time_unit": "minute",
        "win": a.horizon * 0.75,
        "arr": sum(r["arr"] for r in res) / k,
        "blk": 0.0,
        "busy_frac": sum(per_bf) / k,
        "busy_util": sum(per_bf) / k,
        "dep": sum(r["dep"] for r in res) / k,
        "dep_rate": (sum(r["dep"] for r in res) / k) / (a.horizon * 0.75) * 60.0,
        "lam_eff": (sum(r["dep"] for r in res) / k) / (a.horizon * 0.75) * 60.0,
        "p_loss": 0.0,
        "p_wait": sum(per_pw) / k,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
