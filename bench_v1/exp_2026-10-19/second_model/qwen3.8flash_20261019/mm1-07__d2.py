import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    lam_base = 8.0
    mu_base = 60.0 / 6.0
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.1
    elif args.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    if args.pert != 'mu_up' and args.pert != 'c_up':
        mu = mu_base

    horizon = args.horizon
    time_unit = "hour"
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_customers_in_window = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        service_end = None
        n_in_system = 0
        busy_time_acc = 0.0
        last_event_time = 0.0
        is_busy = False
        
        arrivals_in_win = 0
        deps_in_win = 0
        blk_in_win = 0
        wait_count_in_win = 0
        custs_in_win = 0
        area_n = 0.0
        sum_w_times = 0.0
        
        while t < horizon:
            if not is_busy:
                if next_arrival <= horizon:
                    dt = next_arrival - t
                    if t >= win_start:
                        area_n += n_in_system * dt
                        busy_time_acc += 0.0
                    t = next_arrival
                    n_in_system += 1
                    if t >= win_start:
                        arrivals_in_win += 1
                        custs_in_win += 1
                        wait_count_in_win += 0 
                    svc_dur = rng.expovariate(mu)
                    service_end = t + svc_dur
                    is_busy = True
                    next_arrival = t + rng.expovariate(lam)
                else:
                    break
            else:
                if next_arrival < service_end:
                    dt = next_arrival - t
                    if t >= win_start:
                        area_n += n_in_system * dt
                        busy_time_acc += dt
                    t = next_arrival
                    n_in_system += 1
                    if t >= win_start:
                        arrivals_in_win += 1
                        custs_in_win += 1
                        wait_count_in_win += 1
                    queue.append(t)
                    next_arrival = t + rng.expovariate(lam)
                else:
                    dt = service_end - t
                    if t >= win_start:
                        area_n += n_in_system * dt
                        busy_time_acc += dt
                    t = service_end
                    n_in_system -= 1
                    if t >= win_start:
                        deps_in_win += 1
                        w_time = t - queue.pop(0) if queue else 0.0
                        # Correction: The customer leaving was the one being served.
                        # We need to track arrival time of current service.
                        pass 
                    
                    # Re-implementing logic more carefully for W tracking
                    # Let's restart the inner loop structure slightly cleaner for correctness on W
                    
        # Resetting simulation logic for clarity and correctness regarding W
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # stores arrival times
        service_end = None
        n_in_system = 0
        busy_time_acc = 0.0
        last_event_time = 0.0
        is_busy = False
        
        arrivals_in_win = 0
        deps_in_win = 0
        blk_in_win = 0
        wait_count_in_win = 0
        custs_in_win = 0
        area_n = 0.0
        sum_w_times = 0.0
        
        # State variables for integration
        prev_t = 0.0
        
        while t < horizon:
            # Determine next event time
            arr_t = next_arrival if next_arrival <= horizon else float('inf')
            dep_t = service_end if (is_busy and service_end <= horizon) else float('inf')
            
            next_t = min(arr_t, dep_t)
            if next_t == float('inf'):
                break
                
            dt = next_t - prev_t
            
            if prev_t >= win_start:
                area_n += n_in_system * dt
                if is_busy:
                    busy_time_acc += dt
            
            prev_t = next_t
            t = next_t
            
            if arr_t <= dep_t:
                # Arrival
                n_in_system += 1
                if t >= win_start:
                    arrivals_in_win += 1
                    custs_in_win += 1
                    if is_busy or len(queue) > 0:
                        wait_count_in_win += 1
                
                if not is_busy:
                    is_busy = True
                    svc_dur = rng.expovariate(mu)
                    service_end = t + svc_dur
                    # Store arrival time for this customer currently in service? 
                    # No, we need to know when they arrived to calculate W upon departure.
                    # If server idle, they start immediately. Their arrival time is t.
                    # We can push their arrival time to a list associated with service?
                    # Simpler: maintain a queue of arrival times. 
                    # If server idle, pop from queue? No, queue holds waiting customers.
                    # Let's use a separate variable for current service arrival time.
                    curr_service_arrival = t
                else:
                    queue.append(t)
                
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                n_in_system -= 1
                if t >= win_start:
                    deps_in_win += 1
                    w_time = t - curr_service_arrival
                    sum_w_times += w_time
                
                if queue:
                    curr_service_arrival = queue.pop(0)
                    svc_dur = rng.expovariate(mu)
                    service_end = t + svc_dur
                else:
                    is_busy = False
                    service_end = None

        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sum_w_times / deps_in_win if deps_in_win > 0 else 0
        bf_est = busy_time_acc / win_len if win_len > 0 else 0
        pl_est = blk_in_win / arrivals_in_win if arrivals_in_win > 0 else 0
        pw_est = wait_count_in_win / arrivals_in_win if arrivals_in_win > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        total_arr += arrivals_in_win
        total_dep += deps_in_win
        total_blk += blk_in_win
        total_time_in_sys += sum_w_times
        total_busy_time += busy_time_acc
        total_wait_time += wait_count_in_win # Not used directly but tracked
        total_customers_in_window += custs_in_win

    N_seeds = len(seeds_used)
    avg_L = sum(per_seed_L) / N_seeds
    avg_W = sum(per_seed_W) / N_seeds
    avg_bf = sum(per_seed_busy_frac) / N_seeds
    avg_pl = sum(per_seed_p_loss) / N_seeds
    avg_pw = sum(per_seed_p_wait) / N_seeds
    
    avg_arr = total_arr / N_seeds
    avg_dep = total_dep / N_seeds
    avg_blk = total_blk / N_seeds
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bf, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
