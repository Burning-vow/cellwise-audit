import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaW = 0.0
    tot_win = 0.0
    tot_busy = 0.0
    tot_occ = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaW = 0.0
        win = 0.0
        arr = dep = blk = 0
        busy_area = occ_area = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        pw_cnt = 0
        arr_cnt = 0
        last = 0.0
        while True:
            if next_arr <= t or not queue:
                if next_arr > H and not queue:
                    break
                if next_arr <= t:
                    dt = next_arr - last
                    if t > warm:
                        w = min(dt, t - warm)
                        if w > 0:
                            areaN += n * w
                            busy_area += min(n, c) * w
                            occ_area += (1 if busy > 0 else 0) * w
                            win += w
                    last = next_arr
                    t = next_arr
                    if t > H:
                        break
                    svc = rng.expovariate(mu)
                    if t > warm:
                        arr += 1
                        arr_cnt += 1
                        if n >= c:
                            pw_cnt += 1
                    if n < c:
                        n += 1
                        busy += 1
                        queue.append((t, t + svc, svc))
                    else:
                        if t > warm:
                            blk += 1
                        n += 1
                        queue.append((t, t + svc, svc))
                    next_arr = t + rng.expovariate(lam)
                else:
                    break
            else:
                at, dt_end, svc = queue[0]
                dt = dt_end - last
                if t > warm:
                    w = min(dt, t - warm)
                    if w > 0:
                        areaN += n * w
                        busy_area += min(n, c) * w
                        occ_area += (1 if busy > 0 else 0) * w
                        win += w
                last = dt_end
                t = dt_end
                queue.pop(0)
                n -= 1
                busy -= 1
                if t > warm:
                    dep += 1
                    wait_sum += (dt_end - at)
                    wait_cnt += 1
                if n >= c and queue:
                    pass
                while n < c and queue:
                    at2, dt2, svc2 = queue[0]
                    if dt2 <= t:
                        queue.pop(0)
                        n -= 1
                        busy -= 1
                        if t > warm:
                            dep += 1
                            wait_sum += (dt2 - at2)
                            wait_cnt += 1
                    else:
                        break
                if not queue:
                    if next_arr > H:
                        break
                    if next_arr > t:
                        dt = next_arr - last
                        if t > warm:
                            w = min(dt, t - warm)
                            if w > 0:
                                areaN += n * w
                                busy_area += min(n, c) * w
                                occ_area += (1 if busy > 0 else 0) * w
                                win += w
                        last = next_arr
                        t = next_arr
                        if t > H:
                            break
                        svc = rng.expovariate(mu)
                        if t > warm:
                            arr += 1
                            arr_cnt += 1
                            if n >= c:
                                pw_cnt += 1
                        if n < c:
                            n += 1
                            busy += 1
                            queue.append((t, t + svc, svc))
                        else:
                            if t > warm:
                                blk += 1
                            n += 1
                            queue.append((t, t + svc, svc))
                        next_arr = t + rng.expovariate(lam)
                else:
                    at2, dt2, svc2 = queue[0]
                    if dt2 <= t:
                        continue
                    if next_arr < dt2:
                        dt = next_arr - last
                        if t > warm:
                            w = min(dt, t - warm)
                            if w > 0:
                                areaN += n * w
                                busy_area += min(n, c) * w
                                occ_area += (1 if busy > 0 else 0) * w
                                win += w
                        last = next_arr
                        t = next_arr
                        if t > H:
                            break
                        svc = rng.expovariate(mu)
                        if t > warm:
                            arr += 1
                            arr_cnt += 1
                            if n >= c:
                                pw_cnt += 1
                        if n < c:
                            n += 1
                            busy += 1
                            queue.append((t, t + svc, svc))
                        else:
                            if t > warm:
                                blk += 1
                            n += 1
                            queue.append((t, t + svc, svc))
                        next_arr = t + rng.expovariate(lam)
                    else:
                        dt = dt2 - last
                        if t > warm:
                            w = min(dt, t - warm)
                            if w > 0:
                                areaN += n * w
                                busy_area += min(n, c) * w
                                occ_area += (1 if busy > 0 else 0) * w
                                win += w
                        last = dt2
                        t = dt2
                        queue.pop(0)
                        n -= 1
                        busy -= 1
                        if t > warm:
                            dep += 1
                            wait_sum += (dt2 - at2)
                            wait_cnt += 1
                        while n < c and queue:
                            at3, dt3, svc3 = queue[0]
                            if dt3 <= t:
                                queue.pop(0)
                                n -= 1
                                busy -= 1
                                if t > warm:
                                    dep += 1
                                    wait_sum += (dt3 - at3)
                                    wait_cnt += 1
                            else:
                                break
                        if not queue and next_arr > H:
                            break

        if win <= 0:
            win = 1e-9
        L = areaN / win
        W = (wait_sum / wait_cnt) if wait_cnt > 0 else 0.0
        bf = (busy_area / win) / c
        pl = (blk / arr_cnt) if arr_cnt > 0 else 0.0
        pw = (pw_cnt / arr_cnt) if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_areaN += areaN
        tot_areaW += wait_sum
        tot_win += win
        tot_busy += busy_area
        tot_occ += occ_area

    n_seeds = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    W = (tot_areaW / tot_dep) if tot_dep > 0 else 0.0
    busy_frac = (tot_busy / tot_win) / c if tot_win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = (tot_occ / tot_win) if tot_win > 0 else 0.0
    p_wait = sum(per_pw) / n_seeds if n_seeds > 0 else 0.0
    p_loss = sum(per_pl) / n_seeds if n_seeds > 0 else 0.0
    arr_avg = tot_arr / n_seeds
    dep_avg = tot_dep / n_seeds
    blk_avg = tot_blk / n_seeds
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) * 60.0 if tot_win > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "p_wait": p_wait,
        "p_loss": p_loss,
        "runtime_units": "minute",
        "time_unit": "minute",
        "win": tot_win / n_seeds if n_seeds > 0 else 0.0,
        "seed_list": seeds,
        "seeds_used": n_seeds,
        "arr": arr_avg,
        "dep": dep_avg,
        "blk": blk_avg,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
