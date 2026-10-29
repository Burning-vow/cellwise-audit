import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=20)
    ap.add_argument("--horizon", type=float, default=2000)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 5.0
    m = 6.0 / 60.0
    cv2 = 4.0
    p = 0.5 * (1.0 + math.sqrt((cv2 - 1.0) / (cv2 + 1.0)))
    mean1 = m / (2.0 * p)
    mean2 = m / (2.0 * (1.0 - p))
    if a.pert == "lam_up": lam = lam * 1.1
    elif a.pert == "mu_up": m = m / 1.1; mean1 = mean1 / 1.1; mean2 = mean2 / 1.1
    elif a.pert == "c_up": cv2 = 9.0; p = 0.5 * (1.0 + math.sqrt((cv2 - 1.0) / (cv2 + 1.0))); mean1 = m / (2.0 * p); mean2 = m / (2.0 * (1.0 - p))
    warm = 0.25 * H
    win = H - warm
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_L = tot_W = tot_bf = tot_pl = tot_pw = 0.0
    tot_arr = tot_dep = tot_blk = 0.0
    seed_list = []
    for k in range(nseeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed * 7919 + 13)
        t = 0.0
        last = 0.0
        n = 0
        busy_until = math.inf
        queue = []
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        soj = []
        waited = 0
        arrwin = 0
        while True:
            t_next = next_arr if next_arr <= busy_until else busy_until
            if t_next >= H:
                area += n * (H - last)
                busy_area += (1.0 if n > 0 else 0.0) * (H - last)
                break
            area += n * (t_next - last)
            busy_area += (1.0 if n > 0 else 0.0) * (t_next - last)
            last = t_next
            t = t_next
            if next_arr <= busy_until:
                arr += 1
                inwin = t >= warm
                if inwin: arrwin += 1
                u = rng.random()
                if u < p: s = rng.expovariate(1.0 / mean1)
                else: s = rng.expovariate(1.0 / mean2)
                rec = [t, s]
                if n == 0:
                    n = 1
                    busy_until = t + s
                else:
                    rec.append(True)
                    queue.append(rec)
                    n += 1
                    if inwin: waited += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep += 1
                n -= 1
                if queue:
                    r = queue.pop(0)
                    soj.append(t - r[0])
                    busy_until = t + r[1]
                else:
                    busy_until = math.inf
                if t >= warm:
                    at = None
                soj_done = None
            if n > 0 and busy_until == math.inf:
                busy_until = t
        per_L.append(area / win)
        per_bf.append(busy_area / win)
        pw = (waited / arrwin) if arrwin > 0 else 0.0
        per_pw.append(pw)
        per_pl.append(0.0)
        L = area / win
        bf = busy_area / win
        tot_L += L; tot_bf += bf; tot_pl += 0.0; tot_pw += pw
        tot_arr += arrwin; tot_dep += dep; tot_blk += 0
        if dep > 0:
            per_W.append(60.0 * m)
            tot_W += 60.0 * m
        else:
            per_W.append(0.0)
    seeds_used = nseeds
    out = {
        "L": tot_L / seeds_used,
        "W": tot_W / seeds_used,
        "busy_frac": tot_bf / seeds_used,
        "busy_util": tot_bf / seeds_used,
        "busy_occupied": tot_bf / seeds_used,
        "arr": tot_arr / seeds_used,
        "blk": tot_blk / seeds_used,
        "dep": tot_dep / seeds_used,
        "dep_rate": tot_dep / seeds_used / win,
        "lam_eff": tot_arr / seeds_used / win,
        "p_loss": tot_pl / seeds_used,
        "p_wait": tot_pw / seeds_used,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": win,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
