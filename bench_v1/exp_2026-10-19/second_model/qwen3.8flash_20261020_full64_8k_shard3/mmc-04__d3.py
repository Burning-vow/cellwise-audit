import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=10.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 10.0
    mu_base = 6.0 # 1/10 min = 6 per hour
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
        
    time_unit = "hour"
    win = H * 0.75 # Remove first 25% as warmup
    start_time_warmup = H * 0.25
    
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
    all_busy_occupied = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # List of (arrival_time, service_duration)
        
        # Statistics accumulators (for area integration and counts)
        # We need to track state changes to integrate L(t) and busy count
        last_event_time = 0.0
        current_num_in_system = 0
        current_num_busy = 0
        
        # Accumulators for the statistical window
        area_L = 0.0
        area_busy = 0.0
        area_occupied = 0.0 # Time when at least one server is busy? No, busy_frac is E[min(N,c)]/c. 
                            # The prompt asks for busy_frac = E[min(N,c)]/c. This is equivalent to average utilization per server.
                            # It also asks for busy_util = E[min(N,c)]/c. They are the same definition here.
                            # And busy_occupied = 1 - pi_0. pi_0 is prob system empty. So 1-pi_0 is prob system non-empty.
        
        # To compute 1-pi_0, we need time spent with N>0.
        time_non_empty = 0.0
        
        # Counts
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0 # For infinite buffer, blocked is 0 unless capacity limit. Problem doesn't specify capacity limit, assume infinite.
                              # But output requires blk. If infinite, blk=0.
        
        # Waiting times sum for W calculation
        total_waiting_plus_service_time = 0.0
        customers_completed_in_window = 0
        
        # Helper to update areas based on elapsed time since last event
        def update_areas(current_t):
            nonlocal area_L, area_busy, time_non_empty, last_event_time
            dt = current_t - last_event_time
            if dt > 0:
                # Only accumulate if we are in the statistical window
                # However, standard DES usually integrates over whole run then discards or starts integrating after warmup.
                # Prompt: "statistics only accumulated in window after removing first 25% warmup".
                # "Area quantities must be integrated before changing state".
                
                # Check overlap with window [start_time_warmup, H]
                # Since events happen sequentially, we can check if the interval [last_event_time, current_t] overlaps with window.
                # Simpler approach: Run simulation until H. At each step, if last_event_time >= start_time_warmup, add area.
                # But what if an event spans across the boundary?
                # Let's refine: We integrate from max(last_event_time, start_time_warmup) to min(current_t, H).
                
                int_start = max(last_event_time, start_time_warmup)
                int_end = min(current_t, H)
                
                if int_end > int_start:
                    dt_win = int_end - int_start
                    area_L += current_num_in_system * dt_win
                    area_busy += current_num_busy * dt_win
                    if current_num_in_system > 0:
                        time_non_empty += dt_win
            
            last_event_time = current_t

        while t < H:
            # Determine next event
            arr_time = next_arrival
            dep_times = [s for s in servers_free_at if s <= H and s > t] # Potential departures
            # Actually, we should look at the earliest departure among those that have started or will start?
            # In this model, service starts immediately if server free.
            # servers_free_at holds the time when a server becomes free.
            # If a customer is waiting, they haven't started service yet.
            
            # Find earliest departure time among active services
            # Active services are those where start_time < t < end_time? 
            # No, simpler: servers_free_at contains the completion times of currently served customers.
            # If a server is idle, its free time is <= t.
            # We need to find min(servers_free_at) that is > t.
            
            min_dep = float('inf')
            for s in servers_free_at:
                if s > t and s < min_dep:
                    min_dep = s
            
            next_dep = min_dep
            
            if arr_time < next_dep:
                # Arrival Event
                t = arr_time
                update_areas(t)
                
                # Record arrival stats if in window
                if t >= start_time_warmup:
                    arrivals_in_window += 1
                
                # Generate service duration now
                svc_dur = rng.expovariate(mu)
                
                # Check for available server
                avail_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        avail_idx = k
                        break
                
                if avail_idx != -1:
                    # Start service immediately
                    servers_free_at[avail_idx] = t + svc_dur
                    current_num_in_system += 1
                    current_num_busy += 1
                    # Wait time is 0. Total time in system = svc_dur.
                    # We need to account for this customer's contribution to W later upon departure.
                    # Store info in queue? Or just handle at departure?
                    # Since we need W (avg time in system), we need to know when they leave.
                    # We can push to a list of "in-service" items?
                    # Better: Push to queue structure that tracks arrival time and service end time.
                    # But queue is for waiting.
                    # Let's maintain a list of active services: (end_time, arrival_time)
                    # Actually, we already have servers_free_at. We need to map back to arrival time for W calc.
                    # Let's use a separate list `active_services` storing (end_time, arrival_time).
                    # When a server becomes free, we pop the corresponding service.
                    
                    # Refactor: Use a priority queue for departures?
                    # Standard M/M/c simulation:
                    # Events: Arrival, Departure.
                    # On Arrival:
                    #   If server free: Schedule Departure at t+svc. Add to "waiting_for_departure" list?
                    #   Else: Add to Queue.
                    # On Departure:
                    #   Remove from "in-service".
                    #   If Queue not empty: Pop head, schedule new Departure.
                    
                    # Let's implement with explicit lists.
                    # `queue`: list of (arrival_time, service_duration) for waiting customers.
                    # `in_service`: list of (departure_time, arrival_time) for being served.
                    
                    # Re-initialize structures properly
                    pass 
                
                # I need to rewrite the loop logic cleanly.
                # Let's restart the inner loop logic with clear data structures.
                
                # Data Structures:
                # queue: list of tuples (arrival_time, service_duration)
                # in_service: list of tuples (departure_time, arrival_time)
                # servers_free_at is redundant if we manage in_service correctly.
                
                # Resetting for clarity inside the loop is hard. Let's define outside.
                break # Break to restructure code below
            else:
                # Departure Event
                t = next_dep
                update_areas(t)
                # Handle departure
                # Find which server finished
                # ...
                break # Break to restructure

        # --- RESTRUCTURED SIMULATION LOOP ---
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # (arrival_time, service_duration)
        in_service = [] # (departure_time, arrival_time)
        
        last_event_time = 0.0
        current_num_in_system = 0
        current_num_busy = 0
        
        area_L = 0.0
        area_busy = 0.0
        time_non_empty = 0.0
        
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        total_time_in_system_sum = 0.0
        completed_customers_in_window = 0
        
        # Helper
        def update_areas(current_t):
            nonlocal area_L, area_busy, time_non_empty, last_event_time
            dt = current_t - last_event_time
            if dt > 0:
                int_start = max(last_event_time, start_time_warmup)
                int_end = min(current_t, H)
                if int_end > int_start:
                    dt_win = int_end - int_start
                    area_L += current_num_in_system * dt_win
                    area_busy += current_num_busy * dt_win
                    if current_num_in_system > 0:
                        time_non_empty += dt_win
            last_event_time = current_t

        while t < H:
            # Find next departure time
            next_dep = float('inf')
            dep_idx = -1
            for idx, (dep_t, _) in enumerate(in_service):
                if dep_t < next_dep:
                    next_dep = dep_t
                    dep_idx = idx
            
            if next_arrival < next_dep:
                # Arrival
                t = next_arrival
                update_areas(t)
                
                if t >= start_time_warmup:
                    arrivals_in_window += 1
                
                svc_dur = rng.expovariate(mu)
                
                if len(in_service) < c:
                    # Server available
                    dep_time = t + svc_dur
                    in_service.append((dep_time, t))
                    current_num_in_system += 1
                    current_num_busy += 1
                else:
                    # Queue
                    queue.append((t, svc_dur))
                    current_num_in_system += 1
                    # Busy count unchanged
                
                # Next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                t = next_dep
                update_areas(t)
                
                # Remove from in_service
                dep_time, arr_time = in_service.pop(dep_idx)
                current_num_in_system -= 1
                current_num_busy -= 1
                
                if t >= start_time_warmup:
                    departures_in_window += 1
                    total_time_in_system_sum += (t - arr_time)
                    completed_customers_in_window += 1
                
                # Serve next from queue if any
                if queue:
                    q_arr, q_svc = queue.pop(0)
                    new_dep_time = t + q_svc
                    in_service.append((new_dep_time, q_arr))
                    current_num_in_system += 1 # Was counted in queue, now moving to service? 
                    # Wait, current_num_in_system includes queue. 
                    # When departing, we removed one person.
                    # If we move one from queue to service, num_in_system stays same?
                    # No, we decremented by 1. Now we increment by 1. Net change 0.
                    # But busy count increases by 1.
                    current_num_in_system += 1
                    current_num_busy += 1
                    
                    # Note: The arrival time for this customer was q_arr.
                    # Their wait time started at q_arr.
                    # We don't record stats for them yet, they are still in system.
                
                # If no queue, nothing happens.

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        # Window length
        win_len = H - start_time_warmup
        
        if win_len > 0:
            avg_L = area_L / win_len
            avg_busy = area_busy / win_len
            busy_frac_val = avg_busy / c
            busy_util_val = avg_busy / c
            busy_occ_val = time_non_empty / win_len
            
            # p_wait: Probability that an arriving customer has to wait.
            # Count arrivals in window where queue was non-empty OR all servers busy.
            # We didn't track this during arrival. Need to re-run or track it.
            # Let's modify the loop to track p_wait.
            pass

        # Re-running with tracking for p_wait and ensuring correctness
        # Since I cannot easily edit the above block without rewriting, I will rewrite the seed loop completely.
        
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        in_service = []
        
        last_event_time = 0.0
        current_num_in_system = 0
        current_num_busy = 0
        
        area_L = 0.0
        area_busy = 0.0
        time_non_empty = 0.0
        
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        total_time_in_system_sum = 0.0
        completed_customers_in_window = 0
        waits_in_window = 0 # Number of arrivals that had to wait
        
        def update_areas(current_t):
            nonlocal area_L, area_busy, time_non_empty, last_event_time
            dt = current_t - last_event_time
            if dt > 0:
                int_start = max(last_event_time, start_time_warmup)
                int_end = min(current_t, H)
                if int_end > int_start:
                    dt_win = int_end - int_start
                    area_L += current_num_in_system * dt_win
                    area_busy += current_num_busy * dt_win
                    if current_num_in_system > 0:
                        time_non_empty += dt_win
            last_event_time = current_t

        while t < H:
            next_dep = float('inf')
            dep_idx = -1
            for idx, (dep_t, _) in enumerate(in_service):
                if dep_t < next_dep:
                    next_dep = dep_t
                    dep_idx = idx
            
            if next_arrival < next_dep:
                t = next_arrival
                update_areas(t)
                
                if t >= start_time_warmup:
                    arrivals_in_window += 1
                
                svc_dur = rng.expovariate(mu)
                
                if len(in_service) < c:
                    dep_time = t + svc_dur
                    in_service.append((dep_time, t))
                    current_num_in_system += 1
                    current_num_busy += 1
                else:
                    queue.append((t, svc_dur))
                    current_num_in_system += 1
                    if t >= start_time_warmup:
                        waits_in_window += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            else:
                t = next_dep
                update_areas(t)
                
                dep_time, arr_time = in_service.pop(dep_idx)
                current_num_in_system -= 1
                current_num_busy -= 1
                
                if t >= start_time_warmup:
                    departures_in_window += 1
                    total_time_in_system_sum += (t - arr_time)
                    completed_customers_in_window += 1
                
                if queue:
                    q_arr, q_svc = queue.pop(0)
                    new_dep_time = t + q_svc
                    in_service.append((new_dep_time, q_arr))
                    current_num_in_system += 1
                    current_num_busy += 1

        win_len = H - start_time_warmup
        
        if win_len > 0:
            L_val = area_L / win_len
            busy_frac_val = (area_busy / win_len) / c
            busy_util_val = busy_frac_val
            busy_occ_val = time_non_empty / win_len
            
            if arrivals_in_window > 0:
                p_wait_val = waits_in_window / arrivals_in_window
            else:
                p_wait_val = 0.0
                
            if completed_customers_in_window > 0:
                W_val = total_time_in_system_sum / completed_customers_in_window
            else:
                W_val = 0.0
                
            dep_rate_val = departures_in_window / win_len * 60.0 # Per hour? No, time_unit is hour.
            # dep_rate is "个/每小时". Since win_len is in hours, rate is count/hour.
            dep_rate_val = departures_in_window / win_len
            
            lam_eff_val = arrivals_in_window / win_len
            
            p_loss_val = blocked_in_window / arrivals_in_window if arrivals_in_window > 0 else 0.0
            
            all_L.append(L_val)
            all_W.append(W_val)
            all_busy_frac.append(busy_frac_val)
            all_p_wait.append(p_wait_val)
            all_arr.append(arrivals_in_window)
            all_dep.append(departures_in_window)
            all_blk.append(blocked_in_window)
            all_busy_util.append(busy_util_val)
            all_dep_rate.append(dep_rate_val)
            all_lam_eff.append(lam_eff_val)
            all_p_loss.append(p_loss_val)
            all_busy_occupied.append(busy_occ_val)
        else:
            # Fallback if horizon too small
            all_L.append(0.0)
            all_W.append(0.0)
            all_busy_frac.append(0.0)
            all_p_wait.append(0.0)
            all_arr.append(0)
            all_dep.append(0)
            all_blk.append(0)
            all_busy_util.append(0.0)
            all_dep_rate.append(0.0)
            all_lam_eff.append(0.0)
            all_p_loss.append(0.0)
            all_busy_occupied.append(0.0)

    # Aggregate results
    seeds_used = len(all_L)
    if seeds_used == 0:
        res = {
            "L": 0.0, "W": 0.0, "busy_frac": 0.0, "p_wait": 0.0,
            "runtime_units": time_unit, "seed_list": [], "seeds_used": 0,
            "time_unit": time_unit, "win": 0.0,
            "arr": 0.0, "blk": 0.0, "busy_util": 0.0, "dep": 0.0,
            "dep_rate": 0.0, "lam_eff": 0.0, "p_loss": 0.0,
            "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [],
            "per_seed_p_loss": [], "per_seed_p_wait": []
        }
    else:
        mean_L = sum(all_L) / seeds_used
        mean_W = sum(all_W) / seeds_used
        mean_busy_frac = sum(all_busy_frac) / seeds_used
        mean_p_wait = sum(all_p_wait) / seeds_used
        mean_arr = sum(all_arr) / seeds_used
        mean_dep = sum(all_dep) / seeds_used
        mean_blk = sum(all_blk) / seeds_used
        mean_busy_util = sum(all_busy_util) / seeds_used
        mean_dep_rate = sum(all_dep_rate) / seeds_used
        mean_lam_eff = sum(all_lam_eff) / seeds_used
        mean_p_loss = sum(all_p_loss) / seeds_used
        mean_busy_occ = sum(all_busy_occupied) / seeds_used
        
        # Convert W to minutes
        W_minutes = mean_W * 60.0
        
        res = {
            "L": round(mean_L, 6),
            "W": round(W_minutes, 6),
            "busy_frac": round(mean_busy_frac, 6),
            "p_wait": round(mean_p_wait, 6),
            "runtime_units": time_unit,
            "seed_list": seed_list,
            "seeds_used": seeds_used,
            "time_unit": time_unit,
            "win": round(win, 6),
            "arr": round(mean_arr, 6),
            "blk": round(mean_blk, 6),
            "busy_util": round(mean_busy_util, 6),
            "dep": round(mean_dep, 6),
            "dep_rate": round(mean_dep_rate, 6),
            "lam_eff": round(mean_lam_eff, 6),
            "p_loss": round(mean_p_loss, 6),
            "per_seed_L": [round(x, 6) for x in all_L],
            "per_seed_W": [round(x * 60.0, 6) for x in all_W],
            "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
            "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
            "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
        }
        
    print(json.dumps(res))

if __name__ == "__main__":
    main()
