import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=100000)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 6.0
    K = 6
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        K = 7

    H = a.horizon
    warm = 0.25 * H
    win = H - warm
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_blk = tot_dep = 0.0

    for seed in seeds:
        rng = random.Random(seed)
        t = 0.0
        n = 0
        ta = rng.expovariate(lam)
        td = math.inf
        svc = {}
        ticket = 0
        area = 0.0
        busy = 0.0
        arr = blk = dep = waited = 0

        while t < H:
            tn = min(ta, td)
            dt = tn - t
            if tn > warm:
                area += n * dt
                if n > 0:
                    busy += dt
            t = tn
            if ta <= td:
                if t > warm:
                    arr += 1
                if n < K:
                    if n > 0 and t > warm:
                        waited += 1
                    n += 1
                    ticket += 1
                    svc[ticket] = rng.expovariate(mu)
                    if ticket == 1 or svc[ticket] < td - t:
                        td = t + svc[ticket]
                else:
                    if t > warm:
                        blk += 1
                ta = t + rng.expovariate(lam)
            else:
                n -= 1
                if t > warm:
                    dep += 1
                if n > 0:
                    nxt = min(svc.values())
                    td = t + nxt
                    for k in list(svc):
                        if svc[k] == nxt:
                            del svc[k]
                            break
                else:
                    td = math.inf

        served = max(dep, 1)
        L = area / win
        W = area / served
        bf = busy / win
        p_loss = blk / max(arr + blk, 1)
        p_wait = waited / max(served, 1)
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(p_loss)
        per_pw.append(p_wait)
        tot_arr += arr
        tot_blk += blk
        tot_dep += dep

    m = len(seeds)
    lam_eff = tot_dep / (m * win)
    print(json.dumps({
        "L": sum(per_L) / m,
        "W": sum(per_W) / m,
        "busy_frac": sum(per_bf) / m,
        "p_loss": sum(per_pl) / m,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": m,
        "time_unit": "minute",
        "win": win,
        "arr": tot_arr / m,
        "blk": tot_blk / m,
        "dep": tot_dep / m,
        "dep_rate": lam_eff * 60.0,
        "lam_eff": lam_eff,
        "p_wait": sum(per_pw) / m,
        "busy_util": sum(per_bf) / m,
        "busy_occupied": sum(per_bf) / m,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }))

if __name__ == "__main__":
    main()
