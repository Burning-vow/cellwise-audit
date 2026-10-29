import argparse, json, math, random

def run_seed(seed, horizon, warm, lam, smin):
    rng = random.Random(seed)
    t = 0.0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    N = 0
    queue = []
    last = 0.0
    area_N = 0.0
    area_busy = 0.0
    busy = 0.0
    busy_occ = 0.0
    served = {}
    order = []
    arr = dep = wait_n = 0
    wait_sum = 0.0
    waits = []
    lost = 0
    arr_in_win = 0
    while True:
        if next_arr <= next_dep and next_arr <= horizon:
            nt = next_arr
            a0, a1 = last, nt
            if a1 > warm:
                area_N += N * (a1 - max(a0, warm))
                area_busy += (1 if N >= 1 else 0) * (a1 - max(a0, warm))
            last = nt
            t = nt
            svc = smin
            arrive = t
            order.append(arrive)
            if N < 1:
                start = t
                next_dep = t + svc
            else:
                start = None
            queue.append((arrive, svc, start))
            N += 1
            if arrive >= warm:
                arr_in_win += 1
            next_arr = t + rng.expovariate(lam)
        elif next_dep <= horizon:
            nt = next_dep
            a0, a1 = last, nt
            if a1 > warm:
                area_N += N * (a1 - max(a0, warm))
                area_busy += (1 if N >= 1 else 0) * (a1 - max(a0, warm))
            last = nt
            t = nt
            arrive, svc, start = queue.pop(0)
            N -= 1
            if start is None:
                start = arrive
            for i in range(len(queue)):
                if queue[i][2] is None:
                    queue[i] = (queue[i][0], queue[i][1], t)
                    break
            if arrive >= warm:
                dep += 1
                w = start - arrive
                waits.append(w + svc)
                wait_sum += w + svc
                if w > 0:
                    wait_n += 1
            if N >= 1:
                next_dep = t + queue[0][1]
            else:
                next_dep = math.inf
        else:
            end = horizon
            if end > warm:
                area_N += N * (end - max(last, warm))
                area_busy += (1 if N >= 1 else 0) * (end - max(last, warm))
            break
    win = horizon - warm
    L = area_N / win
    busy_frac = area_busy / win
    W = wait_sum / dep if dep else 0.0
    p_wait = wait_n / dep if dep else 0.0
    return L, W, busy_frac, p_wait, arr_in_win, dep, 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=8000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam_hr = 4.0
    smin = 6.0
    if a.pert == "lam_up": lam_hr *= 1.1
    elif a.pert == "mu_up": smin /= 1.1
    elif a.pert == "c_up": smin /= 2.0
    lam = lam_hr / 60.0
    horizon = a.horizon
    warm = horizon * 0.25
    win = horizon - warm
    Ls, Ws, BFs, PWs = [], [], [], []
    seeds_used = 0
    arr_tot = dep_tot = blk_tot = 0
    seed_list = []
    for k in range(a.seeds):
        s = a.seed_start + k
        L, W, bf, pw, ar, dp, bl = run_seed(s, horizon, warm, lam, smin)
        seed_list.append(s)
        Ls.append(L); Ws.append(W); BFs.append(bf); PWs.append(pw)
        arr_tot += ar; dep_tot += dp; blk_tot += bl
        seeds_used += 1
    n = seeds_used
    out = {
        "L": sum(Ls)/n, "W": sum(Ws)/n, "busy_frac": sum(BFs)/n,
        "busy_util": sum(BFs)/n, "busy_occupied": sum(BFs)/n,
        "runtime_units": win, "seed_list": seed_list, "seeds_used": n,
        "time_unit": "minute", "win": win,
        "arr": arr_tot/n, "dep": dep_tot/n, "blk": blk_tot/n,
        "dep_rate": dep_tot/n/win*60.0, "lam_eff": lam_hr,
        "p_loss": blk_tot/n/max(arr_tot,1), "p_wait": sum(PWs)/n,
        "per_seed_L": Ls, "per_seed_W": Ws,
        "per_seed_busy_frac": BFs, "per_seed_p_loss": [0.0]*n,
        "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
