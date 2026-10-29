import argparse, json, random, heapq

def run_seed(seed, lam, mu1, mu2, horizon):
    rng = random.Random(seed)
    warm = horizon * 0.25
    ev = []
    first = rng.expovariate(lam)
    heapq.heappush(ev, (first, 0, None))
    q1, q2 = [], []
    b1 = b2 = False
    t = 0.0
    area = 0.0
    bt1 = 0.0
    bt2 = 0.0
    last_t = 0.0
    arr_c = dep_c = 0
    wsum = 0.0
    wcnt = 0
    waited = 0
    ac = wc = dpt = wtc = 0
    s_area = s_b1 = s_b2 = 0.0

    def n_now():
        return len(q1) + len(q2) + (1 if b1 else 0) + (1 if b2 else 0)

    def adv(tt):
        nonlocal area, bt1, bt2, last_t
        area += n_now() * (tt - last_t)
        bt1 += (1 if b1 else 0) * (tt - last_t)
        bt2 += (1 if b2 else 0) * (tt - last_t)
        last_t = tt

    def start1(tt):
        nonlocal b1
        if not b1 and q1:
            j = q1.pop(0)
            j[4] = tt - j[0] + j[4]
            b1 = True
            heapq.heappush(ev, (tt + j[2], 1, j))

    def start2(tt):
        nonlocal b2
        if not b2 and q2:
            j = q2.pop(0)
            j[4] = tt - j[0] + j[4]
            b2 = True
            heapq.heappush(ev, (tt + j[3], 2, j))

    while ev:
        tt, typ, j = heapq.heappop(ev)
        if tt > horizon:
            break
        adv(tt)
        t = tt
        if typ == 0:
            job = [t, None, rng.expovariate(mu1), rng.expovariate(mu2), 0.0, False]
            if t >= warm:
                arr_c += 1
            heapq.heappush(ev, (t + rng.expovariate(lam), 0, None))
            q1.append(job)
            start1(t)
        elif typ == 1:
            b1 = False
            j[1] = t
            if q1:
                j[5] = True
            q2.append(j)
            start2(t)
            start1(t)
        else:
            b2 = False
            if q2:
                j[5] = True
            if j[0] >= warm:
                dep_c += 1
                wsum += t - j[0]
                wcnt += 1
                if j[5]:
                    waited += 1
            start2(t)
        if last_t >= warm and s_area == 0.0 and wc + arr_c >= 0 and last_t > warm:
            pass
    # snapshot method: rerun integration split
    return None

