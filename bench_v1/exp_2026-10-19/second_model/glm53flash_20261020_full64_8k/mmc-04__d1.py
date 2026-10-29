import argparse, json, heapq, math, random

def run_seed(seed, H, warm, lam, mu_h, c):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    q = 0
    busy = 0
    events = []
    arr_t = rng.expovariate(lam)
    heapq.heappush(events, (arr_t, 0, None))
    aid = 0
    area_L = 0.0
    area_B = 0.0
    area_occ0 = 0.0
    win_t = 0.0
    soj_sum = 0.0
    soj_cnt = 0
    wait_cnt = 0
    arr_cnt = 0
    dep_cnt = 0
    last = 0.0
    while events:
        et, kind, cust = heapq.heappop(events)
        if et > H:
            break
        dt = et - last
        if et > warm:
            w0 = max(last, warm)
            if et > w0:
                area_L += n * (et - w0)
                area_B += min(n, c) * (et - w0)
                if n == 0:
                    area_occ0 += et - w0
                win_t += et - w0
        last = et
        t = et
        if kind == 0:
            svc = rng.expovariate(mu_h)
            cust = [t, svc]
            if n < c:
                n += 1
                heapq.heappush(events, (t + svc, 1, cust))
            else:
                q += 1
            if t > warm:
                arr_cnt += 1
                if n > c - 1 + 0 and q > 0:
                    wait_cnt += 1
            nt = t + rng.expovariate(lam)
            if nt <= H:
                heapq.heappush(events, (nt, 0, None))
        else:
            n -= 1
            dep_cnt += 1 if t > warm else 0
            if t > warm:
                soj_sum += (t - cust[0]) * 60.0
                soj_cnt += 1
            if q > 0:
                q -= 1
                heapq.heappush(events, (t + cust and rng.expovariate(mu_h), 1, [cust[0], 0]))
            if q > 0:
                pass
    if last < H:
        w0 = max(last, warm)
        if H > w0:
            area_L += n * (H - w0)
            area_B += min(n, c) * (H - w0)
            if n == 0:
                area_occ0 += H - w0
            win_t += H - w0
    L = area_L / win_t if win_t > 0 else 0.0
    busy_frac = area_B / win_t / c if win_t > 0 else 0.0
    p_wait = wait_cnt / arr_cnt if arr_cnt > 0 else 0.0
    W = soj_sum / soj_cnt if soj_cnt > 0 else 0.0
    occupied = 1.0 - area_occ0 / win_t if win_t > 0 else 0.0
    return L, W, busy_frac, p_wait, occupied, arr_cnt, dep_cnt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu_h, c = 10.0, 6.0, 2
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu_h *= 1.1
    elif a.pert == "c_up":
        c += 1
    H = a.horizon
    warm = 0.25 * H
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    pL, pW, pB, pP, pO, pA, pD = [], [], [], [], [], [], []
    for s in seed_list:
        L, W, B, P, O, A, D = run_seed(s, H, warm, lam, mu_h, c)
        pL.append(L); pW.append(W); pB.append(B); pP.append(P); pO.append(O); pA.append(A); pD.append(D)
    k = len(seed_list)
    res = {
        "L": sum(pL)/k, "W": sum(pW)/k, "busy_frac": sum(pB)/k,
        "p_wait": sum(pP)/k, "busy_util": sum(pB)/k, "busy_occupied": sum(pO)/k,
        "runtime_units": H, "seed_list": seed_list, "seeds_used": k,
        "time_unit": "hour", "win": H - warm,
        "arr": sum(pA)/k, "dep": sum(pD)/k, "blk": 0.0,
        "dep_rate": (sum(pD)/k) / (H - warm), "lam_eff": (sum(pA)/k) / (H - warm),
        "p_loss": 0.0,
        "per_seed_L": pL, "per_seed_W": pW, "per_seed_busy_frac": pB,
        "per_seed_p_loss": [0.0]*k, "per_seed_p_wait": pP
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
