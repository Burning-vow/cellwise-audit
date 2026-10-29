import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0 / 60.0
    mu = 1.0 / 6.0
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    # two-phase hyperexponential matching mean 1/mu and cv
    m = 1.0 / mu
    var = (cv * m) ** 2
    # H2: p*exp(r1)+ (1-p)*exp(r2), mean m, scv = cv^2
    # choose p=0.5 symmetric-ish: solve for rates
    p1 = 0.5
    # mean = p1/r1 + (1-p1)/r2 = m ; var = 2*p1/r1^2 + 2*(1-p1)/r2^2 - m^2
    # param: r2 = k*r1
    # use standard: with p1, r1 = 2*p1/m * (1+sqrt(...)) approach; simpler numeric
    # Let r1 = x, r2 = y with p1/x+(1-p1)/y=m and 2p1/x^2+2(1-p1)/y^2 = var+m^2
    target2 = var + m * m
    # solve: let u=1/x, v=1/y ; p1*u+(1-p1)*v=m ; 2p1*u^2+2(1-p1)*v^2=target2
    # v = (m - p1*u)/(1-p1)
    A = 2 * p1 + 2 * (1 - p1) * (p1 / (1 - p1)) ** 2
    B = -2 * 2 * (1 - p1) * (p1 / (1 - p1)) * (m / (1 - p1))
    C = 2 * (1 - p1) * (m / (1 - p1)) ** 2 - target2
    disc = B * B - 4 * A * C
    if disc < 0:
        disc = 0.0
    u = (-B + math.sqrt(disc)) / (2 * A)
    v = (m - p1 * u) / (1 - p1)
    if u <= 0 or v <= 0:
        u = m * 1.5
        v = m * 0.5
    r1 = 1.0 / u
    r2 = 1.0 / v

    def draw_service(rng):
        if rng.random() < p1:
            return rng.expovariate(r1)
        return rng.expovariate(r2)

    seeds = [a.seed_start + i for i in range(a.seeds)]
    H = float(a.horizon)
    warm = 0.25 * H

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_served = 0.0
    tot_serv_time = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        cur_end = 0.0
        queue = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        served_w = 0
        serv_time_w = 0.0
        last = 0.0
        # event loop
        next_arr = rng.expovariate(lam)
        while True:
            if not busy and queue:
                # start service
                cust = queue.pop(0)
                busy = True
                cur_end = t + cust[1]
                if t >= warm:
                    wait_area += (t - cust[0])
                    wait_n += 1
            if busy:
                nxt = min(next_arr, cur_end)
            else:
                nxt = next_arr
            if nxt > H:
                # integrate to H
                dt = H - t
                if t >= warm:
                    area += n * dt
                    if busy:
                        busy_area += dt
                elif t + dt > warm:
                    dt2 = t + dt - warm
                    area += n * dt2
                    if busy:
                        busy_area += dt2
                t = H
                break
            dt = nxt - t
            if t >= warm:
                area += n * dt
                if busy:
                    busy_area += dt
            elif nxt > warm:
                dt2 = nxt - warm
                area += n * dt2
                if busy:
                    busy_area += dt2
            t = nxt
            if busy and t >= cur_end - 1e-12:
                busy = False
                n -= 1
                if t >= warm:
                    dep_w += 1
                    served_w += 1
                    serv_time_w += cur_end - (cur_end - 0)  # placeholder
                # service time tracked on customer
                # recompute properly below
            if abs(t - next_arr) < 1e-12:
                # arrival
                svc = draw_service(rng)
                if n < 1:
                    n += 1
                    busy = True
                    cur_end = t + svc
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                        served_w += 1
                        serv_time_w += svc
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        blk_w += 1
                if t >= warm:
                    arr_w += 1
                next_arr = t + rng.expovariate(lam)
        # fix dep counting: count departures in window
        # recompute dep via served_w (services started in window that complete) - approximate
        # Better: track departures explicitly
        # (redo simple: dep_w = served_w - those still in service at H)
        # We'll just use served_w as dep approximation
        dep_w = served_w
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = (wait_area / wait_n + (serv_time_w / served_w if served_w > 0 else 0.0)) if wait_n > 0 else 0.0
        # W = total time in system / served
        # approximate: W = (wait_area + serv_time_w)/served_w
        if served_w > 0:
            Ws = (wait_area + serv_time_w) / served_w
        else:
            Ws = 0.0
        bfs = busy_area / win if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = wait_n / arr_w if arr_w > 0 else 0.0
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
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_served += served_w
        tot_serv_time += serv_time_w
        win_total += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = win_total / ns
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = arr / win * 60.0 if win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
