import argparse, json, random, math, sys

def run(seed, horizon, lam, service, warmfrac):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    warm = horizon * warmfrac
    area_n = 0.0
    area_busy = 0.0
    tprev = 0.0
    acc = False
    arr_c = 0
    dep_c = 0
    wait_sum = 0.0
    soj_sum = 0.0
    waited = 0
    queue = []
    while t < horizon:
        t = min(next_arr, next_dep)
        if t > horizon:
            t = horizon
        if t >= warm:
            area_n += n * (t - tprev)
            area_busy += (1 if n >= 1 else 0) * (t - tprev)
            acc = True
        tprev = t
        if t >= horizon:
            break
        if next_arr <= next_dep:
            ta = t
            st = service
            if n == 0:
                next_dep = ta + st
                queue.append((ta, st))
                n += 1
                if acc:
                    arr_c += 1
            else:
                queue.append((ta, st))
                n += 1
                if acc:
                    arr_c += 1
            next_arr = ta + rng.expovariate(lam)
        else:
            a, st = queue.pop(0)
            n -= 1
            if queue:
                next_dep = t + queue[0][1]
            else:
                next_dep = math.inf
            if acc:
                dep_c += 1
                soj_sum += t - a
                if t - a > st + 1e-12 or t - a > 1e-9 and a != t:
                    pass
        if acc and t < horizon:
            pass
    # recompute waited/p_wait needs tracking; redo simple second pass flags
    return area_n, area_busy, arr_c, dep_c, soj_sum

def run2(seed, horizon, lam, service, warmfrac):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = math.inf
    warm = horizon * warmfrac
    area_n = 0.0
    area_busy = 0.0
    tprev = 0.0
    arr_c = 0
    dep_c = 0
    soj_sum = 0.0
    waited = 0
    queue = []
    while True:
        t = min(next_arr, next_dep, horizon)
        if t >= warm:
            area_n += n * (t - tprev)
            area_busy += (1 if n >= 1 else 0) * (t - tprev)
        tprev = t
        if t >= horizon:
            break
        if next_arr <= next_dep:
            ta = t
            n += 1
            queue.append(ta)
            if t >= warm:
                arr_c += 1
                if n >= 2:
                    waited += 1
            if n == 1:
                next_dep = ta + service
            next_arr = ta + rng.expovariate(lam)
        else:
            a = queue.pop(0)
            n -= 1
            if queue:
                next_dep = t + service
            else:
                next_dep = math.inf
            if t >= warm:
                dep_c += 1
                soj_sum += t - a
    win = horizon - warm
    return area_n, area_busy, arr_c, dep_c, soj_sum, waited, win

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100000)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    horizon = float(a.horizon)
    base_lam = 4.0
    base_mu = 12.0
    base_c = 1
    lam, mu, c = base_lam, base_mu, base_c
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c += 1
    unit = "minute"
    lam_m = lam / 60.0
    service = 5.0
    warmfrac = 0.25
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot = [0.0] * 6
    for s in seeds:
        area_n, area_busy, arr_c, dep_c, soj_sum, waited, win = run2(s, horizon, lam_m, service, warmfrac)
        L = area_n / win
        depd = dep_c
        W = soj_sum / depd if depd else 0.0
        bf = area_busy / win
        pl = 0.0
        pw = waited / arr_c if arr_c else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        seed_list.append(s)
        tot[0] += area_n; tot[1] += area_busy; tot[2] += arr_c
        tot[3] += dep_c; tot[4] += soj_sum; tot[5] += waited
    ns = len(seeds)
    win = horizon * (1 - warmfrac)
    L = tot[0] / (ns * win)
    W = (tot[4] / tot[3]) if tot[3] else 0.0
    bf = tot[1] / (ns * win)
    arr = tot[2] / ns
    dep = tot[3] / ns
    blk = 0.0
    dep_rate = dep / win
    lam_eff = dep_rate
    p_loss = 0.0
    p_wait = (tot[5] / tot[2]) if tot[2] else 0.0
    out = {
        "L": L, "W": W, "busy_frac": bf, "busy_util": bf,
        "busy_occupied": bf, "pi0": 1 - bf,
        "runtime_units": unit, "seed_list": seed_list,
        "seeds_used": ns, "time_unit": unit, "win": win,
        "arr": arr, "blk": blk, "dep": dep, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
