import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0 / 60.0
    mu = 1.0 / 12.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
        cap = 5

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_win = 0.0
    tot_areaN = tot_areaBusy = tot_areaOcc = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaBusy = areaOcc = 0.0
        wsum = 0.0
        served = 0
        waited = 0
        arr_w = dep_w = blk_w = 0
        last = 0.0
        while True:
            if not queue:
                if next_arr > H:
                    dt = H - t
                    if t < H:
                        if t >= warm:
                            areaN += n * dt
                            areaBusy += (1 if busy > 0 else 0) * dt
                            areaOcc += min(n, c) * dt
                    t = H
                    break
                dt = next_arr - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += (1 if busy > 0 else 0) * dt
                    areaOcc += min(n, c) * dt
                t = next_arr
                if t > H:
                    break
                # arrival
                if t >= warm:
                    arr_w += 1
                if n < cap:
                    n += 1
                    st = rng.expovariate(mu)
                    queue.append([t, st])
                    if busy < c:
                        busy += 1
                        queue[-1].append(t)
                else:
                    if t >= warm:
                        blk_w += 1
                next_arr = t + rng.expovariate(lam)
            else:
                # next event: arrival or departure
                dep_t = queue[0][2] if len(queue[0]) > 2 else None
                # find earliest departure among in-service
                best = None
                for q in queue:
                    if len(q) > 2:
                        d = q[2] + q[1]
                        if best is None or d < best:
                            best = d
                if best is None:
                    # no one in service, start service
                    q = queue[0]
                    q.append(t)
                    busy += 1
                    continue
                if next_arr < best:
                    dt = next_arr - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                        areaOcc += min(n, c) * dt
                    t = next_arr
                    if t > H:
                        break
                    if t >= warm:
                        arr_w += 1
                    if n < cap:
                        n += 1
                        st = rng.expovariate(mu)
                        queue.append([t, st])
                        if busy < c:
                            busy += 1
                            queue[-1].append(t)
                    else:
                        if t >= warm:
                            blk_w += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    dt = best - t
                    if t >= warm:
                        areaN += n * dt
                        areaBusy += (1 if busy > 0 else 0) * dt
                        areaOcc += min(n, c) * dt
                    t = best
                    if t > H:
                        break
                    # departures at time t
                    done = [q for q in queue if len(q) > 2 and abs(q[2] + q[1] - t) < 1e-12]
                    for q in done:
                        queue.remove(q)
                        n -= 1
                        busy -= 1
                        if t >= warm:
                            dep_w += 1
                            wsum += (q[2] - q[0])
                            served += 1
                            if q[2] > q[0]:
                                waited += 1
                    # start service for waiting
                    while busy < c and queue:
                        q = queue[0]
                        if len(q) > 2:
                            break
                        q.append(t)
                        busy += 1
        win = H - warm
        tot_win += win
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaBusy += areaBusy
        tot_areaOcc += areaOcc
        tot_wait += wsum
        tot_served += served
        tot_waited += waited
        per_L.append(areaN / win if win > 0 else 0.0)
        per_W.append(wsum / served if served > 0 else 0.0)
        per_bf.append(areaBusy / win if win > 0 else 0.0)
        per_pl.append(blk_w / arr_w if arr_w > 0 else 0.0)
        per_pw.append(waited / served if served > 0 else 0.0)

    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_areaBusy / tot_win if tot_win > 0 else 0.0
    busy_util = tot_areaOcc / (c * tot_win) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    lam_eff = arr / tot_win if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': tot_win / len(seeds),
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
