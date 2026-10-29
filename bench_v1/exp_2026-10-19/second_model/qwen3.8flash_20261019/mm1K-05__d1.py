import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    lam_base = 9.0
    mu_base = 60.0 / 6.0
    c = 4

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 5
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    win = H * 0.75
    warmup = H * 0.25

    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arrivals = 0
    all_departures = 0
    all_blocked = 0
    all_wait_count = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        t = 0.0
        queue = []
        service_end = None
        next_arrival = rng.expovariate(lam)
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        wait_count_in_window = 0
        L_area = 0.0
        W_sum = 0.0
        busy_time = 0.0
        last_event_time = 0.0
        current_N = 0

        while t < H:
            if not queue and service_end is None:
                if next_arrival > H:
                    break
                t = next_arrival
                if t >= warmup:
                    dt = t - last_event_time
                    L_area += current_N * dt
                    if current_N > 0:
                        busy_time += dt
                    last_event_time = t
                    current_N += 1
                    dur = rng.expovariate(mu)
                    queue.append((t, dur))
                    service_end = t + dur
                    arrivals_in_window += 1
                    next_arrival = t + rng.expovariate(lam)
                else:
                    t = next_arrival
                    if t >= warmup:
                        dt = t - last_event_time
                        L_area += current_N * dt
                        if current_N > 0:
                            busy_time += dt
                        last_event_time = t
                        current_N += 1
                        dur = rng.expovariate(mu)
                        queue.append((t, dur))
                        service_end = t + dur
                        arrivals_in_window += 1
                        next_arrival = t + rng.expovariate(lam)
                    else:
                        dt = t - last_event_time
                        L_area += current_N * dt
                        if current_N > 0:
                            busy_time += dt
                        last_event_time = t
                        current_N += 1
                        dur = rng.expovariate(mu)
                        queue.append((t, dur))
                        service_end = t + dur
                        next_arrival = t + rng.expovariate(lam)
            else:
                arr_t = next_arrival
                dep_t = service_end if service_end is not None else float('inf')
                if arr_t <= dep_t:
                    t = arr_t
                    if t >= warmup:
                        dt = t - last_event_time
                        L_area += current_N * dt
                        if current_N > 0:
                            busy_time += dt
                        last_event_time = t
                        if current_N < c:
                            current_N += 1
                            dur = rng.expovariate(mu)
                            queue.append((t, dur))
                            if len(queue) == 1:
                                service_end = t + dur
                            arrivals_in_window += 1
                        else:
                            blocked_in_window += 1
                        next_arrival = t + rng.expovariate(lam)
                    else:
                        dt = t - last_event_time
                        L_area += current_N * dt
                        if current_N > 0:
                            busy_time += dt
                        last_event_time = t
                        if current_N < c:
                            current_N += 1
                            dur = rng.expovariate(mu)
                            queue.append((t, dur))
                            if len(queue) == 1:
                                service_end = t + dur
                        else:
                            pass
                        next_arrival = t + rng.expovariate(lam)
                else:
                    t = dep_t
                    if t >= warmup:
                        dt = t - last_event_time
                        L_area += current_N * dt
                        if current_N > 0:
                            busy_time += dt
                        last_event_time = t
                        if queue:
                            arr_time, dur = queue.pop(0)
                            current_N -= 1
                            departures_in_window += 1
                            w = t - arr_time
                            W_sum += w
                            if w > 0:
                                wait_count_in_window += 1
                            if queue:
                                service_end = t + queue[0][1]
                            else:
                                service_end = None
                        else:
                            service_end = None
                    else:
                        dt = t - last_event_time
                        L_area += current_N * dt
                        if current_N > 0:
                            busy_time += dt
                        last_event_time = t
                        if queue:
                            arr_time, dur = queue.pop(0)
                            current_N -= 1
                            if queue:
                                service_end = t + queue[0][1]
                            else:
                                service_end = None
                        else:
                            service_end = None

        dt_final = H - last_event_time
        L_area += current_N * dt_final
        if current_N > 0:
            busy_time += dt_final

        L_est = L_area / win if win > 0 else 0.0
        W_est = (W_sum / departures_in_window * 60.0) if departures_in_window > 0 else 0.0
        bf_est = busy_time / win if win > 0 else 0.0
        pl_est = blocked_in_window / arrivals_in_window if arrivals_in_window > 0 else 0.0
        pw_est = wait_count_in_window / arrivals_in_window if arrivals_in_window > 0 else 0.0

        all_L_area += L_area
        all_W_sum += W_sum
        all_busy_time += busy_time
        all_arrivals += arrivals_in_window
        all_departures += departures_in_window
        all_blocked += blocked_in_window
        all_wait_count += wait_count_in_window
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        seeds_used += 1
        seed_list.append(s)

    total_win = win * seeds_used
    L_avg = all_L_area / total_win if total_win > 0 else 0.0
    W_avg = (all_W_sum / all_departures * 60.0) if all_departures > 0 else 0.0
    bf_avg = all_busy_time / total_win if total_win > 0 else 0.0
    pl_avg = all_blocked / all_arrivals if all_arrivals > 0 else 0.0
    pw_avg = all_wait_count / all_arrivals if all_arrivals > 0 else 0.0
    arr_avg = all_arrivals / seeds_used if seeds_used > 0 else 0.0
    blk_avg = all_blocked / seeds_used if seeds_used > 0 else 0.0
    dep_avg = all_departures / seeds_used if seeds_used > 0 else 0.0
    dep_rate = all_departures / total_win if total_win > 0 else 0.0
    lam_eff = dep_rate
    busy_util = min(bf_avg, 1.0) / c if c > 0 else 0.0
    busy_occupied = bf_avg

    result = {
        "L": round(L_avg, 6),
        "W": round(W_avg, 6),
        "busy_frac": round(bf_avg, 6),
        "p_loss": round(pl_avg, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(pw_avg, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
