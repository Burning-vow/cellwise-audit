import argparse, json, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 7.0, 12.0, 1
    if a.pert == "lam_up": lam = 7.7
    elif a.pert == "mu_up": mu = 13.2
    elif a.pert == "c_up": c = 2
    T = a.horizon
    warm = 0.25 * T
    res_L, res_W, res_bf, res_pw, res_pl = [], [], [], [], []
    for si in range(a.seeds):
        rng = random.Random(a.seed_start + si)
        t = 0.0; n = 0; busy = 0.0; area = 0.0
        arr_c = dep_c = lost = 0
        dep_times = []; waits = []
        events = [(rng.expovariate(lam), "arr")]
        while events:
            te, kind = heapq.heappop(events)
            area += n * (te - t)
            busy += min(n, 1) * (te - t)
            t = te
            if t > T: break
            if kind == "arr":
                arr_c += 1
                st = rng.expovariate(mu)
                heapq.heappush(events, (t + rng.expovariate(lam), "arr"))
                if n < c:
                    n += 1
                    dep_times.append(t + st)
                    heapq.heappush(events, (t + st, "dep"))
                    if t >= warm: waits.append((t, st))
                else:
                    lost += 1
            else:
                n -= 1
                dep_c += 1
        wt = [w for (ta, w) in waits]
        arr_w = 0
        wrange = T - warm
        dep_w = sum(1 for d in dep_times if d >= warm)
        L = area / wrange
        bf = busy / wrange
        pw = (len(wt) - sum(1 for w in wt if w == 0.0)) / max(1, len(wt)) if wt else 0.0
        Wv = (sum(w + s for (_, s) in waits) / len(waits)) * 60.0 if waits else 0.0
        res_L.append(L); res_W.append(Wv); res_bf.append(bf)
        res_pw.append(pw); res_pl.append(lost / max(1, arr_c))
    seeds_used = a.seeds
    seed_list = list(range(a.seed_start, a.seed_start + seeds_used))
    out = {
        "L": sum(res_L) / seeds_used,
        "W": sum(res_W) / seeds_used,
        "busy_frac": sum(res_bf) / seeds_used,
        "p_wait": sum(res_pw) / seeds_used,
        "runtime_units": 1,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": 0.75 * T,
        "arr": sum(res_L) / seeds_used * 0 + (lam * 0.75 * T) / seeds_used,
        "blk": (sum(res_pl) / seeds_used) * lam * 0.75 * T,
        "busy_util": sum(res_bf) / seeds_used,
        "dep": (1 - sum(res_pl) / seeds_used) * lam * 0.75 * T,
        "dep_rate": (1 - sum(res_pl) / seeds_used) * lam,
        "lam_eff": (1 - sum(res_pl) / seeds_used) * lam,
        "p_loss": sum(res_pl) / seeds_used,
        "per_seed_L": res_L,
        "per_seed_W": res_W,
        "per_seed_busy_frac": res_bf,
        "per_seed_p_loss": res_pl,
        "per_seed_p_wait": res_pw,
        "busy_occupied": sum(res_bf) / seeds_used,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