def sim(seed, lam, mu1, mu2, horizon):
    rng = random.Random(seed)
    warm = horizon * 0.25
    ev = []
    heapq.heappush(ev, (rng.expovariate(lam), 0, None))
    q1, q2 = [], []
    st = {"b1": False, "b2": False}
    acc = {"area": 0.0, "bt1": 0.0, "bt2": 0.0, "last": 0.0, "arr": 0, "dep": 0,
           "wsum": 0.0, "wcnt": 0, "waited": 0,
           "s_area": None, "s_b1": None, "s_b2": None, "s_arr": None, "s_dep": None,
           "s_ws": None, "s_wc": None, "s_wt": None}

    def nn():
        return len(q1) + len(q2) + (1 if st["b1"] else 0) + (1 if st["b2"] else 0)

    def adv(tt):
        if acc["s_area"] is None and tt >= warm:
            acc["s_area"] = acc["area"]
            acc["s_b1"] = acc["bt1"]
            acc["s_b2"] = acc["bt2"]
            acc["s_arr"] = acc["arr"]
            acc["s_dep"] = acc["dep"]
            acc["s_ws"] = acc["wsum"]
            acc["s_wc"] = acc["wcnt"]
            acc["s_wt"] = acc["waited"]
        acc["area"] += nn() * (tt - acc["last"])
        acc["bt1"] += (1 if st["b1"] else 0) * (tt - acc["last"])
        acc["bt2"] += (1 if st["b2"] else 0) * (tt - acc["last"])
        acc["last"] = tt

    def start1(tt):
        if not st["b1"] and q1:
            j = q1.pop(0)
            j[5] = j[5] or (len(q1) > 0)
            st["b1"] = True
            heapq.heappush(ev, (tt + j[1], 1, j))

    def start2(tt):
        if not st["b2"] and q2:
            j = q2.pop(0)
            st["b2"] = True
            heapq.heappush(ev, (tt + j[2], 2, j))

    while ev:
        tt, typ, j = heapq.heappop(ev)
        if tt > horizon:
            break
        adv(tt)
        if typ == 0:
            job = [tt, rng.expovariate(mu1), rng.expovariate(mu2), False]
            if tt >= warm:
                acc["arr"] += 1
            heapq.heappush(ev, (tt + rng.expovariate(lam), 0, None))
            if len(q1) > 0 or st["b1"]:
                job[3] = True
            q1.append(job)
            start1(tt)
        elif typ == 1:
            st["b1"] = False
            j2 = [tt, j[2], 0.0, False]
            if len(q2) > 0 or st["b2"]:
                j2[3] = True
            q2.append(j2)
            start2(tt)
            start1(tt)
        else:
            st["b2"] = False
            if tt >= warm:
                acc["dep"] += 1
                acc["wsum"] += tt - j[0]
                acc["wcnt"] += 1
                if j[3]:
                    acc["waited"] += 1
            start2(tt)
    if acc["s_area"] is None:
        acc["s_area"] = acc["area"]; acc["s_b1"] = acc["bt1"]; acc["s_b2"] = acc["bt2"]
        acc["s_arr"] = acc["arr"]; acc["s_dep"] = acc["dep"]
        acc["s_ws"] = acc["wsum"]; acc["s_wc"] = acc["wcnt"]; acc["s_wt"] = acc["waited"]
    win = horizon - warm
    W = (acc["wsum"] - acc["s_ws"]) / max(acc["wcnt"] - acc["s_wc"], 1) * 60.0
    L = (acc["area"] - acc["s_area"]) / win
    return {
        "L": L, "W": W,
        "arr": acc["arr"] - acc["s_arr"],
        "dep": acc["dep"] - acc["s_dep"],
        "blk": 0.0,
        "busy_frac": ((acc["bt1"] - acc["s_b1"]) + (acc["bt2"] - acc["s_b2"])) / (2.0 * win),
        "p_loss": 0.0,
        "p_wait": (acc["waited"] - acc["s_wt"]) / max(acc["arr"] - acc["s_arr"], 1),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=lambda s: float(s), default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 8.0, 12.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up":
        mu1 *= 1.1; mu2 *= 1.1
    res = []
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    for s in seeds:
        res.append(sim(s, lam, mu1, mu2, a.horizon))
    n = len(res)
    win = a.horizon - a.horizon * 0.25
    out = {
        "L": sum(r["L"] for r in res) / n,
        "W": sum(r["W"] for r in res) / n,
        "runtime_units": a.horizon,
        "seed_list": seeds,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win,
        "arr": sum(r["arr"] for r in res) / n,
        "blk": sum(r["blk"] for r in res) / n,
        "busy_frac": sum(r["busy_frac"] for r in res) / n,
        "busy_util": sum(r["busy_frac"] for r in res) / n,
        "dep": sum(r["dep"] for r in res) / n,
        "dep_rate": sum(r["dep"] for r in res) / n / win,
        "lam_eff": sum(r["dep"] for r in res) / n / win,
        "p_loss": 0.0,
        "p_wait": sum(r["p_wait"] for r in res) / n,
        "per_seed_L": [r["L"] for r in res],
        "per_seed_W": [r["W"] for r in res],
        "per_seed_busy_frac": [r["busy_frac"] for r in res],
        "per_seed_p_loss": [r["p_loss"] for r in res],
        "per_seed_p_wait": [r["p_wait"] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
