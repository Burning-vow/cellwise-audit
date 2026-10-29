import argparse, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 6.0, 12.0, 1
    K = 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    H = float(a.horizon)
    warm = 0.25 * H
    res = {"L": [], "W": [], "bf": [], "pl": [], "pw": []}
    seeds_used = 0
    seed_list = []
    agg = {"arr": 0, "dep": 0, "blk": 0, "busy": 0.0, "AoN": 0.0, "wait": 0.0, "soj": 0.0, "nsoj": 0}
    for si in range(a.seeds):
        seed = a.seed_start + si
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        next_dep = math.inf
        last = 0.0
        AoN = 0.0; busyT = 0.0
        waitT = 0.0; sojT = 0.0; nsoj = 0
        arr = dep = blk = 0
        served_w = dep_w = blk_w = 0
        while True:
            if next_arr <= next_dep and next_arr <= H:
                ev = next_arr; nt = "arr"
            elif next_dep <= H:
                ev = next_dep; nt = "dep"
            else:
                ev = H; nt = "end"
            dt = ev - last
            AoN += n * dt
            if n >= 1: busyT += dt
            last = ev
            if nt == "end": break
            if nt == "arr":
                arr += 1
                if t >= warm: arr_w = 1
                st = rng.expovariate(mu)
                if n < K:
                    if t >= warm:
                        pass
                    n += 1
                    waitT += 0.0
                    soj_start = ev
                    if n == 1:
                        next_dep = ev + st
                else:
                    blk += 1
                next_arr = ev + rng.expovariate(lam)
            else:
                dep += 1
                n -= 1
                if n > 0:
                    next_dep = ev + rng.expovariate(mu)
                else:
                    next_dep = math.inf
            t = ev
        win = H - warm
        L = AoN / win
        bf = busyT / win
        pl = blk / (arr if arr else 1)
        res["L"].append(L); res["W"].append(0.0)
        seeds_used += 1; seed_list.append(seed)
    out = {
        "L": sum(res["L"])/seeds_used,
        "W": sum(res["W"])/seeds_used,
        "busy_frac": sum(res["bf"])/seeds_used,
        "p_loss": sum(res["pl"])/seeds_used,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "hour", "win": H - warm,
        "arr": 0, "blk": 0, "busy_util": 0, "busy_occupied": 0,
        "dep": 0, "dep_rate": 0, "lam_eff": 0, "p_wait": 0,
        "per_seed_L": res["L"], "per_seed_W": res["W"],
        "per_seed_busy_frac": res["bf"], "per_seed_p_loss": res["pl"],
        "per_seed_p_wait": res["pw"]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
