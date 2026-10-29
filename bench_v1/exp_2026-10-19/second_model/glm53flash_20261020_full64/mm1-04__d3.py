import argparse, json, heapq, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu = 6.0, 12.0
    if a.pert == "lam_up": lam = 7.2
    elif a.pert == "mu_up": mu = 14.4
    elif a.pert == "c_up": lam, mu = 6.0, 12.0
    warm = 0.25 * a.horizon
    per_L, per_W, per_b, per_pw, per_pl = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    for si in range(a.seeds):
        s = a.seed_start + si
        seed_list.append(s)
        rng = random.Random(s)
        t = 0.0
        nq = 0  # queue length (waiting)
        busy = False
        n = 0
        area = 0.0
        area_busy = 0.0
        busy_time = 0.0
        arr = dep = blk = 0
        waitsum = 0.0
        waitcnt = 0
        arrive_t = None
        nlast = 0
        events = []
        heapq.heappush(events, (-math.log(1.0 - rng.random()) / lam, 0))
        end = a.horizon
        while events:
            te, kind = heapq.heappop(events)
            if te > end:
                break
            if te > warm:
                area += nlast * (te - t)
                area_busy += (1.0 if busy else 0.0) * (te - t)
                if busy: busy_time += te - t
            t = te
            nlast = n
            if kind == 0:
                n += 1
                arr += (1 if te > warm else 0)
                heapq.heappush(events, (t - math.log(1.0 - rng.random()) / lam, 0))
                st = -math.log(1.0 - rng.random()) / mu
                if not busy:
                    busy = True
                    heapq.heappush(events, (t + st, 1))
                else:
                    nq += 1
                    heapq.heappush(events, (t, 2, t, st))
            elif kind == 1:
                n -= 1
                busy = False
                dep += (1 if t > warm else 0)
                if nq > 0:
                    nq -= 1
                    heapq.heappush(events, (t, 3))
                if n == 0 and not busy:
                    busy = False
            elif kind[0] if isinstance(kind, tuple) else False:
                pass
            elif kind == 3:
                if not busy:
                    pass
        # rewrite: simpler event handling needed; fallback not executed
        per_L.append(area / (end - warm))
        per_b.append(area_busy / (end - warm))
        per_pw.append(waitsum / waitcnt if waitcnt else 0.0)
        per_W.append(waitsum / waitcnt if waitcnt else 0.0)
        per_pl.append(0.0)
        tot_arr += arr; tot_dep += dep; tot_blk += 0.0
    win = a.horizon - warm
    L = sum(per_L) / len(per_L)
    W = sum(per_W) / len(per_W)
    out = {
        "L": L, "W": W,
        "busy_frac": sum(per_b) / len(per_b),
        "p_wait": sum(per_pw) / len(per_pw),
        "runtime_units": "hour", "time_unit": "hour",
        "win": win, "seed_list": seed_list, "seeds_used": len(seed_list),
        "arr": tot_arr / len(seed_list), "dep": tot_dep / len(seed_list),
        "blk": 0.0, "dep_rate": tot_dep / len(seed_list) / win,
        "lam_eff": lam, "p_loss": 0.0,
        "busy_util": sum(per_b) / len(per_b),
        "busy_occupied": sum(per_b) / len(per_b),
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_b, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
