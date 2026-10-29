import argparse, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, cap = 9.0, 10.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": cap += 1
    H = a.horizon
    warm = 0.25 * H
    win = H - warm
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seeds_used = 0
    seed_list = []
    tot_arr = tot_blk = tot_dep = 0.0
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        t = 0.0
        n = 0
        t_last = 0.0
        tna = rng.expovariate(lam)
        tnd = math.inf
        arrive_t = {}
        L_area = 0.0
        B_area = 0.0
        cnt_arr = cnt_blk = cnt_dep = 0
        sumW = 0.0
        waited = served = 0
        while True:
            if tna <= tnd and tna <= H:
                dt = tna - t_last
                if tna > warm:
                    L_area += n * dt
                    B_area += (1.0 if n > 0 else 0.0) * dt
                t_last = tna
                t = tna
                cnt_arr += 1
                if n >= cap:
                    cnt_blk += 1
                    tna = t + rng.expovariate(lam)
                else:
                    waited += 1
                    arrive_t[waited] = t
                    st = rng.expovariate(mu)
                    if n == 0:
                        tnd = t + st
                    n += 1
                    arrive_t[n] = (t, st)
                    tna = t + rng.expovariate(lam)
            elif tnd <= H:
                dt = tnd - t_last
                if tnd > warm:
                    L_area += n * dt
                    B_area += (1.0 if n > 0 else 0.0) * dt
                t_last = tnd
                t = tnd
                cnt_dep += 1
                served += 1
                at, st = arrive_t[n]
                del arrive_t[n]
                if t > warm:
                    sumW += (t - at) * 60.0
                n -= 1
                if n > 0:
                    tnd = t + arrive_t[n][1]
                else:
                    tnd = math.inf
            else:
                dt = H - t_last
                if H > warm:
                    L_area += n * dt
                    B_area += (1.0 if n > 0 else 0.0) * dt
                break
        seeds_used += 1
        seed_list.append(seed)
        tot_arr += cnt_arr
        tot_blk += cnt_blk
        tot_dep += cnt_dep
        per_L.append(L_area / win)
        per_W.append(sumW / served if served else 0.0)
        per_bf.append(B_area / win)
        per_pl.append(cnt_blk / cnt_arr if cnt_arr else 0.0)
        per_pw.append(waited / cnt_arr if cnt_arr else 0.0)
    S = seeds_used
    L = sum(per_L) / S
    W = sum(per_W) / S
    bf = sum(per_bf) / S
    pl = sum(per_pl) / S
    pw = sum(per_pw) / S
    arr = tot_arr / S
    blk = tot_blk / S
    dep = tot_dep / S
    dep_rate = dep / win
    lam_eff = arr / win
    out = {
        "L": L, "W": W, "busy_frac": bf, "p_loss": pl,
        "runtime_units": win * S, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour", "win": win,
        "arr": arr, "blk": blk, "busy_util": bf, "busy_occupied": bf,
        "dep": dep, "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_wait": pw,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
