import argparse, json, math, random, heapq, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=200.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, c = 8.0, 10.0, 1.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 2
    tunit = "hour"; svc = 6.0/60.0
    warm = H * 0.25
    perL=[];perW=[];perB=[];perPL=[];perPW=[];seed_list=[];arrs=[];deps=[];blks=[];utils=[]
    for k in range(n_seeds):
        seed = S + k; seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0; N = 0; busy = 0
        arr_t = rng.expovariate(lam)
        ev = []; heapq.heappush(ev, (arr_t, "A", None))
        area_N = 0.0; area_B = 0.0
        wt = 0.0; wn = 0; waited = 0
        arr_c = 0; dep_c = 0; blk_c = 0
        last = 0.0
        idle = True
        dep_time = None
        while True:
            if not ev: break
            t2, typ, st = heapq.heappop(ev)
            if t2 > H: break
            if t2 > warm:
                if t2 > last:
                    area_N += N * (min(t2,H)-max(last,warm)) if last < H else 0
                    area_B += (1 if N>0 else 0) * (min(t2,H)-max(last,warm)) if last < H else 0
                    last = t2
            else:
                last = t2
            t = t2
            if typ == "A":
                arr_c += 1
                sv = svc
                if busy < c:
                    busy += 1
                    heapq.heappush(ev, (t + sv, "D", sv))
                    if t > warm:
                        wt += 0.0; wn += 1
                else:
                    if t > warm: waited += 1
                    # queue: record arrival into FIFO of pending
                    q.append((t, sv))
                nx = t + rng.expovariate(lam)
                heapq.heappush(ev, (nx, "A", None))
            else:
                busy -= 1; dep_c += 1
                if q and busy < c:
                    qa, sv = q.pop(0)
                    busy += 1
                    if qa > warm:
                        wt += (t - qa); wn += 1
                    heapq.heappush(ev, (t + sv, "D", sv))
        win = H - warm
        L = area_N / win if win > 0 else 0.0
        B = area_B / win if win > 0 else 0.0
        W = (wt / wn) * 60.0 if wn else 0.0
        perL.append(L); perW.append(W); perB.append(B)
        perPL.append(0.0)
        perPW.append((waited/arr_c) if arr_c else 0.0)
        arrs.append(arr_c); deps.append(dep_c); blks.append(0)
        utils.append(B)
    n = len(perL)
    out = {
        "L": sum(perL)/n, "W": sum(perW)/n, "busy_frac": sum(perB)/n,
        "busy_util": sum(perB)/n, "busy_occupied": sum(perB)/n,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": n,
        "time_unit": tunit, "win": H - warm,
        "arr": sum(arrs)/n, "blk": sum(blks)/n,
        "dep": sum(deps)/n,
        "dep_rate": (sum(deps)/n) / (H - warm),
        "lam_eff": (sum(deps)/n) / (H - warm),
        "p_loss": 0.0, "p_wait": sum(perPW)/n,
        "per_seed_L": perL, "per_seed_W": perW,
        "per_seed_busy_frac": perB, "per_seed_p_loss": perPL,
        "per_seed_p_wait": perPW,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
