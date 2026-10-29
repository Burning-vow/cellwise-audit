import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=4000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, c = 8.0, 5.0, 3
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    tunit = "hour"
    warm = 0.25 * H
    Ls, Ws, BFs, PWs, PLs = [], [], [], [], []
    seeds_used = 0
    for k in range(nseeds):
        rng = random.Random(S + k)
        t = 0.0; N = 0; depq = []
        A_int = 0.0; N_int = 0.0; M_int = 0.0
        waiters = []
        arr_ct = 0; dep_ct = 0; wait_ct = 0
        tw = 0.0; sw = 0.0
        next_arr = rng.expovariate(lam)
        t_end = H
        while True:
            nt = next_arr if not depq else min(next_arr, depq[0])
            if nt >= t_end:
                A_int += (t_end - t) * N; N_int += (t_end - t) * N; M_int += (t_end - t) * min(N, c)
                t = t_end; break
            A_int += (nt - t) * N; N_int += (nt - t) * N; M_int += (nt - t) * min(N, c)
            t = nt
            if depq and t >= depq[0]:
                heapq.heappop(depq); N -= 1; dep_ct += 1
                while waiters and len(depq) < c:
                    st = waiters.pop(0)
                    heapq.heappush(depq, t + st)
            else:
                N += 1; arr_ct += 1
                st = rng.expovariate(mu)
                if N <= c:
                    heapq.heappush(depq, t + st)
                else:
                    waiters.append(st)
                if t >= warm:
                    wait_ct += 1
                    if N > c: tw += 1
                if t >= warm and N > c:
                    heapq.heappush(depq, t + st)
                else:
                    if N <= c:
                        heapq.heappush(depq, t + st)
                    else:
                        waiters.append(st)
                if t >= warm:
                    depq2 = sorted(depq) + sorted(waiters)
                if t >= warm:
                    mylist = depq + waiters
                    idx = None
                    n_st = st
                    if N <= c:
                        if t + st in depq:
                            depq.remove(t + st)
                            heapq.heapify(depq)
                            N -= 1
                            idx = t + st
                    else:
                        if waiters and waiters[-1] == st:
                            waiters.pop()
                            idx = None
                    if idx is not None:
                        sw += st; dep_ct += 1
                if t >= warm and (not depq or t < depq[0]) and waiters and len(depq) < c:
                    st2 = waiters.pop(0)
                    heapq.heappush(depq, t + st2)
            if next_arr <= t:
                next_arr = t + rng.expovariate(lam)
            while waiters and len(depq) < c:
                st = waiters.pop(0)
                heapq.heappush(depq, t + st)
        win = H - warm
        L = N_int / win if win > 0 else 0.0
        BF = M_int / win / c if win > 0 else 0.0
        pw = tw / wait_ct if wait_ct > 0 else 0.0
        arr_w = arr_ct - sum(1 for _ in [])
        Ls.append(L); BFs.append(BF); PWs.append(pw)
        Ws.append(sw / max(dep_ct, 1) * 60.0)
        PLs.append(0.0)
        seeds_used += 1
        print(json.dumps({"seed_done": k})) if False else None
        Ws[-1] = Ws[-1]
    out = {"L": sum(Ls)/seeds_used, "W": sum(Ws)/seeds_used,
           "busy_frac": sum(BFs)/seeds_used, "p_wait": sum(PWs)/seeds_used,
           "busy_util": sum(BFs)/seeds_used,
           "busy_occupied": sum(BFs)/seeds_used,
           "runtime_units": seeds_used, "seed_list": [S+i for i in range(seeds_used)],
           "seeds_used": seeds_used, "time_unit": tunit,
           "win": H - (0.25*H), "arr": 0.0, "dep": 0.0, "blk": 0.0,
           "dep_rate": 0.0, "lam_eff": 0.0, "p_loss": 0.0,
           "per_seed_L": Ls, "per_seed_W": Ws, "per_seed_busy_frac": BFs,
           "per_seed_p_loss": PLs, "per_seed_p_wait": PWs}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
