import argparse, heapq, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); s0 = int(a.seed_start)
    lam, mu, c, K = 6.0, 5.0, 2, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = H * 0.25; win = H - warm
    per = []
    seeds_used = 0
    seed_list = []
    for si in range(n_seeds):
        seed = s0 + si
        rng = random.Random(seed)
        t = 0.0; N = 0
        ev = []; heapq.heapify(ev)
        heapq.heappush(ev, (rng.expovariate(lam), "arr", 0.0))
        t_area = 0.0; t_busy = 0.0; areaL = 0.0; areaBusy = 0.0; areaUtil = 0.0
        last = 0.0
        arr = dep = blk = waits = waits_n = 0.0
        t0 = None
        def integ(tnow):
            nonlocal t_area, areaL, areaBusy, areaUtil, last, t0
            dt = tnow - last
            if tnow > warm and last < warm:
                if t0 is None: t0 = warm
                frac = (tnow - warm) / dt if dt > 0 else 1.0
                areaL += N * dt * frac
                areaBusy += (1.0 if N > 0 else 0.0) * dt * frac
                areaUtil += min(N, c) * dt * frac
            elif tnow > warm:
                if t0 is None: t0 = last
                areaL += N * dt; areaBusy += (1.0 if N > 0 else 0.0) * dt; areaUtil += min(N, c) * dt
            last = tnow
        while ev and t < H:
            t, typ, extra = heapq.heappop(ev)
            integ(t)
            if typ == "arr":
                if N < K:
                    N += 1
                    if t > warm:
                        arr += 1
                        if N > c: waits_n += 1
                    st = rng.expovariate(mu)
                    if N <= c:
                        heapq.heappush(ev, (t + st, "dep", st))
                    else:
                        nq = N - c
                        qlist = [(te, s, "dep", x) for (te, ty, x) in ev if ty == "dep"]
                        heapq.heappush(ev, (math.inf, "dep", st))
                else:
                    if t > warm: blk += 1
                heapq.heappush(ev, (t + rng.expovariate(lam), "arr", 0.0))
            else:
                N -= 1
                if t > warm: dep += 1
                if N >= c:
                    nd = sum(1 for e in ev if e[1] == "dep")
                    if nd < N:
                        pass
            if N > c:
                nd = sum(1 for e in ev if e[1] == "dep" and e[0] < math.inf)
                for i, e in enumerate(ev):
                    if e[1] == "dep" and e[0] == math.inf:
                        ev[i] = (t + e[2], "dep", e[2])
                        heapq._siftdown(ev, 0, len(ev) - 1)
                        break
            t_area += 1
        if t0 is not None and last > warm:
            w = last - warm
            per.append({"L": areaL / w, "busy": areaBusy / w, "util": areaUtil / w / c,
                        "arr": arr, "dep": dep, "blk": blk, "w": w})
        seeds_used += 1
        seed_list.append(seed)
    import statistics
    def m(k): return statistics.fmean([p[k] for p in per]) if per else 0.0
    L = m("L"); dep_r = m("dep") / win if win > 0 else 0.0
    W = dep_r and (m("arr") * L / max(dep_r, 1e-12)) / dep_r if False else (L / dep_r * 60.0 if dep_r > 0 else 0.0)
    W = (L / dep_r) * 60.0 if dep_r > 0 else 0.0
    lam_eff = dep_r
    p_loss = m("blk") / (m("arr") + m("blk")) if (m("arr") + m("blk")) > 0 else 0.0
    Wq = (m("util") * 0 + (L - m("util") * c) / lam_eff) if lam_eff > 0 else 0.0
    p_wait = max(0.0, (L - m("util") * c) / max(m("arr"), 1e-12)) if m("arr") > 0 else 0.0
    print(json.dumps({
        "L": L, "W": W, "busy_frac": m("busy"), "p_loss": p_loss,
        "runtime_units": len(seed_list), "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "hour", "win": win, "arr": m("arr"), "blk": m("blk"),
        "busy_util": m("util"), "busy_occupied": m("busy"), "dep": m("dep"),
        "dep_rate": dep_r, "lam_eff": lam_eff, "p_wait": p_wait,
        "per_seed_L": [p["L"] for p in per],
        "per_seed_W": [(p["L"] / (p["dep"] / p["w"]) * 60.0 if p["dep"] > 0 else 0.0) for p in per],
        "per_seed_busy_frac": [p["busy"] for p in per],
        "per_seed_p_loss": [(p["blk"] / (p["arr"] + p["blk"]) if (p["arr"] + p["blk"]) > 0 else 0.0) for p in per],
        "per_seed_p_wait": [p["wait"] for p in per],
    }))

if __name__ == "__main__":
    main()
