import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, c = 5.0, 1
    mu = 1.0 / 0.1
    cv = 1.5
    pa = 0.5 * (1.0 + math.sqrt((cv * cv - 1.0) / (cv * cv + 1.0)))
    pb = 1.0 - pa
    m1 = 0.1
    mu1 = 2.0 * pa / m1
    mu2 = 2.0 * pb / m1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25 * H
    win = H - warm
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    sL = sW = sB = sPL = sPW = 0.0
    seed_list = []
    for si in range(seeds):
        sd = S + si
        seed_list.append(sd)
        rng = random.Random(sd)
        t = 0.0
        na = 0
        arr_t = []
        busy = 0.0
        areaN = 0.0
        n = 0
        dep_t = []
        waits = []
        served = 0
        lost = 0
        arrived = 0
        tnext = rng.expovariate(lam)
        while t < H:
            ta = t + rng.expovariate(lam)
            arr_t.append(ta)
            t = ta
        while t < H:
            td = t + draw(rng, pa, pb, mu1, mu2)
            dep_t.append(td)
            t = td
        heapq.heapify(arr_t)
        heapq.heapify(dep_t)
        while arr_t or dep_t:
            if arr_t and (not dep_t or arr_t[0] <= dep_t[0]):
                t = heapq.heappop(arr_t)
                if t >= H: break
                areaN += n * max(0.0, min(t, H) - max(t_prev, warm)) if (t_prev := -1.0) or True else 0
                arrived += 1
                if n < c:
                    n += 1
                    if t >= warm:
                        pass
                else:
                    lost += 1
            else:
                t = heapq.heappop(dep_t)
                if t >= H: break
                n -= 1
                served += 1
        break
    out = {"L": 0.0, "W": 0.0}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
