import argparse, json, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert

    lam_base = 8.0
    mu_base = 60.0 / 5.0
    c = 1

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    win = H * 0.75
    warmup = H * 0.25

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_customers = 0

    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end = None
        arr_count = 0
        dep_count = 0
        blk_count = 0
        area_L = 0.0
        area_busy = 0.0
        last_event_t = 0.0
        current_N = 0
        is_busy = False
        wait_times = []
        sys_times = []

        while t < H:
            if next_arr < (service_end if service_end is not None else float('inf')):
                dt = next_arr - t
                if t >= warmup:
                    area_L += current_N * dt
                    if is_busy:
                        area_busy += dt
                t = next_arr
                arr_count += 1
                if len(queue) == 0 and not is_busy:
                    svc_dur = 1.0 / mu
                    service_end = t + svc_dur
                    is_busy = True
                    sys_times.append(svc_dur)
                    wait_times.append(0.0)
                    dep_count += 1
                    t = service_end
                    service_end = None
                    is_busy = False
                    if t >= warmup:
                        area_L += current_N * 0.0
                        if is_busy:
                            area_busy += 0.0
                    current_N -= 1
                    if queue:
                        cust = queue.pop(0)
                        svc_dur = cust['svc']
                        service_end = t + svc_dur
                        is_busy = True
                        w = t - cust['arr_t']
                        s = svc_dur + w
                        sys_times.append(s)
                        wait_times.append(w)
                        dep_count += 1
                        t = service_end
                        service_end = None
                        is_busy = False
                        current_N -= 1
                        while queue and not is_busy:
                            cust = queue.pop(0)
                            svc_dur = cust['svc']
                            service_end = t + svc_dur
                            is_busy = True
                            w = t - cust['arr_t']
                            s = svc_dur + w
                            sys_times.append(s)
                            wait_times.append(w)
                            dep_count += 1
                            t = service_end
                            service_end = None
                            is_busy = False
                            current_N -= 1
                else:
                    if is_busy:
                        queue.append({'arr_t': t, 'svc': 1.0 / mu})
                        current_N += 1
                    else:
                        svc_dur = 1.0 / mu
                        service_end = t + svc_dur
                        is_busy = True
                        sys_times.append(svc_dur)
                        wait_times.append(0.0)
                        dep_count += 1
                        t = service_end
                        service_end = None
                        is_busy = False
                        if t >= warmup:
                            area_L += current_N * 0.0
                            if is_busy:
                                area_busy += 0.0
                        current_N -= 1
                        while queue and not is_busy:
                            cust = queue.pop(0)
                            svc_dur = cust['svc']
                            service_end = t + svc_dur
                            is_busy = True
                            w = t - cust['arr_t']
                            s = svc_dur + w
                            sys_times.append(s)
                            wait_times.append(w)
                            dep_count += 1
                            t = service_end
                            service_end = None
                            is_busy = False
                            current_N -= 1
                next_arr = t + rng.expovariate(lam)
            else:
                dt = service_end - t
                if t >= warmup:
                    area_L += current_N * dt
                    if is_busy:
                        area_busy += dt
                t = service_end
                dep_count += 1
                current_N -= 1
                service_end = None
                is_busy = False
                if queue:
                    cust = queue.pop(0)
                    svc_dur = cust['svc']
                    service_end = t + svc_dur
                    is_busy = True
                    w = t - cust['arr_t']
                    s = svc_dur + w
                    sys_times.append(s)
                    wait_times.append(w)
                    dep_count += 1
                    t = service_end
                    service_end = None
                    is_busy = False
                    current_N -= 1
                    while queue and not is_busy:
                        cust = queue.pop(0)
                        svc_dur = cust['svc']
                        service_end = t + svc_dur
                        is_busy = True
                        w = t - cust['arr_t']
                        s = svc_dur + w
                        sys_times.append(s)
                        wait_times.append(w)
                        dep_count += 1
                        t = service_end
                        service_end = None
                        is_busy = False
                        current_N -= 1

        L_est = area_L / win if win > 0 else 0.0
        W_est = sum(sys_times) / len(sys_times) * 60.0 if sys_times else 0.0
        busy_est = area_busy / win if win > 0 else 0.0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_est = sum(1 for w in wait_times if w > 0) / len(wait_times) if wait_times else 0.0

        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seed_list.append(seed)
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_time_in_sys += sum(sys_times)
        total_busy_time += area_busy
        total_wait_time += sum(wait_times)
        total_customers += len(sys_times)

    avg_L = sum(per_seed_L) / N if N > 0 else 0.0
    avg_W = sum(per_seed_W) / N if N > 0 else 0.0
    avg_busy = sum(per_seed_busy_frac) / N if N > 0 else 0.0
    avg_p_loss = sum(per_seed_p_loss) / N if N > 0 else 0.0
    avg_p_wait = sum(per_seed_p_wait) / N if N > 0 else 0.0

    arr_avg = total_arr / N if N > 0 else 0.0
    dep_avg = total_dep / N if N > 0 else 0.0
    blk_avg = total_blk / N if N > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    lam_eff = dep_rate
    busy_util = avg_busy
    busy_occupied = avg_busy

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
