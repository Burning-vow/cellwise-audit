import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    N = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, K = 6.0, 10.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": K = 5
    warm = 0.25 * H
    pL, pW, pB, pLoss, pWait = [], [], [], [], []
    seeds_used = 0; seed_list = []
    arrs = deps = blks = 0
    for s in range(S, S + N):
        rng = random.Random(s * 2654435761 % (2**31))
        t = 0.0; n = 0
        serv = {}; nxt_dep = None
        arrivals = []; at = rng.expovariate(lam)
        Aint = 0.0; Busy = 0.0; cntA = cntD = cntB = cntW = 0; waitsum = 0.0
        while at < H:
            arrivals.append(at)
            at += rng.expovariate(lam)
        i = 0
        queue = []
        while i < len(arrivals) or nxt_dep is not None:
            if nxt_dep is None or (i < len(arrivals) and arrivals[i] < nxt_dep):
                t = arrivals[i]; i += 1
                if n >= K:
                    if t >= warm: cntB += 1
                else:
                    if t >= warm: cntA += 1
                    st = rng.expovariate(mu)
                    if n == 0:
                        nxt_dep = t + st
                    else:
                        queue.append((t, st))
                        if t >= warm: cntW += 1
                    n += 1
            else:
                t = nxt_dep
                if t >= warm:
                    cntD += 1
                n -= 1
                if queue:
                    at0, st = queue.pop(0)
                    if t >= warm: waitsum += t - at0
                    nxt_dep = t + st
                else:
                    nxt_dep = None
            if t >= warm:
                dt_next = None
                if i < len(arrivals) and (nxt_dep is None or arrivals[i] < nxt_dep):
                    dt_next = arrivals[i]
                elif nxt_dep is not None:
                    dt_next = nxt_dep
                if dt_next is not None and dt_next > warm:
                    dur = min(dt_next, H) - max(t, warm)
                    if dur > 0:
                        Aint += n * dur
                        if n > 0: Busy += dur
        win = H - warm
        L = Aint / win
        busy_frac = Busy / win
        p_loss = cntB / (cntA + cntB) if (cntA + cntB) > 0 else 0.0
        p_wait = cntW / cntA if cntA > 0 else 0.0
        W = waitsum / cntW if cntW > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(busy_frac); pLoss.append(p_loss); pWait.append(p_wait)
        arrs += cntA; deps += cntD; blks += cntB
        seeds_used += 1; seed_list.append(s)
    out = {
        "L": sum(pL)/seeds_used,
        "W": sum(pW)/seeds_used,
        "busy_frac": sum(pB)/seeds_used,
        "p_loss": sum(pLoss)/seeds_used,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": H - warm,
        "arr": arrs/seeds_used,
        "blk": blks/seeds_used,
        "dep": deps/seeds_used,
        "dep_rate": deps/seeds_used/(H-warm),
        "lam_eff": lam*(1-sum(pLoss)/seeds_used),
        "p_wait": sum(pWait)/seeds_used,
        "busy_util": sum(pB)/seeds_used,
        "busy_occupied": sum(pB)/seeds_used,
        "per_seed_L": pL, "per_seed_W": pW,
        "per_seed_busy_frac": pB, "per_seed_p_loss": pLoss, "per_seed_p_wait": pWait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
