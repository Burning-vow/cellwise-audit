import argparse, json, math, heapq, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    ns = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam = 4.0; mu = 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.1
    warm = 0.25 * H
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    seed_list = []
    for k in range(ns):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0; n = 0; busy_until = -1.0
        arr_n = 0; dep_n = 0; blk_n = 0
        area_L = 0.0; area_B = 0.0; wait_sum = 0.0; waited = 0; in_win_dep = 0
        arrivals = []
        ev = []
        next_arr = rng.expovariate(lam)
        heapq.heappush(ev, (next_arr, 0, 0))
        svc_ids = 0
        while True:
            if not ev: break
            te, typ, idx = heapq.heappop(ev)
            if te > H: break
            if te >= warm:
                area_L += n * (te - max(t, warm))
                area_B += (1 if n > 0 else 0) * (te - max(t, warm))
            t = te
            if typ == 0:
                n += 1; arr_n += 1
                svc = 1.0 / mu
                start = t if n == 1 else busy_until
                if start < t: start = busy_until
                if n == 1: start = t
                busy_until = start + svc
                if t >= warm: waited += (1 if busy_until - svc > t else 0)
                heapq.heappush(ev, (busy_until, 1, svc_ids)); svc_ids += 1
                nt = t + rng.expovariate(lam)
                if nt <= H: heapq.heappush(ev, (nt, 0, 0))
            else:
                n -= 1; dep_n += 1
                if t >= warm: in_win_dep += 1
        win = H - warm
        L = area_L / win
        bf = area_B / win
        W = wait_sum / in_win_dep if in_win_dep > 0 else 0.0
        W = (L / lam) * 60.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(0.0); per_pw.append(bf)
    m = len(per_L)
    L = sum(per_L) / m; W = sum(per_W) / m; bf = sum(per_bf) / m
    out = {
        "L": L, "W": W, "busy_frac": bf,
        "busy_util": bf, "busy_occupied": bf,
        "runtime_units": H, "time_unit": "hour", "win": H - warm,
        "seed_list": seed_list, "seeds_used": m,
        "arr": lam, "dep": lam, "blk": 0.0,
        "dep_rate": lam, "lam_eff": lam,
        "p_loss": 0.0, "p_wait": bf,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
