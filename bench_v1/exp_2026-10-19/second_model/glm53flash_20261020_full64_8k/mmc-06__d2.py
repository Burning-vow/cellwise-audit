import argparse, heapq, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 14.0, 10.0, 2
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    warm = 0.25 * a.horizon
    win = a.horizon - warm
    seed_list, per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], [], []
    tot = dict(L=0.0, W=0.0, bf=0.0, pw=0.0, occ=0.0, arr=0.0, dep=0.0, blk=0.0)
    for k in range(a.seeds):
        s = a.seed_start + k
        rng = random.Random(s)
        t, N = 0.0, 0
        ev, seq = [], 0
        heapq.heappush(ev, (rng.expovariate(lam), seq, "arr", None)); seq += 1
        last, aL, aB, aO, arrc, depc, blkc, wsum, wflag = 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0
        while ev:
            t, _, kind, cust = heapq.heappop(ev)
            if t > a.horizon: break
            lo, hi = max(last, warm), min(t, a.horizon)
            if hi > lo:
                aL += (hi - lo) * N
                aB += (hi - lo) * min(N, c)
                aO += (hi - lo) * (1 if N > 0 else 0)
            last = t
            if kind == "arr":
                waited = 1 if N >= c else 0
                serv = rng.expovariate(mu)
                if warm <= t <= a.horizon:
                    arrc += 1; wflag += waited
                if N < c:
                    N += 1
                    heapq.heappush(ev, (t + serv, seq, "dep", (t,))); seq += 1
                else:
                    N += 1
                heapq.heappush(ev, (t + rng.expovariate(lam), seq, "arr", None)); seq += 1
            else:
                N -= 1
                at = cust[0]
                if warm <= at <= a.horizon and t <= a.horizon:
                    depc += 1; wsum += (t - at) * 60.0
                if N >= c:
                    nserv = rng.expovariate(mu)
                    heapq.heappush(ev, (t + nserv, seq, "dep", (t,))); seq += 1
            if not ev or t > a.horizon: break
            if ev[0][0] > a.horizon:
                lo, hi = max(t, warm), a.horizon
                if hi > lo:
                    aL += (hi - lo) * N; aB += (hi - lo) * min(N, c)
                    aO += (hi - lo) * (1 if N > 0 else 0)
                break
        L = aL / win if win > 0 else 0.0
        bf = aB / (c * win) if win > 0 else 0.0
        occ = aO / win if win > 0 else 0.0
        pw = wflag / arrc if arrc else 0.0
        W = wsum / depc if depc else 0.0
        seed_list.append(s)
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(0.0); per_pw.append(pw)
        tot["L"] += L; tot["W"] += W; tot["bf"] += bf; tot["pw"] += pw
        tot["occ"] += occ; tot["arr"] += arrc; tot["dep"] += depc; tot["blk"] += blkc
    n = max(1, a.seeds)
    out = {
        "L": tot["L"] / n, "W": tot["W"] / n, "busy_frac": tot["bf"] / n,
        "p_wait": tot["pw"] / n, "runtime_units": "hour",
        "seed_list": seed_list, "seeds_used": a.seeds, "time_unit": "hour",
        "win": win, "arr": tot["arr"] / n, "blk": tot["blk"] / n,
        "busy_util": tot["bf"] / n, "busy_occupied": tot["occ"] / n,
        "dep": tot["dep"] / n, "dep_rate": tot["dep"] / n / win if win > 0 else 0.0,
        "lam_eff": tot["arr"] / n / win if win > 0 else 0.0,
        "p_loss": tot["blk"] / max(1.0, tot["arr"]) if tot["arr"] else 0.0,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
