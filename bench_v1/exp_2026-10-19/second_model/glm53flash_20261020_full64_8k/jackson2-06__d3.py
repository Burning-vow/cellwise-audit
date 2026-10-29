import argparse, json, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=200)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); s0 = int(a.seed_start)
    lam = 6.0
    m1 = 7.5 / 60.0
    m2 = 5.0 / 60.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        m1 /= 1.1; m2 /= 1.1
    elif a.pert == "c_up":
        pass
    w = 0.25 * H
    win = H - w
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot_L = tot_W = tot_bf = tot_pw = 0.0
    tot_dep = 0.0
    n_done = 0
    for k in range(n_seeds):
        seed = s0 + k
        rng = random.Random(seed)
        t = 0.0
        jobs = []
        while True:
            t += rng.expovariate(lam)
            if t >= H:
                break
            s1 = rng.expovariate(1.0 / m1)
            s2 = rng.expovariate(1.0 / m2)
            jobs.append((t, s1, s2))
        f1 = 0.0; f2 = 0.0
        events = []
        Wsum = 0.0; cnt = 0; nowait = 0
        b1 = 0.0; b2 = 0.0
        dep = 0
        for arr, s1, s2 in jobs:
            st1 = max(arr, f1); d1 = st1 + s1; f1 = d1
            st2 = max(d1, f2); d2 = st2 + s2; f2 = d2
            events.append((arr, 1.0))
            events.append((d1, -1.0))
            events.append((d1, 1.0))
            if d2 <= H:
                events.append((d2, -1.0))
                if d2 >= w:
                    dep += 1
            if arr >= w:
                soj = (d2 - arr) * 60.0
                Wsum += soj; cnt += 1
                if st2 <= arr + 1e-12 and st1 <= arr + 1e-12:
                    nowait += 1
            lo = max(arr, w); hi = min(d1, H)
            if hi > lo: b1 += hi - lo
            lo = max(d1, w); hi = min(d2, H)
            if hi > lo: b2 += hi - lo
        events.sort(key=lambda e: e[0])
        n_at_w = sum(d for tt, d in events if tt <= w)
        area = 0.0; cur = n_at_w; prev = w
        for tt, d in events:
            if tt >= H: break
            if tt > w:
                area += cur * (min(tt, H) - prev)
                prev = min(tt, H)
            cur += d
        if prev < H:
            area += cur * (H - prev)
        L = area / win if win > 0 else 0.0
        W = Wsum / cnt if cnt else 0.0
        bf = (b1 + b2) / (2.0 * win) if win > 0 else 0.0
        pl = 0.0
        pw = 1.0 - nowait / cnt if cnt else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        seed_list.append(seed)
        tot_L += L; tot_W += W; tot_bf += bf; tot_pw += pw
        tot_dep += dep
        n_done += 1
    out = {
        "L": tot_L / n_done,
        "W": tot_W / n_done,
        "runtime_units": H * n_done,
        "seed_list": seed_list,
        "seeds_used": n_done,
        "time_unit": "hour",
        "win": win,
        "arr": (tot_dep / n_done),
        "blk": 0.0,
        "busy_frac": tot_bf / n_done,
        "busy_util": tot_bf / n_done,
        "dep": tot_dep / n_done,
        "dep_rate": (tot_dep / n_done) / win,
        "lam_eff": (tot_dep / n_done) / win,
        "p_loss": 0.0,
        "p_wait": tot_pw / n_done,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
