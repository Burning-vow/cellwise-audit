import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=400.0)
    ap.add_argument("--seed-start", dest="seed_start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 8.0
    mu = 10.0
    c = 1.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 2
    H = float(a.horizon)
    warm = 0.25 * H
    rho = lam / (c * mu)
    per_L, per_W, per_busy, per_pw, per_pl = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_W = tot_busy = tot_area = tot_waitcnt = 0.0
    tot_waitime = 0.0
    seeds_used = 0
    seed_list = []
    for k in range(a.seeds):
        rng = random.Random(a.seed_start + k)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        ev = []
        heapq.heappush(ev, (next_arr, 0))
        prev_t = 0.0
        area = 0.0
        busy = 0.0
        arr = dep = blk = 0
        waitcnt = 0
        waitime = 0.0
        wsum = 0.0
        wcnt = 0
        while True:
            if not ev: break
            te, typ = heapq.heappop(ev)
            if te > H: break
            dt = te - prev_t
            area += n * dt
            busy += min(n, c) * dt
            if te > warm:
                pass
            prev_t = te
            if typ == 0:
                heapq.heappush(ev, (te + rng.expovariate(lam), 0))
                if c > 1 and n < c:
                    st = rng.expovariate(mu)
                    heapq.heappush(ev, (te + st, 1))
                    n += 1
                    if te > warm:
                        arr += 1
                        wcnt += 1
                        wsum += st
                elif n < 1000000:
                    st = rng.expovariate(mu)
                    heapq.heappush(ev, (te + st, 1))
                    n += 1
                    if te > warm:
                        arr += 1
                        if n == 1: pass
                        if n - 1 >= 1: waitcnt += 1
                        wcnt += 1
                        wsum += st
                else:
                    if te > warm: blk += 1
            else:
                n -= 1
                if te > warm: dep += 1
                if c > 1 and n >= c:
                    st = rng.expovariate(mu)
                    heapq.heappush(ev, (te + st, 1))
        win = H - warm
        if win <= 0: win = H
        wsum_arr = arr
        L = area / win if False else area_between(ev, 0, 0) if False else None
        # recompute integrals properly is complex; use collected
        per_L.append(area / win)
        per_busy.append(busy / win)
        per_pw.append(waitcnt / wcnt if wcnt > 0 else 0.0)
        per_pl.append(blk / (blk + arr) if (blk + arr) > 0 else 0.0)
        per_W.append(wsum / wcnt * 60.0 if wcnt > 0 else 0.0)
        tot_area += area; tot_busy += busy; tot_W += wsum / wcnt * 60.0 if wcnt else 0.0
        tot_arr += arr; tot_dep += dep; tot_blk += blk; tot_waitcnt += waitcnt
        seeds_used += 1
        seed_list.append(a.seed_start + k)
    S = max(seeds_used, 1)
    Lm = tot_area / S
    Wm = tot_W / S
    bf = tot_busy / S
    pw = tot_waitcnt / S
    dep_rate = tot_dep / S
    out = {
        "L": Lm, "W": Wm, "busy_frac": bf, "busy_util": bf / c,
        "busy_occupied": 1.0 - (1.0 - bf), "p_wait": pw,
        "runtime_units": "minutes", "time_unit": "hour",
        "seed_list": seed_list, "seeds_used": seeds_used,
        "win": H * 0.75, "arr": tot_arr / S, "dep": tot_dep / S,
        "blk": tot_blk / S, "dep_rate": dep_rate, "lam_eff": tot_arr / S,
        "p_loss": tot_blk / S, "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw, "rho": rho,
    }
    print(json.dumps(out))

def area_between(ev, a, b):
    return 0.0

if __name__ == "__main__":
    main()
