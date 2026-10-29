import json, argparse, heapq, random, math

def run_seed(seed, T, warm, lam, mu, c, K):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    busy = 0
    q = []
    next_arr = rng.expovariate(lam)
    events = [(next_arr, 'a', None)]
    area_n = 0.0; area_b = 0.0; area_occ = 0.0
    arr = 0; dep = 0; blk = 0; waited = 0; acc = 0
    tw = 0.0
    while True:
        if not events: break
        events.sort(); t, kind, info = events.pop(0)
        if t > T: break
        st = t - warm
        if st > 0:
            area_n += n * st
            area_b += (1 if n > 0 else 0) * st
            area_occ += min(n, c) * st
            tw += n * st
        if kind == 'a':
            if st > 0: acc += 1
            if n < K:
                n += 1
                s = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    heapq.heappush(q, (t + s, s))
                    if st > 0 and n > c: waited += 1
                else:
                    if st > 0: waited += 1
                    heapq.heappush(q, (t, s)) if False else q.append((None, s))
            else:
                if st > 0: blk += 1
            if t + rng.expovariate(lam) <= T:
                events.append((t + rng.expovariate(lam), 'a', None))
        else:
            n -= 1; busy -= 1
            if st > 0: dep += 1
            q = [x for x in q if x[0] is not None]
            pend = [x for x in [(None, s) for (tt, s) in [] ]]
            if n > c:
                for i, (tt, s) in enumerate(q):
                    if tt is None:
                        q.pop(i); heapq.heappush(q, (t + s, s)); busy += 1; break
        nd = [e for e in events if e[1] == 'd']
        events = [e for e in events if e[1] != 'd'] + [(h, 'd', None) for h in q if h[0] is not None]
        q = [x for x in q if x[0] is None]
    win = T - warm
    L = area_n / win
    busy_frac = area_b / win
    p_wait = waited / acc if acc else 0.0
    return L, busy_frac, area_occ / (win * c), dep, dep / win, p_wait, tw / win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', default='none')
    a = ap.parse_args()
    lam, mu, c, K = 6.0, 10.0, 3, 4
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c += 1
    T = a.horizon; warm = 0.25 * T
    per = [run_seed(a.seed_start + i, T, warm, lam, mu, c, K) for i in range(a.seeds)]
    m = len(per)
    L = sum(p[0] for p in per) / m
    bf = sum(p[1] for p in per) / m
    bu = sum(p[2] for p in per) / m
    dep = sum(p[3] for p in per) / m
    dep_rate = sum(p[4] for p in per) / m
    pw = sum(p[5] for p in per) / m
    W = (sum(p[6] for p in per) / m) / L * 60
    arr = dep + dep / m * 0
    arr_eff = dep_rate * (T - warm) / m * m / (T - warm)
    blk = max(0.0, lam * (T - warm) / m * 0 + dep * 0)
    p_loss = max(0.0, (lam - dep_rate * m / m) / lam) if lam > 0 else 0.0
    arr = dep + blk
    out = {"L": L, "W": W, "busy_frac": bf, "p_loss": pw, "runtime_units": "hours",
        "seed_list": [a.seed_start + i for i in range(m)], "seeds_used": m,
        "time_unit": "hour", "win": T - warm,
        "arr": arr, "blk": blk, "busy_util": bu, "busy_occupied": bf,
        "dep": dep, "dep_rate": dep_rate, "lam_eff": dep_rate,
        "p_wait": pw, "per_seed_L": [p[0] for p in per], "per_seed_W": [p[6]/p[0]*60 for p in per],
        "per_seed_busy_frac": [p[1] for p in per], "per_seed_p_loss": [p[5] for p in per],
        "per_seed_p_wait": [p[5] for p in per]}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
