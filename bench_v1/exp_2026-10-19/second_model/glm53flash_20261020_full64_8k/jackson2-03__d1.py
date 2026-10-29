import argparse, heapq, json, math, random, sys

def run_seed(seed, H, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    fel = []
    cnt = 0
    heapq.heappush(fel, (rng.expovariate(lam), 0, cnt))
    cnt += 1
    n1 = 0; n2 = 0
    busy1 = False; busy2 = False
    q1 = []; q2 = []
    t0 = 0.25 * H
    area_L = 0.0; area_busy = 0.0; last = 0.0
    arr_w = 0; dep_w = 0; loss_w = 0
    sum_W = 0.0; nW = 0
    waited = 0; nw = 0
    dep1_at = None; dep2_at = None
    def integrate(now):
        nonlocal area_L, area_busy
        if now > last:
            dt = now - last
            a, b = max(last, t0), min(now, H)
            if b > a:
                seg = b - a
                area_L += n_total * seg
                area_busy += (int(busy1) + int(busy2)) * seg
            last = now
    n_total = 0
    while fel:
        ev = heapq.heappop(fel)
        t, kind, _ = ev
        if t > H:
            break
        integrate(t)
        n_total = n1 + n2
        if kind == 0:
            if t >= t0:
                arr_w += 1
            heapq.heappush(fel, (t + rng.expovariate(lam), 0, cnt)); cnt += 1
            s1 = rng.expovariate(mu); s2 = rng.expovariate(mu)
            job = [t, s1, s2]
            if not busy1:
                busy1 = True
                job.append(1)
                heapq.heappush(fel, (t + s1, 1, cnt)); cnt += 1
                job.append(t + s1)
                cur1 = job
            else:
                q1.append(job)
                cur1 = None
            n1 += 1
            if not busy2:
                pass
        elif kind == 1:
            s2 = cur1[2]
            n1 -= 1
            job2 = [cur1[0], cur1[2]]
            if not busy2:
                busy2 = True
                heapq.heappush(fel, (t + s2, 2, cnt)); cnt += 1
                job2.append(t + s2)
                cur2 = job2
            else:
                q2.append(job2)
                cur2 = None
            if q1:
                nxt = q1.pop(0)
                heapq.heappush(fel, (t + nxt[1], 1, cnt)); cnt += 1
                nxt.append(t + nxt[1])
                cur1 = nxt
            else:
                busy1 = False
                cur1 = None
        else:
            n2 -= 1
            started = cur2[2]
            if t >= t0:
                dep_w += 1
                sum_W += (started - cur2[0])
                nW += 1
                if started > cur2[0]:
                    waited += 1
                nw += 1
            if q2:
                nxt = q2.pop(0)
                heapq.heappush(fel, (t + nxt[1], 2, cnt)); cnt += 1
                nxt.append(t + nxt[1])
                cur2 = nxt
            else:
                busy2 = False
                cur2 = None
    win = H - t0
    L = area_L / win if win > 0 else 0.0
    busy_frac = area_busy / win if win > 0 else 0.0
    W = sum_W / nW if nW else 0.0
    p_wait = waited / nw if nw else 0.0
    dep_rate = dep_w / win if win > 0 else 0.0
    lam_eff = arr_w / win if win > 0 else 0.0
    return {"L": L, "W": W, "arr": arr_w, "dep": dep_w, "blk": loss_w,
            "busy_frac": busy_frac / 2.0, "busy_util": busy_frac / 2.0,
            "dep_rate": dep_rate, "lam_eff": lam_eff, "p_loss": 0.0,
            "p_wait": p_wait, "win": win}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu = 4.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    if a.pert == "mu_up": mu *= 1.1
    if a.pert == "c_up": pass
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    arrs = []; deps = []; blks = []; drs = []; les = []
    seed_list = []
    for k in range(a.seeds):
        s = a.seed_start + k
        r = run_seed(s, a.horizon, lam, mu)
        seed_list.append(s)
        per_L.append(r["L"]); per_W.append(r["W"])
        per_bf.append(r["busy_frac"]); per_pl.append(r["p_loss"])
        per_pw.append(r["p_wait"])
        arrs.append(r["arr"]); deps.append(r["dep"]); blks.append(r["blk"])
        drs.append(r["dep_rate"]); les.append(r["lam_eff"])
    n = len(seed_list)
    def avg(x): return sum(x) / n if n else 0.0
    out = {
        "L": avg(per_L), "W": avg(per_W),
        "runtime_units": a.horizon * n,
        "seed_list": seed_list, "seeds_used": n,
        "time_unit": "hour", "win": a.horizon * 0.75,
        "arr": avg(arrs), "blk": avg(blks), "dep": avg(deps),
        "busy_frac": avg(per_bf), "busy_util": avg(per_bf),
        "dep_rate": avg(drs), "lam_eff": avg(les),
        "p_loss": avg(per_pl), "p_wait": avg(per_pw),
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
