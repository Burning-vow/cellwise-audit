import argparse, json, math, random, heapq, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=10)
    p.add_argument("--horizon", type=float, default=2000.0)
    p.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu1, mu2 = 6.0, 8.0, 12.0
    if a.pert == "lam_up": lam *= 1.2
    elif a.pert == "mu_up": mu1 *= 1.2; mu2 *= 1.2
    elif a.pert == "c_up": mu1 *= 1.2; mu2 *= 1.2
    t0 = 0.25 * H
    per = []
    seed_list = []
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        busy1 = 0.0; busy2 = 0.0
        q1 = []; q2 = []
        s1_busy = False; s2_busy = False
        last_t = 0.0; last_n = 0; area = 0.0
        arr_n = 0; dep_n = 0; blk_n = 0
        soj = []
        wait_pos = 0
        done = False
        next_arr = rng.expovariate(lam)
        ev = [(next_arr, 0, None)]
        while ev:
            tt, kind, cust = heapq.heappop(ev)
            if tt > H:
                break
            dt = tt - last_t
            if tt > t0:
                lo = max(last_t, t0)
                if tt > lo:
                    area += last_n * (tt - lo)
            if kind == 0:
                t = tt; last_t = tt
                arr_n += 1
                s1 = rng.expovariate(mu1); s2 = rng.expovariate(mu2)
                c = {"a": t, "s1": s1, "s2": s2, "wq1": 0.0}
                heapq.heappush(ev, (t + rng.expovariate(lam), 0, None))
                if s1_busy:
                    q1.append(c)
                else:
                    s1_busy = True; c["d1"] = t + s1; c["start1"] = t
                    heapq.heappush(ev, (c["d1"], 1, c))
            elif kind == 1:
                t = tt; last_t = tt
                busy1 += cust["s1"]
                cust["wq1"] = cust["start1"] - cust["a"]
                if q1:
                    nc = q1.pop(0)
                    nc["start1"] = t
                    nc["d1"] = t + nc["s1"]
                    heapq.heappush(ev, (nc["d1"], 1, nc))
                else:
                    s1_busy = False
                if s2_busy:
                    q2.append(cust)
                else:
                    s2_busy = True; cust["start2"] = t
                    heapq.heappush(ev, (t + cust["s2"], 2, cust))
            else:
                t = tt; last_t = tt
                busy2 += cust["s2"]
                dep_n += 1
                soj.append(t - cust["a"])
                if cust["wq1"] > 0 or (cust["start2"] - cust["d1"]) > 0:
                    wait_pos += 1
                if q2:
                    nc = q2.pop(0)
                    nc["start2"] = t
                    heapq.heappush(ev, (t + nc["s2"], 2, nc))
                else:
                    s2_busy = False
            last_n = 1 if s1_busy else 0
            last_n += len(q1) + 1 if s1_busy else 0
        dth = max(H - last_t, 0.0)
        if H > t0:
            lo = max(last_t, t0)
            if H > lo:
                area += last_n * (H - lo)
        win = H - t0
        if win <= 0: win = H; area = area if t0 == 0 else 0.0
        L = area / win if win > 0 else 0.0
        W = 60.0 * (sum(soj) / len(soj)) if soj else 0.0
        arr = arr_n * win / H / max(win / H, 1e-12) if False else arr_n
        dep = dep_n
        busy_frac = (busy1 + busy2) / (2.0 * win) if win > 0 else 0.0
        p_wait = (wait_pos / len(soj)) if soj else 0.0
        dep_rate = dep / win if win > 0 else 0.0
        per.append({"L": L, "W": W, "arr": float(arr), "dep": float(dep),
                    "blk": float(blk_n), "busy_frac": busy_frac,
                    "p_loss": 0.0, "p_wait": p_wait, "dep_rate": dep_rate})
    n = len(per)
    def avg(k):
        return sum(d[k] for d in per) / n if n else 0.0
    out = {
        "L": avg("L"), "W": avg("W"),
        "runtime_units": float(H),
        "seed_list": seed_list, "seeds_used": n,
        "time_unit": "hour", "win": float(H - t0),
        "arr": avg("arr"), "dep": avg("dep"), "blk": avg("blk"),
        "busy_frac": avg("busy_frac"), "busy_util": avg("busy_frac"),
        "dep_rate": avg("dep_rate"),
        "lam_eff": avg("dep_rate"), "p_loss": 0.0, "p_wait": avg("p_wait"),
        "per_seed_L": [d["L"] for d in per],
        "per_seed_W": [d["W"] for d in per],
        "per_seed_busy_frac": [d["busy_frac"] for d in per],
        "per_seed_p_loss": [0.0 for d in per],
        "per_seed_p_wait": [d["p_wait"] for d in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
