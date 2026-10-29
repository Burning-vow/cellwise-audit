import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0 / 60.0
    mean_s = 6.0
    cv = 3.0
    var_s = (cv * mean_s) ** 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
        var_s = (cv * mean_s) ** 2
    elif a.pert == 'c_up':
        pass

    # two-phase hyperexponential matching mean and var
    # mixture of two exponentials with rates r1, r2, prob p
    # choose p=0.5, solve for rates
    p = 0.5
    m = mean_s
    v = var_s
    # E[S]=p/r1+(1-p)/r2=m ; E[S^2]=2p/r1^2+2(1-p)/r2^2 = v+m^2
    # let x=1/r1, y=1/r2
    # p x + (1-p) y = m
    # 2p x^2 + 2(1-p) y^2 = v + m^2
    A = p
    B = 1 - p
    # y = (m - A x)/B
    # 2A x^2 + 2B ((m-Ax)/B)^2 = v+m^2
    # 2A x^2 + 2 (m-Ax)^2/B = v+m^2
    # multiply B: 2AB x^2 + 2(m-Ax)^2 = B(v+m^2)
    # 2AB x^2 + 2m^2 -4mAx +2A^2x^2 = B(v+m^2)
    # (2AB+2A^2) x^2 -4mA x + 2m^2 - B(v+m^2)=0
    qa = 2*A*B + 2*A*A
    qb = -4*m*A
    qc = 2*m*m - B*(v + m*m)
    disc = qb*qb - 4*qa*qc
    if disc < 0:
        disc = 0.0
    sq = math.sqrt(disc)
    x1 = (-qb + sq) / (2*qa)
    x2 = (-qb - sq) / (2*qa)
    # pick positive x giving positive y
    cands = []
    for x in (x1, x2):
        if x > 0:
            y = (m - A*x)/B
            if y > 0:
                cands.append((x, y))
    if not cands:
        x = m
        y = m
    else:
        x, y = cands[0]
    r1 = 1.0/x
    r2 = 1.0/y

    horizon = float(a.horizon)
    warm = 0.25 * horizon
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
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        busy = False
        busy_until = 0.0
        queue = []
        # event loop
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        last_t = 0.0
        # we integrate area over window [warm, horizon]
        while True:
            # next event time
            if busy:
                next_dep = busy_until
            else:
                next_dep = float('inf')
            if queue:
                # if busy, queue waits; if not busy, start service immediately at t
                pass
            if not busy and queue:
                # start service now
                cust = queue.pop(0)
                busy = True
                busy_until = t + cust['s']
                # waiting time
                w = t - cust['arr']
                if t >= warm:
                    wait_area += w
                    wait_n += 1
                continue
            ev = min(next_arr, next_dep)
            if ev > horizon:
                # integrate to horizon
                dt = horizon - last_t
                if dt > 0 and last_t >= warm:
                    area += dt * (len(queue) + (1 if busy else 0))
                    busy_area += dt * (1 if busy else 0)
                elif dt > 0 and last_t < warm and horizon > warm:
                    dt2 = horizon - warm
                    area += dt2 * (len(queue) + (1 if busy else 0))
                    busy_area += dt2 * (1 if busy else 0)
                break
            # integrate from last_t to ev
            dt = ev - last_t
            if dt > 0:
                n = len(queue) + (1 if busy else 0)
                if last_t >= warm:
                    area += dt * n
                    busy_area += dt * (1 if busy else 0)
                elif ev > warm:
                    dt2 = ev - warm
                    area += dt2 * n
                    busy_area += dt2 * (1 if busy else 0)
            last_t = ev
            t = ev
            if ev == next_arr:
                arr_c += 1
                # sample service time now
                if rng.random() < p:
                    st = rng.expovariate(r1)
                else:
                    st = rng.expovariate(r2)
                cust = {'arr': t, 's': st}
                if not busy:
                    busy = True
                    busy_until = t + st
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                else:
                    queue.append(cust)
                next_arr = t + rng.expovariate(lam)
            else:
                # departure
                dep_c += 1
                busy = False
                if queue:
                    cust = queue.pop(0)
                    busy = True
                    busy_until = t + cust['s']
                    w = t - cust['arr']
                    if t >= warm:
                        wait_area += w
                        wait_n += 1
        win_len = horizon - warm
        L = area / win_len if win_len > 0 else 0.0
        bf = busy_area / win_len if win_len > 0 else 0.0
        W = wait_area / wait_n if wait_n > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_n / arr_c if arr_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win_len

    n = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / n
    dep = tot_dep / n
    blk = tot_blk / n
    win = tot_win / n
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    lam_eff = arr / win * 60.0 if win > 0 else 0.0
    p_loss = blk / arr if arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': horizon,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'dep': dep,
        'blk': blk,
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
