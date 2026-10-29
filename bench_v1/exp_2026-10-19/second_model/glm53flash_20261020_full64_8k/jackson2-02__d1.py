import argparse, heapq, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    lam, mu1, mu2 = 4.0, 8.0, 12.0
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif pert == "c_up": lam *= 1.05
    warm = 0.25 * H
    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list = []
    tarr = tdep = tblk = tbusy1 = tbusy2 = twait = tseen = 0.0
    for s in range(S, S + n_seeds):
        rng = random.Random(s)
        t = 0.0; n1 = n2 = 0
        arrivals = []
        next_arr = rng.expovariate(lam)
        ev = []
        heapq.heapify(ev)
        arr_count = dep_count = loss_count = 0
        area_L = 0.0; area_b1 = 0.0; area_b2 = 0.0
        soj = []; wait_flags = []
        last = 0.0
        while True:
            cands = []
            if next_arr < H: cands.append((next_arr, 0))
            if n1 > 0: cands.append((heapq.heappop(ev)[0] if False else _nx1, 1)) if False else None
            break
        break
    # event loop rewritten cleanly below
    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list = []
    for s in range(S, S + n_seeds):
        rng = random.Random(s)
        t = 0.0; n1 = n2 = 0
        next_arr = rng.expovariate(lam)
        done1 = []; done2 = []
        busy1 = busy2 = False
        s1 = s2 = 0.0  # remaining service completion times
        arr_count = dep_count = loss_count = 0
        area_L = 0.0; area_b1 = 0.0; area_b2 = 0.0
        soj = []; wait_flags = []
        while True:
            cands = []
            if next_arr < H: cands.append((next_arr, 0))
            if busy1: cands.append((s1, 1))
            if busy2: cands.append((s2, 2))
            if not cands:
                t = H; break
            tc, kind = min(cands)
            if tc >= H:
                t = H; break
            if tc >= warm:
                area_L += (n1 + n2) * (tc - t)
                area_b1 += (1 if busy1 else 0) * (tc - t)
                area_b2 += (1 if busy2 else 0) * (tc - t)
            t = tc
            if kind == 0:
                arr_count += 1
                d1 = rng.expovariate(mu1); d2 = rng.expovariate(mu2)
                item = (t, d1, d2, t)
                if not busy1:
                    busy1 = True; s1 = t + d1; item = (t, d1, d2, t, True)
                else:
                    q1.append(item) if False else None
                try: q1
                except NameError: q1 = []
                if not busy1:
                    pass
                else:
                    q1.append((t, d1, d2, t))
                next_arr = t + rng.expovariate(lam)
            elif kind == 1:
                busy1 = False
                it = cur1
                a_t, d1v, d2v, enq = it[0], it[1], it[2], it[3]
                if tc >= warm: pass
                if not busy2:
                    busy2 = True; s2 = t + d2v; cur2 = (a_t, d2v, enq, t)
                else:
                    try: q2
                    except NameError: q2 = []
                    q2.append((a_t, d2v, enq, t))
                if q1:
                    cur1 = q1.pop(0); busy1 = True; s1 = t + cur1[1]
            else:
                busy2 = False
                a_t, d2v, enq, st2 = cur2
                dep_count += 1
                soj.append(t - a_t)
                wait_flags.append((st2 - enq) > 1e-12)
                if q2:
                    cur2 = q2.pop(0); busy2 = True; s2 = t + cur2[1]
        win = H - warm
        L = area_L / win if win > 0 else 0.0
        W = (sum(soj) / len(soj) * 60.0) if soj else 0.0
        bf = (area_b1 + area_b2) / (2 * win) if win > 0 else 0.0
        pw = (sum(wait_flags) / len(wait_flags)) if wait_flags else 0.0
        per_L.append(L); per_W.append(W); per_busy.append(bf)
        per_ploss.append(0.0); per_pwait.append(pw)
        seed_list.append(s)
        tarr += arr_count; tdep += dep_count; tblk += 0
        tbusy1 += area_b1 / win if win > 0 else 0.0
        tbusy2 += area_b2 / win if win > 0 else 0.0
        tseen += 1
        globals()  # no-op
    # aggregate
    L = sum(per_L) / len(per_L) if per_L else 0.0
    W = sum(per_W) / len(per_W) if per_W else 0.0
    win = H - warm
    busy_frac = (tbusy1 + tbusy2) / (2 * tseen) if tseen else 0.0
    out = {
        "L": L, "W": W, "runtime_units": H, "seed_list": seed_list,
        "seeds_used": len(seed_list), "time_unit": "hour", "win": win,
        "arr": tarr / tseen if tseen else 0.0,
        "blk": tblk / tseen if tseen else 0.0,
        "busy_frac": busy_frac,
        "busy_util": busy_frac,
        "dep": tdep / tseen if tseen else 0.0,
        "dep_rate": (tdep / tseen) / win if tseen and win > 0 else 0.0,
        "lam_eff": lam, "p_loss": 0.0,
        "p_wait": (sum(per_pwait) / len(per_pwait)) if per_pwait else 0.0,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
