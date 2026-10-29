import argparse, json, heapq, math, random

def hyperexp(rng, m):
    if rng.random() < 0.2:
        return rng.expovariate(1.0/(0.893*m))
    return rng.expovariate(1.0/(0.13375*m))

def run_seed(seed, H, lam, m, warm):
    rng = random.Random(seed)
    t = 0.0
    busy = False
    qlen = 0
    arr_int = 0.0
    busy_int = 0.0
    L_int = 0.0
    n_sys = 0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    in_queue = []
    cur_soj = None
    arr_cnt = 0
    dep_cnt = 0
    wait_sum = 0.0
    soj_sum = 0.0
    waited = 0
    dep_win = 0
    arr_win = 0
    p_wait_cnt = 0
    win_start = warm
    while t < H:
        if next_arr <= next_dep and next_arr <= H:
            nt = next_arr
        elif next_dep <= H:
            nt = next_dep
        else:
            nt = H
        if nt >= win_start:
            dt = nt - t
            L_int += n_sys * dt
            busy_int += (1.0 if busy else 0.0) * dt
        t = nt
        if t >= H:
            break
        if next_arr <= next_dep:
            s = hyperexp(rng, m)
            arrive = t
            arr_cnt += 1
            if t >= win_start:
                arr_win += 1
            if not busy:
                busy = True
                next_dep = t + s
                cur_soj = (arrive, arrive, 0)
            else:
                qlen += 1
                in_queue.append((arrive, s))
            n_sys += 1
            next_arr = t + rng.expovariate(lam)
        else:
            a0, a1, w = cur_soj
            n_sys -= 1
            dep_cnt += 1
            if t >= win_start:
                dep_win += 1
                soj_sum += t - a0
                wait_sum += a1 - a0
                if a1 > a0:
                    p_wait_cnt += 1
            if qlen > 0:
                qlen -= 1
                a0, s = in_queue.pop(0)
                next_dep = t + s
                cur_soj = (a0, t, t - a0)
            else:
                busy = False
                next_dep = math.inf
                cur_soj = None
    win = H - win_start
    if win <= 0 or dep_win == 0:
        return dict(L=0.0, W=0.0, busy_frac=0.0, p_wait=0.0, arr=0, dep=0, win=0.0)
    L = L_int / win
    bf = busy_int / win
    return dict(L=L, W=(soj_sum/dep_win)*60.0, busy_frac=bf, p_wait=p_wait_cnt/dep_win,
                arr=arr_win, dep=dep_win, win=win)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    lam = 3.0
    m = 6.0/60.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": m *= 0.9
    elif a.pert == "c_up": pass
    warm = a.horizon * 0.25
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [run_seed(s, a.horizon, lam, m, warm) for s in seed_list]
    n = len(res)
    out = {
        "L": sum(r["L"] for r in res)/n,
        "W": sum(r["W"] for r in res)/n,
        "busy_frac": sum(r["busy_frac"] for r in res)/n,
        "busy_util": sum(r["busy_frac"] for r in res)/n,
        "busy_occupied": sum(r["busy_frac"] for r in res)/n,
        "arr": sum(r["arr"] for r in res)/n,
        "dep": sum(r["dep"] for r in res)/n,
        "blk": 0.0,
        "dep_rate": sum(r["dep"] for r in res)/n / (sum(r["win"] for r in res)/n),
        "lam_eff": sum(r["arr"] for r in res)/n / (sum(r["win"] for r in res)/n),
        "p_loss": 0.0,
        "p_wait": sum(r["p_wait"] for r in res)/n,
        "per_seed_L": [r["L"] for r in res],
        "per_seed_W": [r["W"] for r in res],
        "per_seed_busy_frac": [r["busy_frac"] for r in res],
        "per_seed_p_loss": [0.0]*n,
        "per_seed_p_wait": [r["p_wait"] for r in res],
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": sum(r["win"] for r in res)/n,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
