import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait_n = 0.0
    tot_wait_sum = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        wait_n = 0
        win_start = warm
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait_sum = 0.0
        win_wait_n = 0
        last_t = 0.0
        # event queue: list of (time, kind, payload)
        # kind 0 = arrival, 1 = departure
        events = []
        # schedule first arrival
        t_next_arr = rng.expovariate(lam)
        events.append((t_next_arr, 0, None))
        # server free times per server
        free = [0.0] * c
        # pending customers: (arrival_time, service_time)
        queue = []
        # active departures: list of (dep_time, arrival_time)
        active = []
        while events:
            events.sort(key=lambda e: e[0])
            ev = events.pop(0)
            et, kind, payload = ev
            if et > H:
                break
            # integrate area up to et
            dt = et - last_t
            if last_t >= win_start:
                win_area += n * dt
                win_busy += busy * dt
            elif et > win_start:
                win_area += n * (et - win_start)
                win_busy += busy * (et - win_start)
            area += n * dt
            busy_area += busy * dt
            last_t = et
            t = et
            if kind == 0:
                arr += 1
                if t >= win_start:
                    win_arr += 1
                st = rng.expovariate(mu)
                # try to start service
                started = False
                for i in range(c):
                    if free[i] <= t + 1e-12:
                        free[i] = t + st
                        dep_t = t + st
                        events.append((dep_t, 1, (t, st)))
                        started = True
                        break
                if not started:
                    queue.append((t, st))
                n += 1
                # schedule next arrival
                t_next_arr = t + rng.expovariate(lam)
                events.append((t_next_arr, 0, None))
            else:
                at, st = payload
                dep += 1
                if t >= win_start:
                    win_dep += 1
                w = t - at
                wait_sum += w
                wait_n += 1
                if t >= win_start:
                    win_wait_sum += w
                    win_wait_n += 1
                n -= 1
                # start next from queue
                if queue:
                    qa, qs = queue.pop(0)
                    # find free server
                    for i in range(c):
                        if free[i] <= t + 1e-12:
                            free[i] = t + qs
                            events.append((t + qs, 1, (qa, qs)))
                            break
        # final integration to H
        if last_t < H:
            dt = H - last_t
            if last_t >= win_start:
                win_area += n * dt
                win_busy += busy * dt
            elif H > win_start:
                win_area += n * (H - win_start)
                win_busy += busy * (H - win_start)
            area += n * dt
            busy_area += busy * dt
            last_t = H

        win_len = H - win_start
        Ls = win_area / win_len if win_len > 0 else 0.0
        Ws = (win_wait_sum / win_wait_n) if win_wait_n > 0 else 0.0
        bfs = win_busy / win_len if win_len > 0 else 0.0
        pls = win_blk / win_arr if win_arr > 0 else 0.0
        pws = win_wait_n / win_arr if win_arr > 0 else 0.0
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
        tot_wait_n += win_wait_n

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_sum / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac / c
    busy_occupied = busy_frac
    arr_avg = tot_arr / len(seeds)
    dep_avg = tot_dep / len(seeds)
    blk_avg = tot_blk / len(seeds)
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        "L": L, "W": W, "busy_frac": busy_frac,
        "runtime_units": H, "seed_list": seeds, "seeds_used": len(seeds),
        "time_unit": "minute", "win": tot_win / len(seeds),
        "arr": arr_avg, "blk": blk_avg, "busy_util": busy_util,
        "busy_occupied": busy_occupied, "dep": dep_avg,
        "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_loss": p_loss, "p_wait": p_wait,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
