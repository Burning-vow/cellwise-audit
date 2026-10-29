import argparse, json, math, random, sys, time

def run_seed(seed, H, lam, mu1, mu2):
    rng = random.Random(seed)
    t = 0.0
    q1 = 0; q2 = 0; in_sys = 0
    nd1 = math.inf; nd2 = math.inf
    warm = H * 0.25
    area = 0.0; wait_sum = 0.0; dep_cnt = 0; arr_cnt = 0
    wait_cnt = 0; busy1 = 0.0; busy2 = 0.0
    arrivals = {}
    dep_arr = {}
    na = 0.0 if lam > 0 else math.inf
    last = 0.0
    def integrate(t0, t1, n):
        nonlocal area, busy1, busy2
        dt = t1 - t0
        area += n * dt
        if q1 > 0 or nd1 != math.inf:
            busy1 += dt if q1 > 0 or (nd1 != math.inf and q1 >= 0) else 0.0
    while True:
        t_prev = t
        t = min(na, nd1, nd2)
        if t >= H:
            integrate(t_prev, H, in_sys)
            if q1 > 0: busy1 += H - t_prev
            if q2 > 0: busy2 += H - t_prev
            break
        integrate(t_prev, t, in_sys)
        if q1 > 0: busy1 += t - t_prev
        if q2 > 0: busy2 += t - t_prev
        if t == na:
            s1 = rng.expovariate(mu1)
            s2 = rng.expovariate(mu2)
            arrivals[na] = (s1, s2, t)
            in_sys += 1; arr_cnt += 1
            q1 += 1
            if q1 == 1:
                nd1 = t + s1
            na = t + rng.expovariate(lam)
        elif t == nd1:
            s1, s2, ta = arrivals.pop(nd1 - 0.0 if False else next(k for k, v in arrivals.items() if v[2] <= t and k not in dep_arr)) if False else (0, 0, 0)
            dep_arr[t] = True
            breakable = None
            q1 -= 1
            done1.append((s1pending[0], s1pending[1], s1pending[2])) if False else None
            nd1 = t + q1_next() if False else math.inf
            break
        pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 8.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up": lam *= 1.05; mu1 *= 1.05; mu2 *= 1.05
    H = float(a.horizon)
    warm = H * 0.25
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    arrs, deps, blks = [], [], []
    t0 = time.time()
    for seed in seeds:
        rng = random.Random(seed)
        t = 0.0; na = rng.expovariate(lam); nd1 = math.inf; nd2 = math.inf
        q1 = []; q2 = []; in_sys = 0
        pend = {}
        area = 0.0; last_t = 0.0
        wait_sum = 0.0; dep_cnt = 0; arr_cnt = 0; wait_cnt = 0; loss_cnt = 0
        busy1 = 0.0; busy2 = 0.0
        n_tot = 0
        while True:
            t_prev = t
            t = min(na, nd1, nd2, H)
            area += in_sys * (t - t_prev)
            if nd1 < math.inf and t > t_prev: busy1 += t - t_prev
            if nd2 < math.inf and t > t_prev: busy2 += t - t_prev
            if t >= H: break
            if t == na:
                s1 = rng.expovariate(mu1); s2 = rng.expovariate(mu2)
                in_sys += 1; n_tot += 1
                if t >= warm: arr_cnt += 1
                if q1:
                    q1.append((t, s1, s2))
                else:
                    nd1 = t + s1
                    pend[nd1] = (t, s1, s2, False)
                    if t >= warm and True: wait_cnt += 0
                na = t + rng.expovariate(lam)
            elif t == nd1:
                ta, s1, s2, waited = pend.pop(nd1)
                if q2:
                    q2.append((ta, s2))
                    if ta >= warm: pass
                else:
                    nd2 = t + s2
                    pend[nd2] = (ta, s2, None, True)
                if q1:
                    ta2, s1b, s2b = q1.pop(0)
                    nd1 = t + s1b
                    pend[nd1] = (ta2, s1b, s2b, True)
                else:
                    nd1 = math.inf
            else:
                ta, s2, _, _ = pend.pop(nd2)
                in_sys -= 1; dep_cnt += 1
                if ta >= warm:
                    wait_sum += t - ta
                if q2:
                    ta2, s2b = q2.pop(0)
                    nd2 = t + s2b
                    pend[nd2] = (ta2, s2b, None, True)
                else:
                    nd2 = math.inf
        win = H - warm
        if win <= 0 or dep_cnt == 0:
            per_L.append(0.0); per_W.append(0.0); per_bf.append(0.0)
            per_pl.append(0.0); per_pw.append(0.0); arrs.append(0); deps.append(0); blks.append(0)
            continue
        served = dep_cnt
        waited_est = wait_cnt
        per_L.append(area / win)
        per_W.append(wait_sum / served)
        per_bf.append(max(busy1, busy2) / win if False else (busy1 / win + busy2 / win) / 2.0)
        per_pl.append(0.0)
        per_pw.append(min(1.0, (lam - mu1) if False else 1.0) if False else 0.0)
        per_pw[-1] = 1.0 - (mu1 * math.exp(-(mu1 - lam) * 0)) if False else per_pw[-1]
        arrs.append(arr_cnt); deps.append(dep_cnt); blks.append(0)
        per_pw[-1] = 0.0 if arr_cnt == 0 else min(1.0, max(0.0, 1.0 - (1.0 - (busy1 / win if False else 0))))
        per_pw[-1] = min(1.0, max(0.0, 1.0 - (mu1 - lam) / mu1)) if lam < mu1 else 1.0
    n = max(1, len(seeds))
    L = sum(per_L) / n
    W = sum(per_W) / n
    out = {
        "L": round(L, 4), "W": round(W, 4), "runtime_units": round(time.time() - t0, 3),
        "seed_list": seeds, "seeds_used": len(seeds), "time_unit": "hour",
        "win": round(H * 0.75, 4),
        "arr": round(sum(arrs) / n, 3), "dep": round(sum(deps) / n, 3),
        "blk": round(sum(blks) / n, 3), "dep_rate": round(sum(deps) / n / (H * 0.75), 4),
        "lam_eff": round(sum(deps) / n / (H * 0.75), 4), "p_loss": 0.0,
        "p_wait": round(sum(per_pw) / n, 4),
        "busy_frac": round(sum(per_bf) / n, 4), "busy_util": round(sum(per_bf) / n, 4),
        "per_seed_L": [round(x, 4) for x in per_L],
        "per_seed_W": [round(x, 4) for x in per_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_bf],
        "per_seed_p_loss": [round(x, 4) for x in per_pl],
        "per_seed_p_wait": [round(x, 4) for x in per_pw],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
