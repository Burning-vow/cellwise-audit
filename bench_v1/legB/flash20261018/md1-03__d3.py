import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    svc = 6.0

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait_n = 0
    tot_wait_sum = 0.0
    tot_served = 0
    tot_waited = 0

    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        waited = 0
        served = 0
        last = 0.0
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait_sum = 0.0
        win_waited = 0
        win_served = 0
        win_start = warm
        win_len = H - warm

        def integrate(now):
            nonlocal area, busy_area, win_area, win_busy, last
            dt = now - last
            if dt > 0:
                area += n * dt
                busy_area += busy * dt
                if now > win_start:
                    lo = max(last, win_start)
                    if now > lo:
                        win_area += n * (now - lo)
                        win_busy += busy * (now - lo)
            last = now

        events = []
        next_arr = rng.expovariate(lam)
        while True:
            if next_arr <= t:
                integrate(next_arr)
                t = next_arr
                n += 1
                arr += 1
                if t >= win_start:
                    win_arr += 1
                st = svc
                if busy < c:
                    busy += 1
                    served += 1
                    if t >= win_start:
                        win_served += 1
                    events.append((t + st,))
                else:
                    queue.append((t, st))
                    blk += 0
                next_arr = t + rng.expovariate(lam)
            else:
                if events:
                    nt = events[0][0]
                    if nt <= next_arr:
                        integrate(nt)
                        t = nt
                        events.pop(0)
                        busy -= 1
                        dep += 1
                        if t >= win_start:
                            win_dep += 1
                        if queue:
                            at, st = queue.pop(0)
                            w = t - at
                            wait_sum += w
                            waited += 1
                            if t >= win_start:
                                win_wait_sum += w
                                win_waited += 1
                            busy += 1
                            served += 1
                            if t >= win_start:
                                win_served += 1
                            events.append((t + st,))
                            events.sort()
                        continue
                if next_arr > H and (not events or events[0][0] > H):
                    integrate(H)
                    break
                if next_arr <= H:
                    integrate(next_arr)
                    t = next_arr
                    n += 1
                    arr += 1
                    if t >= win_start:
                        win_arr += 1
                    st = svc
                    if busy < c:
                        busy += 1
                        served += 1
                        if t >= win_start:
                            win_served += 1
                        events.append((t + st,))
                        events.sort()
                    else:
                        queue.append((t, st))
                    next_arr = t + rng.expovariate(lam)
                else:
                    nt = events[0][0]
                    integrate(nt)
                    t = nt
                    events.pop(0)
                    busy -= 1
                    dep += 1
                    if t >= win_start:
                        win_dep += 1
                    if queue:
                        at, st = queue.pop(0)
                        w = t - at
                        wait_sum += w
                        waited += 1
                        if t >= win_start:
                            win_wait_sum += w
                            win_waited += 1
                        busy += 1
                        served += 1
                        if t >= win_start:
                            win_served += 1
                        events.append((t + st,))
                        events.sort()

        Ls = win_area / win_len if win_len > 0 else 0.0
        Ws = (win_wait_sum + win_served * svc) / win_served if win_served > 0 else 0.0
        bfs = win_busy / win_len if win_len > 0 else 0.0
        pls = win_blk / win_arr if win_arr > 0 else 0.0
        pws = win_waited / win_served if win_served > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_win += win_len
        tot_wait_sum += win_wait_sum
        tot_served += win_served
        tot_waited += win_waited

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_wait_sum + tot_served * svc) / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac / c
    busy_occupied = busy_frac
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = tot_arr / (tot_win / 60.0) if tot_win > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "runtime_units": "minute",
        "seed_list": [a.seed_start + i for i in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "minute",
        "win": tot_win / a.seeds if a.seeds > 0 else 0.0,
        "arr": tot_arr / a.seeds if a.seeds > 0 else 0.0,
        "dep": tot_dep / a.seeds if a.seeds > 0 else 0.0,
        "blk": tot_blk / a.seeds if a.seeds > 0 else 0.0,
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
