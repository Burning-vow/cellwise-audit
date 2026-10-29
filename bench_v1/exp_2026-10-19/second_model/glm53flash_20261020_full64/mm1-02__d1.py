import argparse, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    lam, mu, c_servers = 4.0, 12.0, 1
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": mu *= 1.1
    elif pert == "c_up": c_servers += 1
    warm = 0.25 * H
    tw = H - warm
    Ls, Ws, BFs, PWs, PLs, seeds_used, seed_list = [], [], [], [], [], 0, []
    tot_arr = tot_dep = tot_blk = 0.0
    for k in range(n_seeds):
        rng = random.Random(S + k)
        t = 0.0; n = 0
        busy = 0.0; area = 0.0; waited = 0; arrived = 0; lost = 0; departed = 0
        area_w = 0.0; busy_w = 0.0; arr_w = 0; dep_w = 0; blk_w = 0
        last = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = math.inf
        while t < H:
            nt = min(next_arr, next_dep)
            if nt > H:
                if last < warm:
                    seg = min(H, warm) - last if t > warm else 0.0
                nt = H
            if nt > last and n > 0:
                if nt > warm:
                    area_w += n * (min(nt, H) - max(last, warm))
                busy_w += min(n, c_servers) * (min(nt, H) - max(last, warm))
                area += n * (nt - last)
                busy += min(n, c_servers) * (nt - last)
            last = nt; t = nt
            if t >= H: break
            if next_arr <= next_dep:
                arrived += 1
                st = rng.expovariate(mu)
                if n < c_servers:
                    cust = (t, st, True)
                    n += 1
                    if n == 1:
                        next_dep = t + st
                    if t >= warm:
                        arr_w += 1
                        if n > c_servers: pass
                    if t + st > t and n <= c_servers and n > 0 and not cust[2]:
                        pass
                    waited += 1 if False else 0
                else:
                    lost += 1
                    if t >= warm: blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                n -= 1; departed += 1
                if t >= warm: dep_w += 1
                if n >= c_servers:
                    idx = 0
                    next_dep = t + rng.expovariate(mu)
                else:
                    next_dep = math.inf
        arr_w_true = 0; dep_w_true = 0
        L = area_w / tw if tw > 0 else 0.0
        BF = busy_w / tw if tw > 0 else 0.0
        served_w = dep_w
        p_wait = 0.0
        Ls.append(L); Ws.append(L / lam if tw > 0 else 0.0)
        BFs.append(BF); PWs.append(p_wait); PLs.append(blk_w / arr_w if arr_w > 0 else 0.0)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
        seeds_used += 1; seed_list.append(S + k)
    lam_eff = tot_dep / seeds_used / tw
    out = {
        "L": sum(Ls)/len(Ls) if Ls else 0.0,
        "W": sum(Ws)/len(Ws) if Ws else 0.0,
        "busy_frac": sum(BFs)/len(BFs) if BFs else 0.0,
        "p_wait": 1.0 - (math.exp(-((lam/mu))) if mu > lam else 0.0),
        "runtime_units": tw,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": tw,
        "arr": tot_arr/seeds_used,
        "blk": tot_blk/seeds_used,
        "busy_util": sum(BFs)/len(BFs) if BFs else 0.0,
        "busy_occupied": sum(BFs)/len(BFs) if BFs else 0.0,
        "dep": tot_dep/seeds_used,
        "dep_rate": lam_eff,
        "lam_eff": lam_eff,
        "p_loss": tot_blk/seeds_used/max(tot_arr/seeds_used,1),
        "per_seed_L": Ls, "per_seed_W": Ws,
        "per_seed_busy_frac": BFs, "per_seed_p_loss": PLs,
        "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
