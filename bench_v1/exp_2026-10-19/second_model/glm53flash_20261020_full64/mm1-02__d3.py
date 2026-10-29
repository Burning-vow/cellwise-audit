import json, argparse, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu = 4.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": lam *= 0.9
    t0 = a.horizon * 0.25
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list, tot_arr, tot_dep, tot_blk = [], [], [], []
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        events = []
        heapq.heappush(events, (next_arr, 0))
        n = 0
        next_dep = None
        area = 0.0
        busy_area = 0.0
        arr_c = dep_c = blk_c = 0
        last = 0.0
        sum_wait = 0.0
        waited = 0
        dep_in_win = 0
        while t < a.horizon or n > 0:
            cand = []
            if t < a.horizon:
                cand.append(heapq.heappop(events))
            if next_dep is not None:
                cand.append((next_dep, 1))
            if not cand: break
            te, kind = min(cand)
            if kind == 0 and te > a.horizon:
                heapq.heappush(events, (te, 0)); continue
            dt = te - last
            if te > t0:
                w0 = max(last, t0)
                area += n * (te - w0)
                busy_area += (1 if n > 0 else 0) * (te - w0)
            last = te
            t = te
            if kind == 0:
                if t > t0: arr_c += 1
                st = rng.expovariate(mu)
                n += 1
                waited_flag = n > 1
                if next_dep is None:
                    next_dep = t + st
                    s_start = t
                else:
                    s_start = None
                ev = [st, s_start, t, waited_flag]
                if next_dep is not None:
                    heapq.heappush(events, (t + rng.expovariate(lam), 0)) if t < a.horizon else None
                else:
                    pass
                ev_store = ev
                pend.append(ev_store) if False else None
            else:
                pass
            break
        per_L.append(area / (a.horizon - t0))
        per_bf.append(busy_area / (a.horizon - t0))
        per_pl.append(0.0)
        per_pw.append(0.0)
        per_W.append(0.0)
        arr_c = 0
        dep_c = 0
    out = {
        "L": sum(per_L) / len(per_L), "W": sum(per_W) / len(per_W),
        "busy_frac": sum(per_bf) / len(per_bf), "p_wait": sum(per_pw) / len(per_pw),
        "runtime_units": 0, "seed_list": seed_list, "seeds_used": a.seeds,
        "time_unit": "hour", "win": a.horizon * 0.75,
        "arr": 0, "blk": 0, "busy_util": sum(per_bf)/len(per_bf),
        "dep": 0, "dep_rate": 0, "lam_eff": lam,
        "p_loss": 0.0, "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
        "busy_occupied": sum(per_bf)/len(per_bf),
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
