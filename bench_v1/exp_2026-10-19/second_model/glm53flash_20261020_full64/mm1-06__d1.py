import argparse, json, random
from collections import deque

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu = 7.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.1
    H = float(a.horizon)
    warm = 0.25 * H
    Ls, Ws, BF, PW, PL = [], [], [], [], []
    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        cur = None
        dep_t = float("inf")
        q = deque()
        area = 0.0; busy = 0.0
        arr_c = 0; dep_c = 0; ws = 0.0; wn = 0; pw = 0
        while True:
            t2 = min(next_arr, dep_t)
            if t2 > warm:
                seg = min(t2, H) - max(t, warm)
                if seg > 0:
                    area += n * seg
                    busy += min(n, 1) * seg
            if t2 > H:
                break
            t = t2
            if next_arr <= dep_t:
                if t <= H:
                    svc = rng.expovariate(mu)
                    if t > warm:
                        arr_c += 1
                    if cur is None:
                        cur = (t, svc, False)
                        dep_t = t + svc
                    else:
                        q.append((t, svc))
                    n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if cur is not None and t <= H and t > warm:
                    dep_c += 1
                    ws += t - cur[0]
                    wn += 1
                    if cur[2]:
                        pw += 1
                n -= 1
                if q:
                    ar, sv = q.popleft()
                    cur = (ar, sv, True)
                    dep_t = t + sv
                else:
                    cur = None
                    dep_t = float("inf")
        win = H - warm
        Ls.append(area / win)
        Ws.append((ws / wn) * 60.0)
        BF.append(busy / win)
        PW.append(pw / arr_c if arr_c else 0.0)
        PL.append(0.0)
    m = len(Ls)
    out = {
        "L": sum(Ls) / m,
        "W": sum(Ws) / m,
        "busy_frac": sum(BF) / m,
        "busy_util": sum(BF) / m,
        "busy_occupied": sum(BF) / m,
        "p_wait": sum(PW) / m,
        "p_loss": 0.0,
        "arr": sum(arr_c for _ in [0]) / m,
        "dep": None,
        "dep_rate": None,
        "lam_eff": lam,
        "blk": 0.0,
        "runtime_units": "hour",
        "time_unit": "hour",
        "seed_list": [a.seed_start + i for i in range(m)],
        "seeds_used": m,
        "win": H - warm,
        "per_seed_L": Ls,
        "per_seed_W": Ws,
        "per_seed_busy_frac": BF,
        "per_seed_p_wait": PW,
        "per_seed_p_loss": PL,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
