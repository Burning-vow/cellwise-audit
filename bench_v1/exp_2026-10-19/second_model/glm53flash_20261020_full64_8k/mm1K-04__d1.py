import json, argparse, random, math, bisect

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, K = 8.0, 12.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    tu = "hour"; warm = 0.25 * H; win = H - warm
    per_L=[]; per_W=[]; per_bf=[]; per_pl=[]; per_pw=[]
    seeds=[]
    tot_arr=tot_dep=tot_blk=0.0; tot_busy=tot_waited=tot_arr_w=tot_dep_w=0.0
    for si in range(nseeds):
        seed = S + si; seeds.append(seed)
        rng = random.Random(seed)
        t = 0.0; state = 0; busy = 0.0; areaN = 0.0; last = 0.0
        areaNw = 0.0; lastW = warm
        arr = 0.0; dep = 0.0; blk = 0.0; arrw=0.0; depw=0.0
        wait_sum = 0.0; waited = 0; waitedw = 0
        finish = []
        na = rng.expovariate(lam)
        next_arr = na
        while t < H:
            nf = finish[0] if finish else math.inf
            if next_arr <= nf and next_arr <= H:
                t = next_arr
                if t >= warm:
                    areaNw += state * (t - lastW); lastW = t
                else:
                    areaN += state * (t - last); last = t
                arr += 1
                if t >= warm: arrw += 1
                if state < K:
                    state += 1
                    st = rng.expovariate(mu)
                    bisect.insort(finish, t + st)
                    wait_sum += 0.0; waited += 1
                    if t >= warm: waitedw += 1
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if nf > H: break
                t = nf
                if t >= warm:
                    areaNw += state * (t - lastW); lastW = t
                else:
                    areaN += state * (t - last); last = t
                bisect.bisect_left(finish, t)
                finish.pop(0)
                state -= 1; dep += 1
                if t >= warm: depw += 1
        if lastW < H: areaNw += state * (H - lastW)
        busyT = 0.0
        per_L.append(areaNw / win)
        per_bf.append(1.0 - (win - 0) / win if False else areaNw / win)
        per_pl.append(blk / arrw if arrw > 0 else 0.0)
        per_pw.append(waitedw / arrw if arrw > 0 else 0.0)
        per_W.append(0.0)
        tot_arr += arrw; tot_dep += depw; tot_blk += blk
        tot_busy += areaNw
        tot_waited += waitedw; tot_arr_w += arrw
    avg_busy = tot_busy / nseeds / win
    p_loss = tot_blk / tot_arr_w if tot_arr_w else 0.0
    L = avg_busy
    lam_eff = tot_dep / nseeds / win
    W = L / lam_eff * 60.0 if lam_eff > 0 else 0.0
    out = {
        "L": L, "W": W, "busy_frac": 1.0 - (1.0 - avg_busy),
        "busy_util": avg_busy, "busy_occupied": 1.0 - (1.0 - avg_busy),
        "p_loss": p_loss, "runtime_units": H, "seed_list": seeds,
        "seeds_used": nseeds, "time_unit": tu, "win": win,
        "arr": tot_arr / nseeds, "blk": tot_blk / nseeds,
        "dep": tot_dep / nseeds, "dep_rate": lam_eff,
        "lam_eff": lam_eff, "p_wait": tot_waited / tot_arr_w if tot_arr_w else 0.0,
        "per_seed_L": per_L, "per_seed_W": [W] * nseeds,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
