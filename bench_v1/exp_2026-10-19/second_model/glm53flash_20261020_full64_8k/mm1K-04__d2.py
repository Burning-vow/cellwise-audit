import argparse, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=100000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    ns = int(a.seeds); H = float(a.horizon); S = int(a.seed_start); pert = a.pert
    C = 4
    lam = 8.0/60.0; mu = 1.0/5.0
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": mu *= 1.1
    elif pert == "c_up": C = 5
    warm = 0.25 * H
    perL=[]; perW=[]; perBF=[]; perPL=[]; perPW=[]
    seed_list=[]; tot_arr=0; tot_dep=0; tot_blk=0
    for k in range(ns):
        sd = S + k
        seed_list.append(sd)
        rng = random.Random(sd)
        t = 0.0; n = 0
        arrive = 0.0; depart = 0.0; block = 0.0
        areaN = 0.0; areaB = 0.0
        winW = []; waited = 0; winArr = 0
        # event list: (time, type, cust)  cust=(arrival_time, service_time)
        import heapq
        def next_arr(t0):
            return t0 + rng.expovariate(lam)
        na = next_arr(0.0)
        events = []
        heapq.heappush(events, (na, 0, None))
        busyq = []
        last = 0.0
        while True:
            if not events and not busyq:
                break
            if events:
                te, ty, cust = events[0]
            else:
                te = float('inf')
            # service completions
            if busyq and busyq[0][0] < te:
                ct, cdep, cust2 = heapq.heappop(busyq)
                areaN += n*(ct-last); areaB += (1 if n>0 else 0)*(ct-last)
                last = ct; n -= 1
                depart += 1 if ct >= warm else 0
                if ct >= warm:
                    winW.append((cdep[1]) - (cdep[0]))
                if busyq is not None and n > 0 and len(busyq) < C-0:
                    pass
                if n >= 1:
                    nxt = busyq
                # start next waiting customer: we need queue; use events type 1 as in-queue start
                # simpler: keep a queue list
                if servq:
                    nc = servq.pop(0)
                    st = nc[1]
                    heapq.heappush(busyq, (ct+st, ct, nc))
                events = events  # no-op
                continue
            if not events:
                break
            heapq.heappop(events)
            te = te; ty = ty; cust = cust
            areaN += n*(te-last); areaB += (1 if n>0 else 0)*(te-last)
            last = te
            if ty == 0:
                cust = (te, rng.expovariate(mu))
                arrive += 1 if te >= warm else 0
                if te >= warm: winArr += 1
                if n >= C:
                    block += 1 if te >= warm else 0
                else:
                    n += 1
                    if n == 1:
                        heapq.heappush(busyq, (te + cust[1], te, cust))
                    else:
                        servq.append(cust)
                if te < H:
                    heapq.heappush(events, (next_arr(te), 0, None))
            elif ty == 1:
                pass
            if te >= H and not busyq and not servq:
                break
        # fix: ensure servq defined
        break
    # Fallback: simpler correct simulation below (single pass, rewrite)
    perL=[]; perW=[]; perBF=[]; perPL=[]; perPW=[]
    seed_list=[]; tot_arr=0.0; tot_dep=0.0; tot_blk=0.0
    for k in range(ns):
        sd = S + k
        seed_list.append(sd)
        rng = random.Random(sd)
        import heapq
        t = 0.0; n = 0
        servq = []
        areaN = 0.0; areaB = 0.0
        winW = []; winArr = 0; winDep = 0; winBlk = 0
        winWait = 0
        last = 0.0
        busyq = []
        events = [(rng.expovariate(lam), 0)]
        heapq.heapify(events)
        while True:
            if events and (not busyq or events[0][0] < busyq[0][0]):
                te, ty = heapq.heappop(events)
                if te > H and n == 0:
                    break
                areaN += n*(te-last); areaB += (1 if n>0 else 0)*(te-last)
                last = te; t = te
                if ty == 0:
                    cust = (te, rng.expovariate(mu))
                    inwin = te >= warm
                    if inwin: winArr += 1
                    if n >= C:
                        if inwin: winBlk += 1
                    else:
                        n += 1
                        if n == 1:
                            heapq.heappush(busyq, (te + cust[1], cust))
                        else:
                            servq.append(cust)
                    if te < H:
                        heapq.heappush(events, (te + rng.expovariate(lam), 0))
            else:
                ct, cust = heapq.heappop(busyq)
                areaN += n*(ct-last); areaB += (1 if n>0 else 0)*(ct-last)
                last = ct; t = ct
                n -= 1
                if ct >= warm:
                    winDep += 1
                    winW.append(ct - cust[0])
                    if ct - cust[0] > 1e-12: winWait += 1
                if servq:
                    nc = servq.pop(0)
                    heapq.heappush(busyq, (ct + nc[1], nc))
            if not events and not busyq:
                break
            if t >= H and not busyq and not servq:
                break
        if t < H:
            areaN += n*(H-last); areaB += (1 if n>0 else 0)*(H-last)
        win = H - warm
        L = areaN / win if win > 0 else 0.0
        BF = areaB / win if win > 0 else 0.0
        Wm = (sum(winW)/len(winW)) if winW else 0.0
        pl = winBlk/winArr if winArr else 0.0
        pw = winWait/winDep if winDep else 0.0
        perL.append(L); perW.append(Wm); perBF.append(BF); perPL.append(pl); perPW.append(pw)
        tot_arr += winArr; tot_dep += winDep; tot_blk += winBlk
    nsu = ns
    win = H - warm
    L = sum(perL)/nsu
    W = sum(perW)/nsu
    BF = sum(perBF)/nsu
    p_loss = sum(perPL)/nsu
    p_wait = sum(perPW)/nsu
    arr = tot_arr/nsu; dep = tot_dep/nsu; blk = tot_blk/nsu
    dep_rate = dep/win
    lam_eff = (arr - blk)/win
    out = {
        "L": L, "W": W, "busy_frac": BF, "p_loss": p_loss,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": nsu,
        "time_unit": "minute", "win": win,
        "arr": arr, "blk": blk, "busy_util": BF*C/C, "dep": dep,
        "dep_rate": dep_rate, "lam_eff": lam_eff, "p_wait": p_wait,
        "busy_occupied": BF,
        "per_seed_L": perL, "per_seed_W": perW, "per_seed_busy_frac": perBF,
        "per_seed_p_loss": perPL, "per_seed_p_wait": perPW
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
