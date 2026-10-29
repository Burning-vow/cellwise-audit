import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    N, H, S, pert = a.seeds, a.horizon, a.seed_start, a.pert
    lam = 5.0
    mu_mean = 6.0 / 60.0
    cv = 1.5
    if pert == 'lam_up': lam *= 1.1
    elif pert == 'mu_up': mu_mean /= 1.1
    elif pert == 'c_up': pass
    var = (cv * mu_mean) ** 2
    mean = mu_mean
    if var <= mean**2:
        shape = 1.0; scale = mean
    else:
        shape = (mean**2)/var; scale = var/mean
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    time_unit = "hour"
    seeds_used = 0
    seed_list = []
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    total_arr = 0; total_dep = 0; total_blk = 0
    for i in range(N):
        rng = random.Random(S + i)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end = None
        busy = False
        n_in_sys = 0
        area_n = 0.0
        area_busy = 0.0
        arr_count = 0; dep_count = 0; blk_count = 0
        wait_times = []
        while t < H:
            if not queue and service_end is None:
                if next_arr > H: break
                t = next_arr
                dur = rng.gammavariate(shape, scale)
                queue.append((t, dur))
                arr_count += 1
                next_arr = t + rng.expovariate(lam)
                continue
            events = []
            if next_arr < H: events.append(('arr', next_arr))
            if service_end is not None: events.append(('dep', service_end))
            if not events: break
            etype, etime = min(events, key=lambda x: x[1])
            dt = etime - t
            if t >= H * warmup_frac:
                area_n += n_in_sys * dt
                if busy: area_busy += dt
            t = etime
            if etype == 'arr':
                dur = rng.gammavariate(shape, scale)
                queue.append((t, dur))
                arr_count += 1
                next_arr = t + rng.expovariate(lam)
                n_in_sys += 1
                if not busy:
                    busy = True
                    item = queue.pop(0)
                    start_t = item[0]
                    d = item[1]
                    wait_times.append(t - start_t)
                    service_end = t + d
            elif etype == 'dep':
                dep_count += 1
                n_in_sys -= 1
                if queue:
                    item = queue.pop(0)
                    start_t = item[0]
                    d = item[1]
                    wait_times.append(t - start_t)
                    service_end = t + d
                else:
                    busy = False
                    service_end = None
        if t >= H * warmup_frac:
            dt_final = H - t
            area_n += n_in_sys * dt_final
            if busy: area_busy += dt_final
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum(wait_times) / len(wait_times) * 60 if wait_times else 0
        bf = area_busy / win_len if win_len > 0 else 0
        pl = blk_count / arr_count if arr_count > 0 else 0
        pw = len([w for w in wait_times if w > 0]) / len(wait_times) if wait_times else 0
        all_L.append(L_est); all_W.append(W_est); all_busy_frac.append(bf)
        all_p_loss.append(pl); all_p_wait.append(pw)
        total_arr += arr_count; total_dep += dep_count; total_blk += blk_count
        seeds_used += 1
        seed_list.append(S + i)
    avg_L = sum(all_L) / seeds_used if seeds_used else 0
    avg_W = sum(all_W) / seeds_used if seeds_used else 0
    avg_bf = sum(all_busy_frac) / seeds_used if seeds_used else 0
    avg_pl = sum(all_p_loss) / seeds_used if seeds_used else 0
    avg_pw = sum(all_p_wait) / seeds_used if seeds_used else 0
    avg_arr = total_arr / seeds_used if seeds_used else 0
    avg_dep = total_dep / seeds_used if seeds_used else 0
    avg_blk = total_blk / seeds_used if seeds_used else 0
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    res = {
        "L": round(avg_L, 6), "W": round(avg_W, 6), "busy_frac": round(avg_bf, 6),
        "runtime_units": time_unit, "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": time_unit, "win": round(win_len, 6),
        "arr": round(avg_arr, 6), "blk": round(avg_blk, 6), "busy_util": round(avg_bf, 6),
        "dep": round(avg_dep, 6), "dep_rate": round(dep_rate, 6), "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6), "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x, 6) for x in all_L], "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
