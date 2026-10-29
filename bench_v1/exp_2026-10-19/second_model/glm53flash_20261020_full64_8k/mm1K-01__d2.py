import json, argparse, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, K = 6.0, 10.0, 4
    if a.pert == "lam_up": lam = 7.2
    elif a.pert == "mu_up": mu = 12.0
    elif a.pert == "c_up": K = 5
    horizon = a.horizon
    warm = 0.25 * horizon
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot = dict(L=0.0, W=0.0, bf=0.0, pl=0.0, pw=0.0, arr=0.0, blk=0.0, dep=0.0)
    seeds_used = 0
    seed_list = []
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        dep_t = math.inf
        n = 0
        queue = []
        area_N = 0.0
        busy_t = 0.0
        arr_c = blk_c = dep_c = 0
        served = waited = 0
        soj_sum = 0.0
        soj_cnt = 0
        while True:
            nxt = min(next_arr, dep_t)
            if nxt > horizon:
                nxt = horizon
            dt = nxt - t
            if t >= warm:
                area_N += n * dt
                if n > 0:
                    busy_t += dt
            t = nxt
            if t >= horizon:
                break
            if next_arr <= dep_t:
                svc = rng.expovariate(mu)
                at = t
                next_arr = t + rng.expovariate(lam)
                if n >= K:
                    if t >= warm:
                        blk_c += 1
                else:
                    if t >= warm:
                        arr_c += 1
                        served += 1
                        if n > 0:
                            waited += 1
                    if n == 0:
                        dep_t = t + svc
                        cust = (at, svc)
                    else:
                        queue.append((at, svc))
                    n += 1
            else:
                at, svc = cust
                if t >= warm:
                    dep_c += 1
                    soj_sum += t - at
                    soj_cnt += 1
                n -= 1
                if queue:
                    cust = queue.pop(0)
                    dep_t = t + cust[1]
                else:
                    dep_t = math.inf
                    cust = None
        win = horizon - warm
        L = area_N / win
        bf = busy_t / win
        pl = blk_c / (arr_c + blk_c) if (arr_c + blk_c) > 0 else 0.0
        W = soj_sum / soj_cnt if soj_cnt > 0 else 0.0
        pw = waited / served if served > 0 else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot["L"] += L; tot["W"] += W; tot["bf"] += bf; tot["pl"] += pl; tot["pw"] += pw
        tot["arr"] += arr_c / win; tot["blk"] += blk_c / win; tot["dep"] += dep_c / win
        seeds_used += 1
        seed_list.append(seed)
    s = seeds_used
    L = tot["L"] / s; W = tot["W"] / s; bf = tot["bf"] / s
    pl = tot["pl"] / s; pw = tot["pw"] / s
    arr = tot["arr"] / s; blk = tot["blk"] / s; dep = tot["dep"] / s
    lam_eff = dep
    dep_rate = dep
    busy_util = L / 1
    out = {
        "L": L, "W": W, "busy_frac": bf, "p_loss": pl,
        "runtime_units": horizon, "seed_list": seed_list, "seeds_used": s,
        "time_unit": "hour", "win": horizon - warm,
        "arr": arr, "blk": blk, "busy_util": busy_util,
        "busy_occupied": bf, "dep": dep, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_wait": pw,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
