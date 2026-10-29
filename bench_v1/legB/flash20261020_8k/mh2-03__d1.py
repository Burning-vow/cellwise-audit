import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 3.0 / 60.0
    mu = 1.0 / 6.0
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    # two-phase hyperexponential matching mean 1/mu and cv
    # cv^2 = 2*p/(mu1^2) ... use balanced means: p1=0.5
    # For H2 with p1=p2=0.5: E[S]=0.5/m1+0.5/m2, E[S^2]=p1*2/m1^2+p2*2/m2^2
    # cv^2 = E[S^2]/E[S]^2 - 1
    # choose m1 = m2*(1+r) style; solve with p=0.5
    # Let mean m = 1/mu. cv^2 = 2*(p1/m1^2+p2/m2^2)*m^2 - 1
    # with p1=p2=0.5: cv^2+1 = (1/m1^2+1/m2^2)*m^2
    # let m1 = m*(1-d), m2 = m*(1+d) -> 1/(1-d)^2+1/(1+d)^2 = 2*(cv^2+1)
    target = 2.0 * (cv * cv + 1.0)
    # solve 1/(1-d)^2 + 1/(1+d)^2 = target
    lo, hi = 0.0, 0.999
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        v = 1.0 / ((1 - mid) ** 2) + 1.0 / ((1 + mid) ** 2)
        if v > target:
            lo = mid
        else:
            hi = mid
    d = 0.5 * (lo + hi)
    m = 1.0 / mu
    m1 = m * (1 - d)
    m2 = m * (1 + d)
    r1 = 1.0 / m1
    r2 = 1.0 / m2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_served = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        served_cnt = 0
        last_t = 0.0
        # event loop
        while True:
            # next arrival
            ia = rng.expovariate(lam)
            ta = t + ia
            if ta > H and next_dep > H:
                # integrate to H
                dt = H - t
                if t < H:
                    if t >= warm:
                        area += n * dt
                        busy_area += (1 if busy else 0) * dt
                break
            # determine next event
            if ta <= next_dep:
                # arrival at ta
                dt = ta - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                elif ta > warm:
                    dt2 = ta - warm
                    area += n * dt2
                    busy_area += (1 if busy else 0) * dt2
                t = ta
                if t > H:
                    break
                # sample service time now
                if rng.random() < 0.5:
                    st = rng.expovariate(r1)
                else:
                    st = rng.expovariate(r2)
                if t >= warm:
                    arr_w += 1
                if not busy:
                    busy = True
                    next_dep = t + st
                    if t >= warm:
                        served_cnt += 1
                else:
                    # queue: but c=1, so it waits; we need to track queue
                    # use a FIFO queue of (arrival_time, service_time)
                    pass
                # We'll implement with explicit queue
                # redo: simpler approach below
                break
            else:
                break
        # The above is messy; rewrite cleanly
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        served_cnt = 0
        queue = []
        # schedule first arrival
        t_next_arr = rng.expovariate(lam)
        while True:
            # next event time
            if t_next_arr <= next_dep:
                te = t_next_arr
                is_arr = True
            else:
                te = next_dep
                is_arr = False
            if te > H:
                # integrate to H
                dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += (1 if busy else 0) * dt
                elif t + dt > warm:
                    dt2 = t + dt - warm
                    area += n * dt2
                    busy_area += (1 if busy else 0) * dt2
                break
            dt = te - t
            if t >= warm:
                area += n * dt
                busy_area += (1 if busy else 0) * dt
            elif te > warm:
                dt2 = te - warm
                area += n * dt2
                busy_area += (1 if busy else 0) * dt2
            t = te
            if is_arr:
                # sample service time at arrival
                if rng.random() < 0.5:
                    st = rng.expovariate(r1)
                else:
                    st = rng.expovariate(r2)
                if t >= warm:
                    arr_w += 1
                if not busy:
                    busy = True
                    n += 1
                    next_dep = t + st
                    if t >= warm:
                        served_cnt += 1
                else:
                    queue.append((t, st))
                    n += 1
                t_next_arr = t + rng.expovariate(lam)
            else:
                # departure
                if t >= warm:
                    dep_w += 1
                n -= 1
                if queue:
                    at, st = queue.pop(0)
                    next_dep = t + st
                    if t >= warm:
                        wait_sum += (t - at)
                        waited_cnt += 1
                        served_cnt += 1
                else:
                    busy = False
                    next_dep = float('inf')
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (area / dep_w) if dep_w > 0 else 0.0
        bfs = busy_area / win if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = waited_cnt / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_served += served_cnt

    ns = len(seeds)
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / ns) / win if win > 0 else 0.0
    lam_eff = (tot_arr / ns) / win if win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": win,
        "arr": arr,
        "blk": blk,
        "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "dep": dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
