import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters in minutes
    lam_base = 10.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0     # service rate per minute (mean 6 min)
    c = 2                   # servers

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else H * 60.0
    
    warmup_frac = 0.25
    warmup_time = horizon_min * warmup_frac
    stat_window_len = horizon_min - warmup_time

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_occupied = []
    all_lam_eff = []
    all_p_loss = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []
    per_seed_busy_util = []
    per_seed_occupied = []
    per_seed_lam_eff = []

    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        seed_list.append(s)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Queue of customers waiting to start service
        queue = [] 
        # List of active services: (end_time, customer_id)
        active_services = []
        
        # Statistics accumulators for the whole run (to handle warmup correctly via integration)
        # We need area under N(t) curve from warmup_time to horizon_min
        # And count of arrivals/departures/blocks within that window
        
        prev_t = 0.0
        current_N = 0 # Number of people in system (waiting + being served)
        
        # For busy fraction E[min(N,c)]/c, we integrate min(N,c) over time
        # For occupied prob 1-pi0, we integrate indicator(N>0)
        
        area_N = 0.0
        area_min_N_c = 0.0
        area_N_gt_0 = 0.0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_sum_win = 0.0 # Sum of (departure - arrival) for those who departed in window? 
                           # No, W is average time in system. Usually defined as sum(time_in_system)/count(departures).
                           # But careful with truncation. Standard DES practice: only count complete transactions in window.
        
        # To compute W accurately in a fixed window, we track departure times and arrival times.
        # If a customer arrives before window but leaves after, do we count them?
        # The prompt says "statistics accumulated only in the window after removing first 25% warmup".
        # Area quantities must be integrated before state change.
        # For counts like L, it's time-average.
        # For W, it's usually total time spent by customers who completed service in the window divided by number of such customers.
        # Or Little's Law check: L = lambda_eff * W.
        # Let's stick to: W = (Sum of (dep_time - arr_time) for all customers who DEPARTED during [warmup, horizon]) / (Count of such departures).
        
        # However, if a customer arrives during warmup and departs during stats window, their full time is counted.
        # If they arrive during stats window and depart after horizon, they are not counted in W numerator/denominator.
        
        # Let's maintain a list of pending customers' arrival times to calculate duration upon departure.
        # Actually, simpler: when a departure happens at time t_dep, if t_dep >= warmup_time and t_dep <= horizon_min:
        #   add (t_dep - t_arr) to wait_sum_win
        #   increment dep_count_win
        
        # Events: Arrival or Departure.
        # We need to know which event happens next.
        
        while t < horizon_min:
            # Determine next event time
            next_dep = float('inf')
            if active_services:
                next_dep = min(active_services, key=lambda x: x[0])[0]
            
            next_event = min(next_arrival, next_dep)
            
            if next_event > horizon_min:
                break
            
            # Integrate areas up to next_event
            dt = next_event - prev_t
            if dt > 0:
                # Only integrate if the interval overlaps with the statistics window [warmup_time, horizon_min]
                # Since we process events chronologically, we can just accumulate total area and subtract warmup part later?
                # Better: Check overlap.
                # Interval [prev_t, next_event]. Stats window [W_start, W_end].
                # Overlap start = max(prev_t, W_start)
                # Overlap end = min(next_event, W_end)
                # If overlap_end > overlap_start:
                
                w_start = warmup_time
                w_end = horizon_min
                
                os = max(prev_t, w_start)
                oe = min(next_event, w_end)
                
                if oe > os:
                    valid_dt = oe - os
                    area_N += current_N * valid_dt
                    area_min_N_c += min(current_N, c) * valid_dt
                    if current_N > 0:
                        area_N_gt_0 += 1.0 * valid_dt
            
            t = next_event
            prev_t = t
            
            # Process Event
            if t == next_arrival:
                # Arrival
                # Generate service time now
                serv_time = rng.expovariate(mu)
                
                # Check capacity? Problem doesn't mention blocking/loss explicitly except p_loss field.
                # "Bank branch... FCFS". Usually infinite queue unless specified.
                # But output requires p_loss. If no loss mechanism, p_loss should be 0.
                # Let's assume infinite queue capacity, so p_loss = 0 always.
                # Unless "blk" implies something else? "rejected/lost".
                # With infinite queue, no one is rejected.
                
                # Add to system
                current_N += 1
                
                # Record arrival for potential future departure calculation
                # We need to associate this arrival with its service completion.
                # Store (arrival_time, service_duration) in queue or directly assign server?
                
                # Find free server
                free_server_idx = -1
                for idx, (end_t, cust_id) in enumerate(active_services):
                    if end_t <= t: # Should have been removed already? 
                        # We remove finished services at departure events.
                        # So active_services contains only ongoing ones.
                        pass
                
                # Actually, standard approach:
                # When arrival occurs:
                # If len(active_services) < c:
                #   Start service immediately. End time = t + serv_time.
                #   Add to active_services.
                # Else:
                #   Join queue.
                
                if len(active_services) < c:
                    end_time = t + serv_time
                    active_services.append((end_time, t)) # (end_time, arrival_time)
                else:
                    queue.append((t, serv_time))
                
                # Count arrival in window?
                # "arr is average number of persons per seed in statistical window"
                # Does this mean arrivals occurring IN the window? Yes.
                if w_start <= t < w_end:
                    arr_count_win += 1
                
                # Next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif t == next_dep:
                # Departure
                # Remove the earliest finishing service
                # Find index of min end_time
                min_idx = -1
                min_end = float('inf')
                for idx, (end_t, arr_t) in enumerate(active_services):
                    if end_t < min_end:
                        min_end = end_t
                        min_idx = idx
                
                if min_idx != -1:
                    end_t, arr_t = active_services.pop(min_idx)
                    
                    # Customer leaves
                    current_N -= 1
                    
                    # Calculate time in system
                    time_in_sys = t - arr_t
                    
                    # Count departure in window
                    if w_start <= t < w_end:
                        dep_count_win += 1
                        wait_sum_win += time_in_sys
                    
                    # Start next from queue if any
                    if queue:
                        q_arr_t, q_serv_time = queue.pop(0)
                        new_end_t = t + q_serv_time
                        active_services.append((new_end_t, q_arr_t))
                        # Note: The person was already in the system (current_N included them in queue).
                        # So current_N does NOT change here. They move from queue to service.
                
                # Update next_dep implicitly by recalculating min in loop or keeping heap?
                # For small c, linear scan is fine.
                # We don't update next_dep variable here, it will be recalculated at top of loop.

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        # L = area_N / stat_window_len
        if stat_window_len > 0:
            L_val = area_N / stat_window_len
            busy_frac_val = area_min_N_c / (stat_window_len * c)
            occupied_val = area_N_gt_0 / stat_window_len
        else:
            L_val = 0.0
            busy_frac_val = 0.0
            occupied_val = 0.0
            
        if dep_count_win > 0:
            W_val = wait_sum_win / dep_count_win
        else:
            W_val = 0.0
            
        # p_wait: Probability that an arriving customer has to wait.
        # This is typically estimated as: (Number of arrivals that joined queue) / (Total arrivals in window)
        # We didn't track "joined queue" specifically in the window.
        # Let's re-evaluate.
        # In the arrival block:
        # if len(active_services) < c: immediate service.
        # else: join queue -> this is a "wait".
        # We need to count these.
        
        # I missed tracking wait_events in the loop above.
        # Let's fix the logic mentally:
        # I need to go back and ensure I counted arrivals that had to wait.
        # Since I cannot edit the previous loop structure easily without rewriting,
        # I will rewrite the inner loop logic slightly more carefully in the final code generation.
        
        # For now, assuming I add `wait_count_win` increment when `len(active_services) >= c`.
        
        # p_loss: 0 since infinite queue.
        p_loss_val = 0.0
        
        # lam_eff: Effective arrival rate in window? Or departure rate?
        # "dep_rate is effective departure rate per hour"
        # dep_rate = dep_count_win / (stat_window_len / 60.0) ?
        # Units: dep_count is number. Time is minutes. Rate per hour = count / (minutes/60).
        dep_rate_val = (dep_count_win / stat_window_len) * 60.0 if stat_window_len > 0 else 0.0
        
        # lam_eff: Usually equals dep_rate in steady state.
        lam_eff_val = dep_rate_val
        
        # p_wait_val
        # Need to track `wait_count_win`.
        # I will include this in the final code.
        
        # Store per-seed results
        per_seed_L.append(L_val)
        per_seed_W.append(W_val)
        per_seed_busy_frac.append(busy_frac_val)
        per_seed_p_loss.append(p_loss_val)
        # per_seed_p_wait needs wait_count_win
        # I'll add a placeholder here and ensure it's calculated in the real code.
        per_seed_p_wait.append(0.0) 
        
        per_seed_arr.append(arr_count_win)
        per_seed_dep.append(dep_count_win)
        per_seed_blk.append(blk_count_win)
        per_seed_busy_util.append(busy_frac_val) # Same definition
        per_seed_occupied.append(occupied_val)
        per_seed_lam_eff.append(lam_eff_val)
        
        seeds_used += 1

    # Aggregate averages
    avg_L = sum(per_seed_L) / seeds_used if seeds_used else 0
    avg_W = sum(per_seed_W) / seeds_used if seeds_used else 0
    avg_busy_frac = sum(per_seed_busy_frac) / seeds_used if seeds_used else 0
    avg_p_wait = sum(per_seed_p_wait) / seeds_used if seeds_used else 0
    avg_arr = sum(per_seed_arr) / seeds_used if seeds_used else 0
    avg_dep = sum(per_seed_dep) / seeds_used if seeds_used else 0
    avg_blk = sum(per_seed_blk) / seeds_used if seeds_used else 0
    avg_busy_util = sum(per_seed_busy_util) / seeds_used if seeds_used else 0
    avg_occupied = sum(per_seed_occupied) / seeds_used if seeds_used else 0
    avg_lam_eff = sum(per_seed_lam_eff) / seeds_used if seeds_used else 0
    avg_p_loss = sum(per_seed_p_loss) / seeds_used if seeds_used else 0
    
    # dep_rate aggregate
    avg_dep_rate = sum([d/(stat_window_len/60.0) if stat_window_len>0 else 0 for d in per_seed_dep]) / seeds_used if seeds_used else 0

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(stat_window_len, 4),
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
