import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    lam_base = 14.0 / 60.0  # per minute
    mu_base = 1.0 / 6.0     # per minute
    c = 2

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else (H * 60 if time_unit == "hour" else H / 60)
    
    warmup_frac = 0.25
    win_len = horizon_min * (1 - warmup_frac)
    start_time = horizon_min * warmup_frac

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []

    for i in range(N_seeds):
        seed_val = seed_start + i
        rng = random.Random(seed_val)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] 
        n_in_system = 0
        
        area_L = 0.0
        last_event_time = 0.0
        arrivals_count = 0
        departures_count = 0
        blocked_count = 0
        wait_times_sum = 0.0
        service_times_sum = 0.0
        busy_area = 0.0
        p_wait_count = 0
        total_customers_served_or_blocked = 0
        
        while True:
            next_departure = min(servers_free_at) if any(s > t for s in servers_free_at) else float('inf')
            
            if next_arrival < next_departure and next_arrival <= horizon_min:
                dt = next_arrival - last_event_time
                if last_event_time >= start_time:
                    area_L += n_in_system * dt
                    busy_area += min(n_in_system, c) * dt
                
                t = next_arrival
                last_event_time = t
                arrivals_count += 1
                
                free_server_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_server_idx = k
                        break
                
                if free_server_idx != -1:
                    serv_time = rng.expovariate(mu)
                    servers_free_at[free_server_idx] = t + serv_time
                    n_in_system += 1
                    wait_times_sum += 0.0
                    service_times_sum += serv_time
                    total_customers_served_or_blocked += 1
                    if t >= start_time:
                        p_wait_count += 0
                else:
                    if len(queue) < 1000: 
                        serv_time = rng.expovariate(mu)
                        queue.append((t, serv_time))
                        n_in_system += 1
                        if t >= start_time:
                            p_wait_count += 1
                    else:
                        blocked_count += 1
                        if t >= start_time:
                            pass 

            elif next_departure <= horizon_min and next_departure < next_arrival:
                dt = next_departure - last_event_time
                if last_event_time >= start_time:
                    area_L += n_in_system * dt
                    busy_area += min(n_in_system, c) * dt
                
                t = next_departure
                last_event_time = t
                
                finished_server_idx = -1
                for k in range(c):
                    if abs(servers_free_at[k] - t) < 1e-9:
                        finished_server_idx = k
                        break
                
                if finished_server_idx != -1:
                    n_in_system -= 1
                    departures_count += 1
                    
                    if queue:
                        arr_t, serv_t = queue.pop(0)
                        wait_w = t - arr_t
                        wait_times_sum += wait_w
                        service_times_sum += serv_t
                        servers_free_at[finished_server_idx] = t + serv_t
                        n_in_system += 1
                        total_customers_served_or_blocked += 1
                else:
                    pass

            else:
                dt = horizon_min - last_event_time
                if last_event_time >= start_time:
                    area_L += n_in_system * dt
                    busy_area += min(n_in_system, c) * dt
                t = horizon_min
                break

        L_est = area_L / win_len if win_len > 0 else 0
        W_est = (wait_times_sum + service_times_sum) / total_customers_served_or_blocked if total_customers_served_or_blocked > 0 else 0
        busy_frac_est = busy_area / (win_len * c) if win_len > 0 and c > 0 else 0
        p_wait_est = p_wait_count / arrivals_count if arrivals_count > 0 else 0
        p_loss_est = blocked_count / arrivals_count if arrivals_count > 0 else 0
        dep_rate_est = departures_count / (win_len / 60.0) if win_len > 0 else 0
        lam_eff_est = arrivals_count / (win_len / 60.0) if win_len > 0 else 0
        busy_util_est = busy_area / (win_len * c) if win_len > 0 and c > 0 else 0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arrivals_count)
        all_dep.append(departures_count)
        all_blk.append(blocked_count)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seeds_used_list.append(seed_val)

    avg_L = sum(all_L) / N_seeds
    avg_W = sum(all_W) / N_seeds
    avg_busy_frac = sum(all_busy_frac) / N_seeds
    avg_p_wait = sum(all_p_wait) / N_seeds
    avg_arr = sum(all_arr) / N_seeds
    avg_dep = sum(all_dep) / N_seeds
    avg_blk = sum(all_blk) / N_seeds
    avg_busy_util = sum(all_busy_util) / N_seeds
    avg_dep_rate = sum(all_dep_rate) / N_seeds
    avg_lam_eff = sum(all_lam_eff) / N_seeds
    avg_p_loss = sum(all_p_loss) / N_seeds

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
