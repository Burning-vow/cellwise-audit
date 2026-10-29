import argparse, heapq, json, math, random, sys

def hyperexp_two(rand, mean, cv):
    cv2 = cv * cv
    p = 0.5 * (1.0 + math.sqrt((cv2 - 1.0) / (cv2 + 1.0)))
    m1 = mean * p
    m2 = (mean - p * m1) / (1.0 - p) if p < 1.0 else mean
    return (m1, p, m2)

def draw_service(rand, m1, p, m2):
    return m1 if rand.random() < p else m2

def run_seed(seed, horizon, warm, lam, m1, p, m2, rng_off):
    rand = random.Random(seed + rng_off)
    t = 0.0
    next_arr = rand.expovariate(lam)
    events = []
    heapq.heappush(events, (next_arr, 0, None))
    busy = False
    svc_left = 0.0
    q = []
    n_sys = 0
    area_n = 0.0
    area_b = 0.0
    last = 0.0
    w_sums = []
    waits = []
    dep_ct = 0
    arr_ct = 0
    eid = 0
    while True:
        if not events:
            break
        ev_t, kind, info = heapq.heappop(events)
        if ev_t > horizon:
            break
        area_n += n_sys * (ev_t - last)
        area_b += (1.0 if n_sys >= 1 else 0.0) * (ev_t - last)
        last = ev_t
        t = ev_t
        if kind == 0:
            arr_ct += 1 if t >= warm else 0
            n_sys += 1
            s = draw_service(rand, m1, p, m2)
            waited = busy or len(q) > 0
            if t >= warm:
                waits.append(1.0 if waited else 0.0)
            if not busy:
                busy = True
                heapq.heappush(events, (t + s, 1, s))
            else:
                q.append((t, s))
            nt = t + rand.expovariate(lam)
            eid += 1
            heapq.heappush(events, (nt, 0, None))
        else:
            n_sys -= 1
            if t >= warm:
                dep_ct += 1
                w_sums.append(t - info[0])
            if q:
                at, s = q.pop(0)
                heapq.heappush(events, (t + s, 1, (at, s)))
            else:
                busy = False
    win = horizon - warm
    if win <= 0:
        win = horizon
        warm_v = 0.0
    L = area_n / win
    busy_frac = area_b / win
    W = (sum(w_sums) / len(w_sums)) * 60.0 if w_sums else 0.0
    p_wait = (sum(waits) / len(waits)) if waits else 0.0
    return L, W, busy_frac, p_wait, arr_ct, dep_ct, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 5.0
    mean_svc = 6.0 / 60.0
    cv = 3.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mean_svc /= 1.1
    elif a.pert == "c_up":
        cv *= 1.1
    m1, p, m2 = hyperexp_two(None, mean_svc, cv)
    m1 = mean_svc * p
    m2 = (mean_svc - p * m1) / (1.0 - p)
    horizon = a.horizon
    warm = 0.25 * horizon
    per_L, per_W, per_b, per_pw = [], [], [], []
    seed_list = []
    tot_arr = tot_dep = 0
    tot_L = tot_W = tot_b = 0.0
    n = 0
    for i in range(a.seeds):
        seed = a.seed_start + i
        L, W, bf, pw, ac, dc, win = run_seed(seed, horizon, warm, lam, m1, p, m2, 1000 * seed)
        seed_list.append(seed)
        per_L.append(L); per_W.append(W); per_b.append(bf); per_pw.append(pw)
        tot_L += L; tot_W += W; tot_b += bf
        tot_arr += ac; tot_dep += dc
        n += 1
    out = {
        "L": tot_L / n,
        "W": tot_W / n,
        "busy_frac": tot_b / n,
        "busy_util": tot_b / n,
        "busy_occupied": tot_b / n,
        "runtime_units": horizon,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": horizon - warm,
        "arr": tot_arr / n,
        "dep": tot_dep / n,
        "blk": 0.0,
        "dep_rate": (tot_dep / n) / (horizon - warm),
        "lam_eff": lam,
        "p_loss": 0.0,
        "p_wait": sum(per_pw) / n,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_b,
        "per_seed_p_loss": [0.0] * n,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
