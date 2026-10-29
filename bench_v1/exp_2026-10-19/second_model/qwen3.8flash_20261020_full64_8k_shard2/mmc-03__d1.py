import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    N_seeds = a.seeds
    H = a.horizon
    S_start = a.seed_start
    pert = a.pert
    lam_base = 8.0
    mu_base = 60.0 / 6.0
    c = 2
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
    time_unit = 'hour'
    warmup_frac = 0.25
    results = []
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end_times = [0.0] * c
        busy_count = 0
        total_wait_time = 0.0
        total_service_time = 0.0
        n_in_system_integral = 0.0
        last_event_time = 0.0
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        wait_events = []
        dep_events = []
        blk_events = []
        n_samples = []
        while t < H:
            arr_t = next_arr
            min_serv_end = min(service_end_times) if busy_count > 0 else float('inf')
            if arr_t <= min_serv_end and arr_t < H:
                dt = arr_t - last_event_time
                n_in_system_integral += (len(queue) + busy_count) * dt
                last_event_time = arr_t
                t = arr_t
                if t >= warmup_frac * H:
                    arrivals_in_window += 1
                free_counter = -1
                for j in range(c):
                    if service_end_times[j] <= t:
                        free_counter = j
                        break
                if free_counter != -1:
                    serv_dur = rng.expovariate(mu)
                    service_end_times[free_counter] = t + serv_dur
                    busy_count += 1
                    total_service_time += serv_dur
                    if t >= warmup_frac * H:
                        wait_events.append(0.0)
                        dep_events.append(t + serv_dur)
                else:
                    serv_dur = rng.expovariate(mu)
                    queue.append((t, serv_dur))
                    if t >= warmup_frac * H:
                        pass
                next_arr = t + rng.expovariate(lam)
            else:
                dt = min_serv_end - last_event_time
                n_in_system_integral += (len(queue) + busy_count) * dt
                last_event_time = min_serv_end
                t = min_serv_end
                idx = service_end_times.index(min_serv_end)
                busy_count -= 1
                if len(queue) > 0:
                    arr_time, serv_dur = queue.pop(0)
                    wait_time = t - arr_time
                    total_wait_time += wait_time
                    service_end_times[idx] = t + serv_dur
                    busy_count += 1
                    total_service_time += serv_dur
                    if t >= warmup_frac * H:
                        wait_events.append(wait_time)
                        dep_events.append(t + serv_dur)
                else:
                    service_end_times[idx] = 0.0
                    if t >= warmup_frac * H:
                        dep_events.append(t)
        dt_final = H - last_event_time
        n_in_system_integral += (len(queue) + busy_count) * dt_final
        win_len = H - warmup_frac * H
        L_avg = n_in_system_integral / win_len if win_len > 0 else 0.0
        W_avg = (total_wait_time + total_service_time) / max(arrivals_in_window, 1) if arrivals_in_window > 0 else 0.0
        W_min = W_avg * 60.0
        busy_util_val = sum(1 for _ in range(1) ) 
        e_min_nc = 0.0
        steps = 1000
        for k in range(steps):
            tt = warmup_frac * H + (k + 0.5) * win_len / steps
            bc_at_tt = 0
            for j in range(c):
                if service_end_times[j] > tt:
                    bc_at_tt += 1
            q_at_tt = 0
            for at, sd in queue:
                if at <= tt and at + sd > tt:
                    q_at_tt += 1
            nc = bc_at_tt + q_at_tt
            e_min_nc += min(nc, c)
        e_min_nc /= steps
        busy_frac_val = e_min_nc / c
        p_wait_val = 0.0
        if arrivals_in_window > 0:
            cnt_wait = 0
            for w in wait_events:
                if w > 0:
                    cnt_wait += 1
            p_wait_val = cnt_wait / len(wait_events) if wait_events else 0.0
        p_loss_val = 0.0
        dep_rate_val = departures_in_window / win_len if win_len > 0 else 0.0
        lam_eff_val = arrivals_in_window / win_len if win_len > 0 else 0.0
        results.append({
            'L': L_avg,
            'W': W_min,
            'busy_frac': busy_frac_val,
            'p_wait': p_wait_val,
            'arr': arrivals_in_window,
            'dep': departures_in_window,
            'blk': blocked_in_window,
            'busy_util': busy_frac_val,
            'dep_rate': dep_rate_val,
            'lam_eff': lam_eff_val,
            'p_loss': p_loss_val,
        })
    seeds_used = len(results)
    seed_list = [S_start + i for i in range(seeds_used)]
    avg_L = sum(r['L'] for r in results) / seeds_used
    avg_W = sum(r['W'] for r in results) / seeds_used
    avg_busy_frac = sum(r['busy_frac'] for r in results) / seeds_used
    avg_p_wait = sum(r['p_wait'] for r in results) / seeds_used
    avg_arr = sum(r['arr'] for r in results) / seeds_used
    avg_dep = sum(r['dep'] for r in results) / seeds_used
    avg_blk = sum(r['blk'] for r in results) / seeds_used
    avg_busy_util = sum(r['busy_util'] for r in results) / seeds_used
    avg_dep_rate = sum(r['dep_rate'] for r in results) / seeds_used
    avg_lam_eff = sum(r['lam_eff'] for r in results) / seeds_used
    avg_p_loss = sum(r['p_loss'] for r in results) / seeds_used
    per_seed_L = [r['L'] for r in results]
    per_seed_W = [r['W'] for r in results]
    per_seed_busy_frac = [r['busy_frac'] for r in results]
    per_seed_p_loss = [r['p_loss'] for r in results]
    per_seed_p_wait = [r['p_wait'] for r in results]
    out = {
        'L': round(avg_L, 6),
        'W': round(avg_W, 6),
        'busy_frac': round(avg_busy_frac, 6),
        'p_wait': round(avg_p_wait, 6),
        'runtime_units': 'hours',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': time_unit,
        'win': round(H - warmup_frac * H, 6),
        'arr': round(avg_arr, 6),
        'blk': round(avg_blk, 6),
        'busy_util': round(avg_busy_util, 6),
        'dep': round(avg_dep, 6),
        'dep_rate': round(avg_dep_rate, 6),
        'lam_eff': round(avg_lam_eff, 6),
        'p_loss': round(avg_p_loss, 6),
        'per_seed_L': [round(x, 6) for x in per_seed_L],
        'per_seed_W': [round(x, 6) for x in per_seed_W],
        'per_seed_busy_frac': [round(x, 6) for x in per_seed_busy_frac],
        'per_seed_p_loss': [round(x, 6) for x in per_seed_p_loss],
        'per_seed_p_wait': [round(x, 6) for x in per_seed_p_wait],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
