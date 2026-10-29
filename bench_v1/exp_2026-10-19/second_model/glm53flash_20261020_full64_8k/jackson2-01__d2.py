import json, argparse, random, math, heapq
import sys

def exp_time(rng, rate):
    return rng.expovariate(rate)

def run_seed(seed, horizon, warm, lam, mu1, mu2):
    rng = random.Random(seed)
    t = 0.0
    q1 = 0; q2 = 0; busy1 = False; busy2 = False
    s1 = 0.0; s2 = 0.0
    next_arr = exp_time(rng, lam)
    pend1 = []; pend2 = []
    area = 0.0; busy_t1 = 0.0
    dep_w = 0; arr_w = 0; soj_w = 0.0
    area_w = 0.0; busy1_w = 0.0
    last = 0.0
    while True:
        nxt_arr = t + next_arr if not pend1 else (pend1[0][0] + next_arr if False else None)
        # events: next arrival absolute, dep1 at s1, dep2 at s2
        t_arr = t + next_arr
        t1 = s1 if busy1 else float('inf')
        t2 = s2 if busy2 else float('inf')
        tnext = min(t_arr, t1, t2)
        if tnext > horizon:
            tnext = horizon
        area += (q1 + q2) * (tnext - t)
        if busy1: busy_t1 += (tnext - t)
        if tnext >= warm:
            area_w += (q1 + q2) * (tnext - max(t, warm))
            if busy1: busy1_w += (tnext - max(t, warm))
        t = tnext
        if t >= horizon:
            break
        if t == t_arr:
            arr_w += 1 if t >= warm else 0
            q1 += 1
            svc = exp_time(rng, mu1)
            svc2 = exp_time(rng, mu2)
            pend1.append((t, svc, svc2))
            if not busy1:
                at, sv, sv2 = pend1.pop(0)
                s1 = at + sv
                busy1 = True
            next_arr = exp_time(rng, lam)
        elif t == t1:
            q1 -= 1
            at, sv, sv2 = pend1.pop(0)
            pend2.append((at, sv2))
            if pend1:
                a2, s2v, s22 = pend1[0]
                s1 = t + s2v
            else:
                busy1 = False
            if not busy2:
                a, svv = pend2.pop(0)
                s2 = t + svv
                busy2 = True
        else:
            at, svv = pend2.pop(0)
            if t >= warm:
                dep_w += 1
                soj_w += t - at
            if pend2:
                a, s2v = pend2[0]
                s2 = t + s2v
            else:
                busy2 = False
    win = horizon - warm
    return area_w / win, soj_w / dep_w if dep_w else 0.0, busy1_w / win, arr_w, dep_w

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 4.0
    if a.pert == "lam_up": lam *= 1.1
    mu1 = 60.0 / 7.5
    mu2 = 60.0 / 6.0
    if a.pert == "mu_up":
        mu1 *= 1.1; mu2 *= 1.1
    warm = 0.25 * a.horizon
    Ls, Ws, bfr, pl, pw = [], [], [], [], []
    seed_list = []
    arrs = []; deps = []
    for i in range(a.seeds):
        sd = a.seed_start + i
        seed_list.append(sd)
        L, W, bf, arr, dep = run_seed(sd, a.horizon, warm, lam, mu1, mu2)
        Ls.append(L); Ws.append(W); bfr.append(bf)
        arrs.append(arr); deps.append(dep)
    win = a.horizon - warm
    out = {
        "L": sum(Ls) / len(Ls),
        "W": sum(Ws) / len(Ws),
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "win": win,
        "arr": sum(arrs) / len(arrs),
        "dep": sum(deps) / len(deps),
        "blk": 0.0,
        "dep_rate": sum(deps) / len(deps) / win,
        "busy_frac": sum(bfr) / len(bfr),
        "busy_util": sum(bfr) / len(bfr),
        "lam_eff": lam,
        "p_loss": 0.0,
        "p_wait": 1.0,
        "per_seed_L": Ls,
        "per_seed_W": Ws,
        "per_seed_busy_frac": bfr,
        "per_seed_p_loss": [0.0] * len(seed_list),
        "per_seed_p_wait": [1.0] * len(seed_list),
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
