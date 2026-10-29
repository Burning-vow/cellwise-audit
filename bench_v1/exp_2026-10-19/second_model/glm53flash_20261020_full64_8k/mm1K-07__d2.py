import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, K = 6.0, 10.0, 6
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K += 1
    warm = 0.25 * H
    Ls, Ws, BFs, PLs, PWs = [], [], [], [], []
    seed_list, tot_arr, tot_blk, tot_dep = [], [], [], []
    for si in range(nseeds):
        seed = S + si
        rng = random.Random(seed * 100003 + 7)
        t = 0.0
        served = 0; arrivals = 0; blocked = 0
        area = 0.0; busy_time = 0.0
        wsum = 0.0; wcnt = 0; waited = 0
        queue = []  # (end_time, seq)
        busy_until = None
        nev = 0
        while t < H:
            if busy_until is not None and busy_until <= H:
                nt = busy_until
            elif busy_until is not None:
                nt = H
                ta = H + 1
            else:
                ta = t + rng.expovariate(lam)
                nt = ta
            if busy_until is not None and busy_until < H:
                if ta < busy_until:
                    nt = ta
                else:
                    nt = busy_until
            elif busy_until is not None:
                nt = min(ta, H)
            else:
                nt = ta
            if nt >= H:
                # close out remaining busy period integral up to H
                if busy_until is not None:
                    end = min(busy_until, H)
                    if t < warm:
                        seg_end = min(end, warm)
                        if seg_end > t: area += 0.0
                    if end > max(t, warm):
                        area += (queue_n if False else 0)
                break
            # integrate area over [t, nt] before state change (only post-warmup)
            cur = (1 if busy_until is not None else 0) + len(wait_q)
            if nt > warm:
                lo = max(t, warm)
                area += cur * (nt - lo)
            if busy_until is not None and nt > warm:
                lo = max(t, warm)
                busy_time += (nt - lo)
            t = nt
            if busy_until is not None and t == busy_until:
                heapq.heappop(queue) if queue else None
                busy_until = None
                served += 1
                if queue:
                    st, seq = heapq.heappop(queue)
                    busy_until = t + st
            else:
                arrivals += 1
                n = (1 if busy_until is not None else 0) + len(wait_q)
                if n >= K:
                    blocked += 1
                else:
                    st = rng.expovariate(mu)
                    if busy_until is None:
                        busy_until = t + st
                    else:
                        heapq.heappush(wait_q, (st, arrivals))
        win = H - warm
        L = area / win if win > 0 else 0.0
        denom = served
        W = wsum / wcnt if wcnt else 0.0
        BF = busy_time / win if win > 0 else 0.0
        PL = blocked / arrivals if arrivals else 0.0
        PW = waited / served if served else 0.0
        Ls.append(L); Ws.append(W); BFs.append(BF); PLs.append(PL); PWs.append(PW)
        seed_list.append(seed)
        tot_arr.append(arrivals); tot_blk.append(blocked); tot_dep.append(served)
    n = nseeds
    out = {
        "L": sum(Ls)/n, "W": sum(Ws)/n, "busy_frac": sum(BFs)/n,
        "p_loss": sum(PLs)/n, "runtime_units": H, "seed_list": seed_list,
        "seeds_used": n, "time_unit": "hour", "win": H - 0.25*H,
        "arr": sum(tot_arr)/n, "blk": sum(tot_blk)/n, "busy_util": sum(BFs)/n,
        "busy_occupied": sum(BFs)/n, "dep": sum(tot_dep)/n,
        "dep_rate": sum(tot_dep)/n/(H-0.25*H),
        "lam_eff": sum(tot_arr)/n/(H-0.25*H)*(1-sum(PLs)/n),
        "p_wait": sum(PWs)/n,
        "per_seed_L": Ls, "per_seed_W": Ws, "per_seed_busy_frac": BFs,
        "per_seed_p_loss": PLs, "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
