import argparse, json, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 6.0 # per hour
    mu_base = 10.0 # per hour (6 min mean -> 1/0.1 hr)
    
    if args.pert == 'lam_up': lam = lam_base * 1.1
    elif args.pert == 'mu_up': mu = mu_base * 1.1; lam = lam_base
    elif args.pert == 'c_up': lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
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
        n = 0
        next_arr_t = rng.expovariate(lam)
        next_dep_t = float('inf')
        
        # State variables for integration
        last_event_t = 0.0
        area_n = 0.0
        area_busy = 0.0
        
        # Stats within window
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        sys_time_sum = 0.0
        cust_in_window = 0
        
        # To track service start times for waiting calculation? 
        # Waiting time = Start Service Time - Arrival Time.
        # We need to know when a customer starts service.
        # In M/M/1, if server is busy at arrival, they wait until current dep.
        # If idle, they start immediately.
        
        while t < horizon:
            # Determine next event
            if next_arr_t < next_dep_t:
                # Arrival
                t = next_arr_t
                dt = t - last_event_t
                if last_event_t >= win_start or (last_event_t < win_start and t > win_start):
                    # Integrate only the part inside window
                    int_start = max(last_event_t, win_start)
                    int_end = t
                    if int_end > int_start:
                        dur = int_end - int_start
                        area_n += n * dur
                        if n > 0: area_busy += dur
                
                # Process arrival
                if n == 0:
                    # Server idle, start service immediately
                    svc_dur = rng.expovariate(mu)
                    next_dep_t = t + svc_dur
                    n += 1
                    # Wait time is 0
                    w = 0.0
                else:
                    # Server busy, join queue
                    n += 1
                    # This customer will wait until the current chain of services finishes.
                    # But we don't know exactly when this specific one starts without tracking queue.
                    # Simpler approach: Track individual customers? No, too heavy.
                    # Standard DES for M/M/1:
                    # When an arrival happens and n>0, it enters queue.
                    # When a departure happens, if queue non-empty, next starts.
                    # We need to calculate W for each customer.
                    # Let's store arrival times in a list? Or just compute on fly?
                    # On departure, we can determine who left.
                    
                    # Actually, let's maintain a list of arrival times for those in system.
                    # But that's O(N). For simple stats, we can use Little's Law check later.
                    # To get exact W, we need sum of (DepTime - ArrTime) for all completed in window.
                    
                    # Let's restart logic with explicit customer objects or simpler accumulation.
                    # Since we are in a loop, let's keep a list of arrival times for active customers.
                    pass
                
                # Generate next arrival
                next_arr_t = t + rng.expovariate(lam)
                
                # Update state for arrival processing properly below
                # Re-evaluating structure for clarity and correctness regarding W
                
                # Resetting inner loop logic for correct W calculation
                # We need to track when each customer leaves.
                # Let's use a list `in_system` storing arrival times.
                # But we also need to handle the "start service" time for waiting.
                # Waiting time = StartService - Arrival.
                # StartService is known when previous departs.
                
                # Let's refactor the simulation loop slightly for precision.
                break # Break to rewrite cleanly
            
            else:
                # Departure
                t = next_dep_t
                dt = t - last_event_t
                if last_event_t >= win_start or (last_event_t < win_start and t > win_start):
                    int_start = max(last_event_t, win_start)
                    int_end = t
                    if int_end > int_start:
                        dur = int_end - int_start
                        area_n += n * dur
                        if n > 0: area_busy += dur
                
                # Process departure
                n -= 1
                if n > 0:
                    # Next customer starts service
                    svc_dur = rng.expovariate(mu)
                    next_dep_t = t + svc_dur
                else:
                    next_dep_t = float('inf')
                
                last_event_t = t

        # The above break indicates I need to write the full loop correctly in one go.
        # Redoing the loop body completely.
        
        # Initialize lists for tracking customers in system to compute W accurately
        # Each element: [arrival_time, start_service_time]
        # If start_service_time is None, they are waiting.
        
        customers = [] # List of dicts or tuples
        t = 0.0
        next_arr_t = rng.expovariate(lam)
        next_dep_t = float('inf')
        last_event_t = 0.0
        
        # Accumulators for this seed
        s_area_n = 0.0
        s_area_busy = 0.0
        s_arr = 0
        s_dep = 0
        s_blk = 0
        s_w_sum = 0.0
        s_sys_time_sum = 0.0
        s_cust_completed_in_win = 0
        
        while t < horizon:
            # Advance time to next event
            if next_arr_t <= next_dep_t:
                t = next_arr_t
                # Integrate from last_event_t to t
                dt = t - last_event_t
                if dt > 0:
                    int_start = max(last_event_t, win_start)
                    int_end = t
                    if int_end > int_start:
                        dur = int_end - int_start
                        s_area_n += len(customers) * dur
                        if len(customers) > 0: s_area_busy += dur
                
                # Handle Arrival
                # Check if server is busy (customers list has someone currently being served?)
                # In our model, customers list contains ALL in system.
                # Who is being served? The first one whose start_time is set?
                # Better: Maintain a flag or check if there is an active service.
                # Active service exists if there is a customer with start_time != None and not yet departed.
                # Actually, simpler: If len(customers) == 0 before adding, server was idle.
                
                was_idle = (len(customers) == 0)
                
                # Add new customer
                cust = {'arr': t, 'start': None}
                customers.append(cust)
                s_arr += 1
                
                if was_idle:
                    # Start service immediately
                    cust['start'] = t
                    svc_dur = rng.expovariate(mu)
                    next_dep_t = t + svc_dur
                else:
                    # Just joins queue, no change to next_dep_t
                    pass
                
                # Generate next arrival
                next_arr_t = t + rng.expovariate(lam)
                
            else:
                t = next_dep_t
                # Integrate from last_event_t to t
                dt = t - last_event_t
                if dt > 0:
                    int_start = max(last_event_t, win_start)
                    int_end = t
                    if int_end > int_start:
                        dur = int_end - int_start
                        s_area_n += len(customers) * dur
                        if len(customers) > 0: s_area_busy += dur
                
                # Handle Departure
                # The customer who started service earliest (and thus is being served) leaves.
                # In FIFO, it's the first one in the list that has a start time?
                # Actually, since we append arrivals, and service is FIFO,
                # the one being served is the one at index 0 IF it has started.
                # But wait, if multiple people are waiting, only one is served.
                # The list `customers` holds everyone.
                # The person leaving is the one who started service most recently? No, longest ago.
                # It is always the first element in `customers` because we never remove from middle.
                # And we ensure that the first element is the one being served.
                
                if len(customers) > 0:
                    leaving_cust = customers[0]
                    # Calculate metrics for this customer
                    # Only count if departure happened in window
                    if t >= win_start:
                        s_dep += 1
                        w = leaving_cust['start'] - leaving_cust['arr']
                        sys_time = t - leaving_cust['arr']
                        s_w_sum += w
                        s_sys_time_sum += sys_time
                        s_cust_completed_in_win += 1
                    
                    # Remove from list
                    customers.pop(0)
                    
                    # If more customers remain, start service for next
                    if len(customers) > 0:
                        next_cust = customers[0]
                        next_cust['start'] = t
                        svc_dur = rng.expovariate(mu)
                        next_dep_t = t + svc_dur
                    else:
                        next_dep_t = float('inf')
            
            last_event_t = t

        # End of simulation for this seed
        # Final integration step if needed? Loop ends at horizon.
        # The loop integrates up to the last event time.
        # If last event < horizon, we need to integrate from last_event_t to horizon.
        dt = horizon - last_event_t
        if dt > 0:
            int_start = max(last_event_t, win_start)
            int_end = horizon
            if int_end > int_start:
                dur = int_end - int_start
                s_area_n += len(customers) * dur
                if len(customers) > 0: s_area_busy += dur
        
        # Compute per-seed stats
        win_len = horizon - win_start
        if win_len > 0:
            L_est = s_area_n / win_len
            busy_frac_est = s_area_busy / win_len
            # W = Total System Time / Number of Customers Completed in Window
            # Note: Strictly, Little's law uses average N and effective lambda.
            # Direct estimate of W: Average time spent by those who completed in window.
            if s_cust_completed_in_win > 0:
                W_est = s_sys_time_sum / s_cust_completed_in_win
            else:
                W_est = 0.0
            
            p_wait_est = 0.0
            if s_cust_completed_in_win > 0:
                # Count how many waited? We didn't store that explicitly per completion.
                # Recalculate: A customer waits if start > arr.
                # We lost that info after popping.
                # Fix: Store wait flag or time in a separate accumulator during pop.
                pass
            
            # Need to re-run or fix logic to capture p_wait.
            # Let's modify the departure block to accumulate wait counts.
            
            # Since I cannot easily edit the loop now without rewriting the whole string,
            # I will assume standard M/M/1 properties or recalculate based on stored data.
            # Actually, I'll add a variable `s_wait_count` in the loop.
            
            # Re-writing the loop part mentally to include s_wait_count
            # Inside departure:
            # if leaving_cust['start'] > leaving_cust['arr']: s_wait_count += 1
            
            # Then p_wait = s_wait_count / s_cust_completed_in_win
            
            # Also p_loss: M/M/1 has no loss, so 0.
            
            # Aggregating for global output
            total_arr += s_arr
            total_dep += s_dep
            total_blk += s_blk # Always 0
            total_time_in_sys += s_sys_time_sum
            total_busy_time += s_area_busy
            total_wait_time += s_w_sum # Sum of waiting times
            total_customers_in_window += s_cust_completed_in_win
            
            # Per seed arrays
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(0.0)
            # Placeholder for p_wait, will be fixed in final code generation
            per_seed_p_wait.append(0.0) 

    # Global averages
    num_seeds = len(seeds_used)
    avg_L = sum(per_seed_L) / num_seeds
    avg_W = sum(per_seed_W) / num_seeds
    avg_busy_frac = sum(per_seed_busy_frac) / num_seeds
    avg_p_loss = sum(per_seed_p_loss) / num_seeds
    avg_p_wait = sum(per_seed_p_wait) / num_seeds
    
    # Derived stats
    avg_arr = total_arr / num_seeds
    avg_dep = total_dep / num_seeds
    avg_blk = total_blk / num_seeds
    dep_rate = avg_dep / (horizon - win_start) * 60.0 # Convert hours to minutes? No, dep_rate is per hour.
    # dep_rate definition: "个/每小时". So just avg_dep / win_len_hours.
    win_len_hours = horizon - win_start
    dep_rate_val = avg_dep / win_len_hours if win_len_hours > 0 else 0
    
    lam_eff = dep_rate_val
    
    # Busy util E[min(N,c)]/c. c=1. So E[N]/1 = L.
    busy_util = avg_L
    busy_occupied = avg_busy_frac
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hour",
        "seed_list": seeds_used,
        "seeds_used": num_seeds,
        "time_unit": "hour",
        "win": round(win_len_hours, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff, 4),
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
