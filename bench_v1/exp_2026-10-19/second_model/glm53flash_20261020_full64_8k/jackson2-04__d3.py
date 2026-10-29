import argparse, json, math, random
from collections import deque

def run_seed(seed, H, lam, s1m, s2m, warm):
    rng = random.Random(seed)
    t = 0.0
    na = rng.expovariate(lam)
    s1_q, s2_q = deque(), deque()
    s1_dep, s2_dep = math.inf, math.inf
    s1_busy, s2_busy = False, False
    area, busy1, busy2 = 0.0, 0.0, 0.0
    arr_n = dep_n = 0
    w_sum = 0.0
    p_wait_hit = 0
    total = lambda: len(s1_q) + len(s2_q) + int(s1_busy) + int(s2_busy)
    while True:
        tn = min(na, s1_dep, s2_dep)
        if tn >= H and not s1_busy and not s2_busy and not s1_q and not s2_q:
            break
        if tn > H:
            tn = H
        if tn > t:
            seg = tn - t
            if tn > warm:
                lo = max(t, warm)
                w = tn - lo
                if w > 0:
                    area += total() * w
                    busy1 += int(s1_busy) * w
                    busy2 += int(s2_busy) * w
            t = tn
        if tn == na and na <= H:
            arr_n += 1
            inwin = na > warm
            s1_q.append((na, rng.expovariate(1.0 / s1m), rng.expovariate(1.0 / s2m), inwin))
            na = rng.expovariate(lam) if na < H else math.inf
        elif tn == s1_dep:
            s2_q.append(s1_q.popleft() if False else s1_done)
            s1_busy = False
        elif tn == s2_dep:
            job = s2_done
            if job[3]:
                w_sum += t - job[0]
                dep_n += 1
                if job[6]:
                    p_wait_hit += 1
            s2_busy = False
        if not s1_busy and s1_q:
            s1_done = s1_q.popleft()
            s1_busy = True
            s1_dep = t + s1_done[1]
        else:
            s1_dep = math.inf if not s1_busy else s1_dep
        if not s2_busy and s2_q:
            s2_done = s2_q.popleft()
            s2_busy = True
            s2_dep = t + s2_done[2]
        else:
            s2_dep = math.inf if not s2_busy else s2_dep
        if na >= H and not s1_busy and not s2_busy and not s1_q and not s2_q:
            break
    win = H - warm
    cnt = max(arr_n, 1)
    busy_frac = (busy1 + busy2) / (2.0 * win)
    return {
        "L": area / win, "W": w_sum / max(dep_n, 1),
        "arr": arr_n, "dep": dep_n, "busy_frac": busy_frac,
        "p_wait": p_wait_hit / cnt, "p_loss": 0.0,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    lam, s1m, s2m = 4.0, 6.0, 5.0
    if a.pert == "lam_up": lam *= 1.2
    elif a.pert == "mu_up": s1m /= 1.2; s2m /= 1.2
    elif a.pert == "c_up": s1m *= 1.2; s2m *= 1.2
    lam_pm = lam / 60.0
    warm = 0.25 * a.horizon
    win = a.horizon - warm
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run_seed(s, a.horizon, lam_pm, s1m, s2m, warm) for s in seed_list]
    n = len(per)
    L = sum(r["L"] for r in per) / n
    W = sum(r["W"] for r in per) / n
    arr = sum(r["arr"] for r in per) / n
    dep = sum(r["dep"] for r in per) / n
    busy_frac = sum(r["busy_frac"] for r in per) / n
    p_wait = sum(r["p_wait"] for r in per) / n
    p_loss = 0.0
    out = {
        "L": round(L, 4), "W": round(W, 4),
        "runtime_units": round(win * n, 4), "seed_list": seed_list,
        "seeds_used": n, "time_unit": "minute", "win": round(win, 4),
        "arr": round(arr, 4), "blk": round(p_loss * arr, 4),
        "busy_frac": round(busy_frac, 4), "busy_util": round(busy_frac, 4),
        "dep": round(dep, 4), "dep_rate": round(dep / win, 4),
        "lam_eff": round(dep / win, 4), "p_loss": 0.0,
        "p_wait": round(p_wait, 4),
        "per_seed_L": [round(r["L"], 4) for r in per],
        "per_seed_W": [round(r["W"], 4) for r in per],
        "per_seed_busy_frac": [round(r["busy_frac"], 4) for r in per],
        "per_seed_p_loss": [0.0] * n,
        "per_seed_p_wait": [round(r["p_wait"], 4) for r in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
