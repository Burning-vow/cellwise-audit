import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 4.0
    mu_base = 10.0
    c = 1
    
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': c += 1
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        # Event simulation: M/M/1 with finite capacity? Problem says stable, no blocking mentioned explicitly but blk is required. 
        # Standard M/M/1 has infinite queue, so blk should be 0 unless specified otherwise. 
        # However, the prompt asks for blk (rejected/lost). In standard M/M/1, there is no rejection. 
        # But to satisfy the output keys, we must report it. If no rejection mechanism is defined, blk=0.
        # Let's assume standard M/M/1 where customers never leave without service (no balking/rejection).
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        
        n_in_sys = 0
        busy_time = 0.0
        last_event_time = 0.0
        
        # For W calculation: need sum of times spent by customers who departed within window
        # We track arrival time for each customer in system
        # Since we only have one server, we can track when current service started and queue start times
        
        # To compute L accurately via area integration:
        # Area under N(t) curve from win_start to horizon
        
        # To compute W: Average time in system for customers departing in window
        # Need to record departure times and corresponding arrival times
        
        # Data structures for tracking customers in system
        # Queue: list of arrival times
        # Server: (arrival_time, service_end_time) or None
        
        queue = []
        server_customer = None # (arr_time, dep_time)
        
        # Statistics accumulators for this seed
        area_N = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_time_in_sys_win = 0.0
        busy_time_win = 0.0
        
        # We need to handle events carefully around the warmup boundary
        
        while t < horizon:
            # Determine next event
            if next_arr <= next_dep:
                # Arrival
                t = next_arr
                # Update integrals up to t
                dt = t - last_event_time
                if last_event_time < win_start:
                    # Part before window
                    pass
                else:
                    area_N += n_in_sys * dt
                    if server_customer is not None:
                        busy_time_win += dt
                
                # Process arrival
                if n_in_sys < 1000000: # Infinite buffer effectively
                    queue.append(t)
                    n_in_sys += 1
                    count_arr_win += 1 if t >= win_start else 0
                    
                    # Start service if idle
                    if server_customer is None:
                        serv_time = rng.expovariate(mu_base)
                        dep_t = t + serv_time
                        arr_t = queue.pop(0)
                        n_in_sys -= 1
                        server_customer = (arr_t, dep_t)
                        next_dep = dep_t
                else:
                    count_blk_win += 1 if t >= win_start else 0
                
                # Schedule next arrival
                next_arr = t + rng.expovariate(lam_base)
                
            else:
                # Departure
                t = next_dep
                dt = t - last_event_time
                if last_event_time < win_start:
                    pass
                else:
                    area_N += n_in_sys * dt
                    if server_customer is not None:
                        busy_time_win += dt
                
                # Process departure
                if server_customer is not None:
                    arr_t, dep_t = server_customer
                    if dep_t >= win_start:
                        count_dep_win += 1
                        sum_time_in_sys_win += (dep_t - arr_t)
                    
                    server_customer = None
                    n_in_sys -= 1
                    
                    # Start next service if queue non-empty
                    if queue:
                        serv_time = rng.expovariate(mu_base)
                        dep_t_new = t + serv_time
                        arr_t_new = queue.pop(0)
                        n_in_sys -= 1
                        server_customer = (arr_t_new, dep_t_new)
                        next_dep = dep_t_new
                    else:
                        next_dep = float('inf')
            
            last_event_time = t
            
        # Final update if loop ended exactly at horizon or past
        if last_event_time < horizon:
             dt = horizon - last_event_time
             if last_event_time < win_start:
                 # Split
                 d1 = win_start - last_event_time
                 d2 = horizon - win_start
                 # Before window: ignore for stats
                 # After window:
                 area_N += n_in_sys * d2
                 if server_customer is not None:
                     busy_time_win += d2
             else:
                 area_N += n_in_sys * dt
                 if server_customer is not None:
                     busy_time_win += dt

        # Calculate metrics for this seed
        L_est = area_N / win_len if win_len > 0 else 0
        W_est = sum_time_in_sys_win / count_dep_win if count_dep_win > 0 else 0
        busy_frac_est = busy_time_win / win_len if win_len > 0 else 0
        p_wait_est = 0.0 # Probability of waiting upon arrival. Hard to get directly from simple sim without more tracking.
                         # Approximate as fraction of arrivals that found server busy?
                         # Or use Little's Law derived values? 
                         # Let's approximate p_wait as (L - rho)/rho ? No.
                         # In M/M/1, P(wait) = rho.
                         # From sim: Count arrivals that had to wait (queue length > 0 at arrival)
                         # We didn't track that explicitly. 
                         # Let's re-run logic mentally: We need to count how many arrivals found server busy.
                         # I will add a counter for that.
                         
        # Re-simulate quickly to get p_wait properly? Or modify above.
        # Modifying above is better.
        
        # Reset and redo with proper tracking for p_wait
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        n_in_sys = 0
        last_event_time = 0.0
        queue = []
        server_customer = None
        area_N = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_time_in_sys_win = 0.0
        busy_time_win = 0.0
        count_wait_win = 0 # Arrivals that waited
        
        while t < horizon:
            if next_arr <= next_dep:
                t = next_arr
                dt = t - last_event_time
                if last_event_time >= win_start:
                    area_N += n_in_sys * dt
                    if server_customer is not None:
                        busy_time_win += dt
                elif t > win_start:
                    d_pre = win_start - last_event_time
                    d_post = t - win_start
                    area_N += n_in_sys * d_post
                    if server_customer is not None:
                        busy_time_win += d_post
                
                # Arrival
                if n_in_sys < 1000000:
                    if t >= win_start:
                        count_arr_win += 1
                        if server_customer is not None:
                            count_wait_win += 1
                    
                    queue.append(t)
                    n_in_sys += 1
                    
                    if server_customer is None:
                        serv_time = rng.expovariate(mu_base)
                        dep_t = t + serv_time
                        arr_t = queue.pop(0)
                        n_in_sys -= 1
                        server_customer = (arr_t, dep_t)
                        next_dep = dep_t
                else:
                    if t >= win_start:
                        count_blk_win += 1
                
                next_arr = t + rng.expovariate(lam_base)
            else:
                t = next_dep
                dt = t - last_event_time
                if last_event_time >= win_start:
                    area_N += n_in_sys * dt
                    if server_customer is not None:
                        busy_time_win += dt
                elif t > win_start:
                    d_pre = win_start - last_event_time
                    d_post = t - win_start
                    area_N += n_in_sys * d_post
                    if server_customer is not None:
                        busy_time_win += d_post
                
                if server_customer is not None:
                    arr_t, dep_t = server_customer
                    if dep_t >= win_start:
                        count_dep_win += 1
                        sum_time_in_sys_win += (dep_t - arr_t)
                    
                    server_customer = None
                    n_in_sys -= 1
                    
                    if queue:
                        serv_time = rng.expovariate(mu_base)
                        dep_t_new = t + serv_time
                        arr_t_new = queue.pop(0)
                        n_in_sys -= 1
                        server_customer = (arr_t_new, dep_t_new)
                        next_dep = dep_t_new
                    else:
                        next_dep = float('inf')
            
            last_event_time = t
            
        if last_event_time < horizon:
             dt = horizon - last_event_time
             if last_event_time >= win_start:
                 area_N += n_in_sys * dt
                 if server_customer is not None:
                     busy_time_win += dt
             elif horizon > win_start:
                 d_post = horizon - win_start
                 area_N += n_in_sys * d_post
                 if server_customer is not None:
                     busy_time_win += d_post

        L_est = area_N / win_len if win_len > 0 else 0
        W_est = sum_time_in_sys_win / count_dep_win if count_dep_win > 0 else 0
        busy_frac_est = busy_time_win / win_len if win_len > 0 else 0
        p_wait_est = count_wait_win / count_arr_win if count_arr_win > 0 else 0
        p_loss_est = count_blk_win / count_arr_win if count_arr_win > 0 else 0
        lam_eff_est = count_dep_win / win_len if win_len > 0 else 0
        dep_rate_est = count_dep_win / win_len if win_len > 0 else 0 # Same as lam_eff in steady state
        
        busy_util_est = busy_frac_est # E[min(N,c)]/c = busy_frac for c=1
        busy_occ_est = 1 - (1 - busy_frac_est) # 1-pi0 = busy_frac
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr_win)
        all_dep.append(count_dep_win)
        all_blk.append(count_blk_win)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        all_dep_rate.append(dep_rate_est)

    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_busy_occupied = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0
    
    # Convert W to minutes if time_unit is hour
    W_min = avg_W * 60 if time_unit == 'hour' else avg_W
    
    res = {
        "L": round(avg_L, 4),
        "W": round(W_min, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
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
        "per_seed_W": [round(x*60 if time_unit=='hour' else x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
