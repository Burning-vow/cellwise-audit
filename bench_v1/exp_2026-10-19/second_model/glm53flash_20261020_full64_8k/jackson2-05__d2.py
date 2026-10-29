import argparse, json, math, random, sys

def run_seed(seed, H, lam, mu1, mu2):
    rng = random.Random(seed)
    INF = math.inf
    warm = 0.25 * H
    t = 0.0
    next_arr = rng.expovariate(lam)
    q1 = []; q2 = []
    s1busy = None; s2busy = None
    nd1 = INF; nd2 = INF
    n1 = 0; n2 = 0
    areaL = 0.0; b1 = 0.0; b2 = 0.0
    arr_w = 0; dep_w = 0; blk_w = 0
    wait_n = 0; wsum = 0.0; wcnt = 0

    def seg(a, b, val, acc):
        lo = max(a, warm); hi = min(b, H)
        if hi > lo:
            acc[0] += val * (hi - lo)

    while True:
        tnext = min(next_arr, nd1, nd2)
        accL = [areaL]; acc1 = [b1]; acc2 = [b2]
        seg(t, tnext, n1 + n2, accL)
        seg(t, tnext, 1.0 if s1busy else 0.0, acc1)
        seg(t, tnext, 1.0 if s2busy else 0.0, acc2)
        areaL, b1, b2 = accL[0], acc1[0], acc2[0]
        t = tnext
        if t == next_arr:
            if t > H:
                next_arr = INF
            else:
                job = [t, rng.expovariate(mu1), rng.expovariate(mu2)]
                if t >= warm:
                    arr_w += 1
                    if n1 > 0:
                        wait_n += 1
                q1.append(job)
                n1 += 1
                if s1busy is None:
                    s1busy = q1.pop(0)
                    n1 -= 1
                    nd1 = t + s1busy[1]
                next_arr = t + rng.expovariate(lam) if t < H else INF
        elif t == nd1:
            job = s1busy
            q2.append(job)
            n2 += 1
            if s2busy is None:
                s2busy = q2.pop(0)
                n2 -= 1
                nd2 = t + s2busy[2]
            if q1:
                s1busy = q1.pop(0)
                nd1 = t + s1busy[1]
            else:
                s1busy = None
                nd1 = INF
        else:
            job = s2busy
            if t >= warm and job[0] >= warm:
                dep_w += 1
                wsum += t - job[0]
                wcnt += 1
            elif t >= warm:
                dep_w += 1
            if q2:
                s2busy = q2.pop(0)
                nd2 = t + s2busy[2]
            else:
                s2busy = None
                nd2 = INF
        if next_arr == INF and nd1 == INF and nd2 == INF and not q1 and not q2 and s1busy is None and s2busy is None:
            break
    win = H - warm
    W = (wsum / wcnt * 60.0) if wcnt > 0 else 0.0
    L = areaL / win if win > 0 else 0.0
    return L, W, arr_w, dep_w, blk_w, b1 / win, b2 / win, (wait_n / arr_w if arr_w else 0.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 8.0, 10.0
    if a.pert == "lam_up":
        lam *= 1.2
    elif a.pert == "mu_up":
        mu1 *= 1.2; mu2 *= 1.2
    elif a.pert == "c_up":
        mu1 *= 1.2; mu2 *= 1.2
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L = []; per_W = []; per_b = []; per_pl = []; per_pw = []
    sa = sd = sb = 0.0; sL = sW = 0.0; sbf = 0.0; spw = 0.0
    H = a.horizon
    win = 0.75 * H
    for s in seeds:
        L, W, ar, dp, bl, bf1, bf2, pw = run_seed(s, H, lam, mu1, mu2)
        per_L.append(L); per_W.append(W)
        bf = (bf1 + bf2) / 2.0
        per_b.append(bf); per_pl.append(0.0); per_pw.append(pw)
        sa += ar; sd += dp; sb += bl
        sL += L; sW += W; sbf += bf; spw += pw
    n = len(seeds)
    out = {
        "L": sL / n, "W": sW / n,
        "runtime_units": H, "seed_list": seeds, "seeds_used": n,
        "time_unit": "hour", "win": win,
        "arr": sa / n, "dep": sd / n, "blk": sb / n,
        "dep_rate": (sd / n) / win,
        "lam_eff": (sa / n) / win,
        "busy_util": sbf / n, "busy_frac": sbf / n,
        "p_loss": 0.0, "p_wait": spw / n,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_b, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
