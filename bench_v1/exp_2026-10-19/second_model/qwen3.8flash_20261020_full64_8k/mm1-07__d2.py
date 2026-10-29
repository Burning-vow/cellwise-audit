import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 8.0
    mu_base = 60.0 / 6.0
    c = 1

    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        c = 2
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    horizon = args.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    seed_list = []

    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end_times = []
        n_in_sys = 0
        busy_periods = 0.0
        wait_count = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        area_L = 0.0
        last_event_time = 0.0
        events = []
        while True:
            if next_arr < float('inf'):
                ev_type = 'arr'
                ev_time = next_arr
            else:
                ev_type = 'dep'
                ev_time = min(service_end_times) if service_end_times else float('inf')
            if ev_time > horizon:
                break
            dt = ev_time - last_event_time
            if last_event_time >= win_start and dt > 0:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    busy_periods += dt
            if ev_type == 'arr':
                t = ev_time
                dur = rng.expovariate(mu)
                if len(queue) + n_in_sys < c:
                    n_in_sys += 1
                    start_service = max(t, last_event_time)
                    end_service = t + dur
                    service_end_times.append(end_service)
                    queue.append((t, dur))
                    arr_count += 1
                else:
                    blk_count += 1
                    arr_count += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = ev_time
                idx = service_end_times.index(ev_time)
                service_end_times.pop(idx)
                if queue:
                    cust = queue.pop(0)
                    n_in_sys -= 1
                    dep_count += 1
                    if cust[0] < win_start:
                        pass
                    else:
                        wait_time = t - cust[0]
                        if wait_time > 1e-9:
                            wait_count += 1
                    if len(queue) + n_in_sys < c:
                        new_dur = rng.expovariate(mu)
                        n_in_sys += 1
                        end_service = t + new_dur
                        service_end_times.append(end_service)
                        queue.append((t, new_dur))
                else:
                    n_in_sys -= 1
                    dep_count += 1
            last_event_time = t
        if last_event_time < horizon:
            dt = horizon - last_event_time
            if last_event_time >= win_start and dt > 0:
                area_L += n_in_sys * dt
                if n_in_sys > 0:
                    busy_periods += dt
        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = (area_L / dep_count) if dep_count > 0 else 0.0
        bf_est = busy_periods / win_len if win_len > 0 else 0.0
        pl_est = blk_count / arr_count if arr_count > 0 else 0.0
        pw_est = wait_count / dep_count if dep_count > 0 else 0.0
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        seed_list.append(seed)

    seeds_used = len(per_seed_L)
    avg_L = sum(per_seed_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used > 0 else 0.0
    avg_bf = sum(per_seed_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_pl = sum(per_seed_p_loss) / seeds_used if seeds_used > 0 else 0.0
    avg_pw = sum(per_seed_p_wait) / seeds_used if seeds_used > 0 else 0.0
    avg_arr = total_arr / seeds_used if seeds_used > 0 else 0.0
    avg_dep = total_dep / seeds_used if seeds_used > 0 else 0.0
    avg_blk = total_blk / seeds_used if seeds_used > 0 else 0.0
    dep_rate = avg_dep / win_len * 60.0 if win_len > 0 else 0.0
    lam_eff = dep_rate
    p_loss = avg_pl
    busy_util = avg_bf
    busy_occupied = avg_bf

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "p_wait": round(avg_pw, 4),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 4)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
