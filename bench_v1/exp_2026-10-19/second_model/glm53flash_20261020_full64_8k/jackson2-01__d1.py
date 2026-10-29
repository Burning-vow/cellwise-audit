import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    NS, H, S = int(a.seeds), a.horizon, int(a.seed_start)
    lam, mu1, mu2 = 4.0, 8.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up": pass
    warm = 0.25 * H
    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_wait_frac = 0.0
    for k in range(NS):
        rng = random.Random(S + k)
        seed_list.append(S + k)
        t = 0.0
        q1, q2 = [], []
        busy1_end = busy2_end = -1.0
        area = 0.0
        busy1 = busy2 = 0.0
        arr = dep = 0
        waits = []
        last_t = 0.0
        def next_arr():
            return t + rng.expovariate(lam)
        na = rng.expovariate(lam)
        while True:
            c1 = q1[0][1] if q1 else math.inf
            c2 = q2[0][1] if q2 else math.inf
            tn = min(na, c1, c2)
            if tn > H:
                tn = H
            n_now = len(q1) + (1 if busy1_end > t else 0) + len(q2) + (1 if busy2_end > t else 0)
            if t >= warm and tn > t:
                area += n_now * (tn - t)
                b1 = busy1_end > t and busy1_end <= tn
                if busy1_end > t:
                    busy1 += min(busy1_end, tn) - t
                if busy2_end > t:
                    busy2 += min(busy2_end, tn) - t
            t = tn
            if t >= H:
                break
            if t == na:
                arr += 1
                s1 = rng.expovariate(mu1)
                s2 = rng.expovariate(mu2)
                job = [t, s1, s2]
                st1 = max(t, busy1_end)
                job.append(st1 + s1)
                heapq.heappush(q1, (job[3], job))
                busy1_end = st1 + s1
                na = t + rng.expovariate(lam)
            elif q1 and t == q1[0][0]:
                _, job = heapq.heappop(q1)
                if t >= warm:
                    waits.append(job[3] - job[0])
                st2 = max(t, busy2_end)
                job.append(st2 + job[2])
                heapq.heappush(q2, (job[4], job))
                busy2_end = st2 + job[2]
            elif q2 and t == q2[0][0]:
                _, job = heapq.heappop(q2)
                if t >= warm:
                    dep += 1
                    waits.append(job[4] - job[0])
            else:
                continue
        win = H - warm
        W = sum(waits) / len(waits) if waits else 0.0
        L = area / win
        per_L.append(L)
        per_W.append(W)
        per_busy.append((busy1 + busy2) / (2.0 * win))
        per_ploss.append(0.0)
        nsys_warm = arr
        per_pwait.append(1.0 if waits and all(w > 0 for w in waits) else (sum(1 for w in waits if w > 0) / len(waits) if waits else 0.0))
        tot_arr += arr * win / win
        tot_dep += dep
        tot_blk += 0.0
        tot_wait_frac += per_pwait[-1]
    seeds_used = NS
    Wm = sum(per_W) / seeds_used
    Lm = sum(per_L) / seeds_used
    out = {
        "L": Lm, "W": Wm, "runtime_units": H, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour",
        "win": H - warm,
        "arr": tot_arr / seeds_used, "blk": tot_blk / seeds_used,
        "busy_frac": sum(per_busy) / seeds_used,
        "busy_util": sum(per_busy) / seeds_used,
        "dep": tot_dep / seeds_used,
        "dep_rate": tot_dep / seeds_used / (H - warm),
        "lam_eff": lam, "p_loss": 0.0,
        "p_wait": tot_wait_frac / seeds_used,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy, "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
