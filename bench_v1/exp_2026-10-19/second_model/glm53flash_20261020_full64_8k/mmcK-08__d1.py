import argparse, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=20)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    c, K = 3, 4
    lam, mu = 8.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot = {"arr":0.0,"dep":0.0,"blk":0.0,"A_N":0.0,"A_B":0.0,"A_WT":0.0,"n_wait":0,"n_waited":0,"T":0.0,"busy_occ":0.0}
    seed_list = []
    for s in range(S, S + n_seeds):
        rng = random.Random(s * 7919 + 13)
        seed_list.append(s)
        t = 0.0; N = 0; served = [None]*c; q = []
        arr = dep = blk = 0
        A_N = A_B = A_WT = 0.0
        n_wait = n_waited = 0
        last = 0.0; busy_occ = 0.0
        while True:
            tn = rng.expovariate(lam)
            td = min(served) if N > len(q) and any(x is not None for x in served) else None
            dts = [x - t for x in served if x is not None]
            dt_d = min(dts) if dts else None
            dt_a = tn
            if dt_d is not None and dt_d < dt_a and t + dt_d <= H:
                dt = dt_d
            elif t + dt_a <= H:
                dt = dt_a; is_arr = True
            else:
                break
            if t >= warm:
                A_N += N * dt; A_B += (1 if N > 0 else 0) * dt
                if N > 0: busy_occ += dt
            t += dt
            if is_arr:
                arr += 1
                st = rng.expovariate(mu)
                if N < K:
                    N += 1
                    n_waited += 1 if len([x for x in served if x is None]) == 0 else 0
                    free = [i for i in range(c) if served[i] is None]
                    if free:
                        served[free[0]] = t + st
                        n_wait += 1 if False else 0
                    else:
                        q.append((t, st))
                    if t >= warm:
                        pass
                else:
                    blk += 1
            else:
                done = min(range(c), key=lambda i: served[i] if served[i] is not None else math.inf)
                served[done] = None
                dep += 1
                if q:
                    at, st = q.pop(0)
                    if t >= warm:
                        A_WT += t - at; n_wait += 1
                    free = [i for i in range(c) if served[i] is None]
                    served[free[0]] = t + st
                N -= 1
        if t <= warm: 
            per_L.append(0.0); per_W.append(0.0); per_bf.append(0.0); per_pl.append(0.0); per_pw.append(0.0); continue
        win = t - warm
        n_arr_w = arr; n_dep_w = dep; n_blk_w = blk
        L = A_N / win
        busy_frac = A_B / win
        p_loss = n_blk_w / n_arr_w if n_arr_w else 0.0
        p_wait = (n_wait / n_dep_w) if n_dep_w else 0.0
        Wmin = (A_WT / n_wait * 60.0) if n_wait else 0.0
        per_L.append(L); per_W.append(Wmin); per_bf.append(busy_frac); per_pl.append(p_loss); per_pw.append(p_wait)
        tot["arr"] += n_arr_w; tot["dep"] += n_dep_w; tot["blk"] += n_blk_w
        tot["A_N"] += A_N; tot["A_B"] += A_B; tot["A_WT"] += A_WT
        tot["n_wait"] += n_wait; tot["n_waited"] += n_dep_w; tot["T"] += win
        tot["busy_occ"] += busy_occ
    T = tot["T"]; ns = len(per_L)
    L = tot["A_N"] / T
    busy_frac = tot["A_B"] / T
    busy_util = 0.0
    p_loss = tot["blk"] / tot["arr"] if tot["arr"] else 0.0
    p_wait = tot["n_wait"] / tot["n_waited"] if tot["n_waited"] else 0.0
    W = (tot["A_WT"] / tot["n_wait"] * 60.0) if tot["n_wait"] else 0.0
    dep_rate = tot["dep"] / T
    out = {"L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
           "runtime_units": "python3", "seed_list": seed_list, "seeds_used": ns,
           "time_unit": "hour", "win": H * 0.75,
           "arr": tot["arr"]/ns, "blk": tot["blk"]/ns, "busy_util": busy_util,
           "busy_occupied": busy_frac, "dep": tot["dep"]/ns, "dep_rate": dep_rate,
           "lam_eff": (tot["arr"] - tot["blk"])/T, "p_wait": p_wait,
           "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
           "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
