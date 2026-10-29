import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    c, K = 2, 4
    lam, mu = 8.0, 5.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    tu = "minute"
    lam = lam / 60.0
    T = a.horizon if tu == "minute" else a.horizon
    warm = 0.25 * T
    seed_list, per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], [], []
    arrs, deps, blks, busy_utils = [], [], [], []
    for si in range(a.seeds):
        seed = a.seed_start + si
        rng = random.Random(seed)
        seed_list.append(seed)
        t = 0.0
        n = 0
        events = []
        def sch(t_, kind):
            if kind == "arr":
                dt = rng.expovariate(lam)
            else:
                dt = rng.expovariate(mu)
            heapq.heappush(events, (t_ + dt, kind, seq_c[0]))
            seq_c[0] += 1
        seq_c = [0]
        sch(t, "arr")
        A = 0.0; B = 0.0
        Aarr = 0.0; dep_c = 0; blk_c = 0
        wsum = 0.0; wcnt = 0; waitcnt = 0; arrcnt = 0
        prev = 0.0
        busy_time = 0.0
        while t < T:
            t2, kind, _ = heapq.heappop(events)
            if t2 > T:
                seg = T - prev
                if prev >= warm:
                    A += n * seg; B += min(n, c) * seg; Aarr += n * 0
                    busy_time += (1.0 if n > 0 else 0.0) * seg
                t = T
                break
            seg = t2 - prev
            if prev >= warm:
                A += n * seg
                B += min(n, c) * seg
                busy_time += (1.0 if n > 0 else 0.0) * seg
            t = t2; prev = t
            if kind == "arr":
                if prev >= warm:
                    arrcnt += 1
                if n < K:
                    n += 1
                    heapq.heappush(events, (t + rng.expovariate(mu), "dep", seq_c[0])); seq_c[0] += 1
                    if prev >= warm:
                        enter_t[t if False else 0] = t
                    recs.append(t) if False else None
                    if prev >= warm:
                        pass
                    wait_zero = (n <= c)
                    if prev >= warm:
                        if not wait_zero: pass
                    if prev >= warm and n > c:
                        waitcnt += 1
                    if prev >= warm:
                        arrival_times.append(t)
                else:
                    if prev >= warm:
                        blk_c += 1
                heapq.heappush(events, (t + rng.expovariate(lam), "arr", seq_c[0])); seq_c[0] += 1
            else:
                n -= 1
                dep_c += 1 if prev >= warm else 0
                if arrival_times:
                    at = arrival_times.pop(0)
                    if prev >= warm:
                        wsum += (t - at); wcnt += 1
        win = T - warm
        L = A / win
        busy_util = B / (win * c)
        busy_frac = busy_time / win
        p_loss = blk_c / arrcnt if arrcnt else 0.0
        W = wsum / wcnt if wcnt else 0.0
        p_wait = waitcnt / arrcnt if arrcnt else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(busy_frac)
        per_pl.append(p_loss); per_pw.append(p_wait)
        arrs.append(arrcnt / win * 60.0 if tu == "minute" else arrcnt / win)
        deps.append(dep_c / win * 60.0 if tu == "minute" else dep_c / win)
        blks.append(blk_c / win * 60.0 if tu == "minute" else blk_c / win)
        busy_utils.append(busy_util)
        recs.clear() if False else None
    m = len(per_L)
    out = {
        "L": sum(per_L)/m, "W": sum(per_W)/m, "busy_frac": sum(per_bf)/m,
        "p_loss": sum(per_pl)/m, "runtime_units": tu, "seed_list": seed_list,
        "seeds_used": m, "time_unit": tu, "win": (T - warm),
        "arr": sum(arrs)/m, "blk": sum(blks)/m, "busy_util": sum(busy_utils)/m,
        "dep": sum(deps)/m, "dep_rate": sum(deps)/m,
        "lam_eff": sum(arrs)/m * (1 - sum(per_pl)/m),
        "p_wait": sum(per_pw)/m,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
        "busy_occupied": sum(per_bf)/m,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
