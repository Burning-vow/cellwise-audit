import argparse, json, math, random, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, K = 6.0, 10.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1

    H = a.horizon
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    agg = dict(arr=0.0, dep=0.0, blk=0.0, area=0.0, busy=0.0)
    seed_list = []

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        na = rng.expovariate(lam)
        nd = math.inf
        queue = []
        n = 0
        last = 0.0
        area = busy = 0.0
        arr = dep = blk = 0
        sosj = 0.0
        ndep = 0
        nent = 0
        nwait = 0
        next_arr_t = None

        def schedule_next_dep(now):
            return now + queue[0][1] if queue else math.inf

        while True:
            if na <= nd:
                nt = na
                if nt > H: break
                if nt >= warm:
                    arr += 1
                area += n * (nt - last); busy += (1 if n > 0 else 0) * (nt - last)
                last = nt
                if n < K:
                    svc = rng.expovariate(mu)
                    if n == 0:
                        if nt >= warm:
                            nent += 1
                        queue.append([nt, svc])
                        n = 1
                        nd = nt + svc
                    else:
                        queue.append([nt, svc])
                        n += 1
                        if nt >= warm: nent += 1
                else:
                    if nt >= warm: blk += 1
                na = nt + rng.expovariate(lam)
                next_arr_t = na
            else:
                nt = nd
                if nt > H: break
                if nt >= warm:
                    dep += 1
                    ndep += 1
                    sosj += nt - queue[0][0]
                area += n * (nt - last); busy += (1 if n > 0 else 0) * (nt - last)
                last = nt
                queue.pop(0)
                n -= 1
                if queue:
                    nd = nt + queue[0][1]
                    if queue[0][0] < nt and nt >= warm:
                        nwait += 1
                    if nt >= warm: nent += 1
                else:
                    nd = math.inf

        if H > warm and (arr + blk) > 0:
            L = area / (H - warm)
            bf = busy / (H - warm)
            W = sosj / ndep if ndep > 0 else 0.0
            pl = blk / (arr + blk)
            pw = nwait / nent if nent > 0 else 0.0
        else:
            L = bf = W = pl = pw = 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        agg["arr"] += arr; agg["dep"] += dep; agg["blk"] += blk
        agg["area"] += area; agg["busy"] += busy

    S = a.seeds
    win = H - warm
    L = agg["area"] / (S * win)
    bf = agg["busy"] / (S * win)
    dep = agg["dep"] / S
    arr = agg["arr"] / S
    blk = agg["blk"] / S
    dep_rate = dep / win
    lam_eff = (arr + blk) / win
    p_loss = blk / (arr + blk) if (arr + blk) > 0 else 0.0
    W = sum(per_W) / S
    p_wait = sum(per_pw) / S
    out = {
        "L": L, "W": W, "busy_frac": bf, "p_loss": p_loss,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": S,
        "time_unit": "minute", "win": win,
        "arr": arr, "blk": blk, "dep": dep, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_wait": p_wait,
        "busy_util": min(L, 1.0), "busy_occupied": bf,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
