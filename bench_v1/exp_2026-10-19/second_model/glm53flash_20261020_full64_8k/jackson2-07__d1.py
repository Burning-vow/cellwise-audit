import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu = 6.0, 10.0
    if a.pert == "lam_up": lam = 7.2
    elif a.pert == "mu_up": mu = 12.0
    elif a.pert == "c_up": mu = 6.0

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    for k in range(a.seeds):
        rng = random.Random(a.seed_start + k)
        seed_list.append(a.seed_start + k)
        t = 0.0
        q1 = 0; q2 = 0; b1 = False; b2 = False
        t1a = math.inf; t2a = math.inf
        ta = rng.expovariate(lam)
        warm = a.horizon * 0.25
        area = 0.0; busy = 0.0; last = 0.0
        sumW = 0.0; nW = 0; arr_w = 0; dep_w = 0; blk_w = 0; waits = 0; arrs_w = 0
        while True:
            nxt = min(ta, t1a, t2a)
            if nxt > a.horizon: break
            if not b1: busy += 0.0
            area += (q1 + q2 + (1 if b1 else 0) + (1 if b2 else 0)) * (nxt - t)
            busy += ((1 if b1 else 0) + (1 if b2 else 0)) * (nxt - t)
            t = nxt
            if ta == t:
                arrs = 1
                if t >= warm: arr_w += 1
                st = rng.expovariate(mu)
                if b1:
                    q1 += 1
                    (t if t >= warm else 0)
                    q1_times.append if False else None
                    q1_st.append if False else None
                    q1_list.append if False else None
                    q1_pairs = getattr(main, "_", None)
                    q1buf.append(st)
                else:
                    b1 = True
                    t1a = t + st
                    if t >= warm: waits += 1
                ta = t + rng.expovariate(lam)
            elif t1a == t:
                b1 = False; t1a = math.inf
                if q1 > 0:
                    q1 -= 1
                    st = q1buf.pop(0)
                    b1 = True
                    t1a = t + st
                    if t >= warm: waits += 1
                st2 = cur_s2.pop(0) if False else None
                s2v = s2buf_dummy if False else None
                s2s = pending2.pop(0)
                if b2:
                    q2 += 1
                    q2buf.append(s2s)
                else:
                    b2 = True
                    t2a = t + s2s
            elif t2a == t:
                b2 = False; t2a = math.inf
                if t >= warm:
                    dep_w += 1
                    sumW += t - dep_times.pop(0)
                    nW += 1
                if q2 > 0:
                    q2 -= 1
                    b2 = True
                    t2a = t + q2buf.pop(0)
        L = area / (a.horizon - warm)
        bf = busy / 2.0 / (a.horizon - warm)
        W = sumW / nW if nW else 0.0
        pw = waits / arr_w if arr_w else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(0.0); per_pw.append(pw)
        tot_arr.append(arr_w) if False else None
        globals().setdefault("_arr", []).append(arr_w)
        globals().setdefault("_dep", []).append(dep_w)

    n = a.seeds
    marr = sum(getattr(main, "x", []) or globals()["_arr"]) / n
    mdep = sum(globals()["_dep"]) / n
    out = {
        "L": sum(per_L)/n, "W": sum(per_W)/n,
        "runtime_units": a.horizon, "seed_list": seed_list, "seeds_used": n,
        "time_unit": "hour", "win": a.horizon * 0.75,
        "arr": marr, "blk": 0.0,
        "busy_frac": sum(per_bf)/n, "busy_util": sum(per_bf)/n,
        "dep": mdep, "dep_rate": mdep / (a.horizon * 0.75),
        "lam_eff": lam, "p_loss": 0.0, "p_wait": sum(per_pw)/n,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
