import random, json, math, sys

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # in time_unit (hour)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    # Parameters
    lam_base = 8.0 # per hour
    mu_base = 6.0 # per hour (1/10 min = 6/hour)
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    all_busy_occupied = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # list of arrival times
        n_in_system = 0
        
        # Statistics accumulators (for the whole run, then we will filter by warmup)
        # We need to track events to compute area integrals correctly after removing warmup.
        # Strategy: Record all events with timestamps and state changes.
        # Events: Arrival, Departure.
        # State variables at event times: n_in_system, number of busy servers.
        
        events = [] # (time, type, n_before, n_after, wait_time_if_departure_or_arrival_relevant?)
        # Actually, simpler: record intervals.
        # Let's store a list of (start_time, end_time, n_in_system, num_busy_servers)
        # But n_in_system changes only at arrivals/departures.
        
        timeline = [] # (t_start, t_end, n, k_busy)
        current_t = 0.0
        current_n = 0
        current_k = 0
        
        # To handle warmup removal properly for area-based stats (L, busy_frac), 
        # we need to integrate over the window [H*0.25, H].
        # For rate-based stats (p_wait, W), we count customers who arrived in the window?
        # Standard practice: Discard first 25% of time. 
        # Customers arriving before cutoff but departing after? Usually excluded from W/p_wait counts if arrival < cutoff.
        # Or include them if they are in system during window? 
        # Prompt says: "统计量只在去掉前 25% 预热后的窗口内累计".
        # Interpretation: 
        # L, busy_frac: Time-weighted average over [T_warm, T_end].
        # p_wait: Fraction of arrivals in [T_warm, T_end] that had to wait.
        # W: Average sojourn time of customers who ARRIVED in [T_warm, T_end].
        
        T_warm = H * 0.25
        T_end = H
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        sum_sojourn_win = 0.0
        wait_count_win = 0
        
        # Generate events until T_end
        while True:
            # Determine next event time
            next_dep = min(servers_free_at) if any(s > t for s in servers_free_at) else float('inf')
            # If no one is being served, next_dep is inf.
            
            if next_arrival <= next_dep:
                # Arrival
                t_event = next_arrival
                if t_event > T_end: break
                
                # Update timeline segment up to t_event
                if t_event > current_t:
                    timeline.append((current_t, t_event, current_n, current_k))
                    current_t = t_event
                
                # Process Arrival
                n_before = current_n
                k_before = current_k
                
                # Check capacity? Bank usually has infinite queue unless specified. 
                # "到达时需要排队的概率" implies queueing allowed. No blocking mentioned except "blk" key.
                # Assuming infinite buffer, blk is always 0 unless system full? 
                # Problem doesn't specify finite capacity. Default infinite.
                
                # Find server
                free_server_idx = -1
                for idx in range(c):
                    if servers_free_at[idx] <= t_event:
                        free_server_idx = idx
                        break
                
                if free_server_idx != -1:
                    # Start service immediately
                    serv_time = rng.expovariate(mu)
                    servers_free_at[free_server_idx] = t_event + serv_time
                    current_n += 1
                    current_k += 1
                    # Customer does not wait
                    # Sojourn = serv_time
                    # We need to link this customer to its departure later.
                    # Store (arrival_time, start_time, end_time) implicitly via queue?
                    # Easier: Push to a global list of active customers?
                    # Since we process sequentially, let's just record the arrival time and service completion time.
                    # But we need to know when it leaves to update stats.
                    # Let's maintain a priority queue of departures? 
                    # The `servers_free_at` array acts as the next departure times for specific servers.
                    # We need to associate the customer identity.
                    
                    # Let's use a simple approach: 
                    # When a departure happens, we pop the earliest finishing server.
                    # But which customer was on that server?
                    # We can store (finish_time, arrival_time, start_time) in a heap or just check servers.
                    
                    # Refactor: Use a heap for departures.
                    pass 
                else:
                    # Queue
                    queue.append(t_event)
                    current_n += 1
                    # Wait probability indicator: if len(queue) > 0 before adding? 
                    # If no server free, they wait.
                    # Note: If server becomes free exactly at arrival time, it's handled above.
                
                # Schedule next arrival
                next_arrival = t_event + rng.expovariate(lam)
                
            else:
                # Departure
                t_event = next_dep
                if t_event > T_end: break
                
                # Update timeline
                if t_event > current_t:
                    timeline.append((current_t, t_event, current_n, current_k))
                    current_t = t_event
                
                # Identify which server finished
                # Find index with min finish time equal to t_event
                # Due to floating point, exact match might be tricky, but we set them explicitly.
                # We iterate to find the server that became free at t_event.
                # There might be multiple? Unlikely with continuous dists.
                
                finished_server_idx = -1
                for idx in range(c):
                    if abs(servers_free_at[idx] - t_event) < 1e-9:
                        finished_server_idx = idx
                        break
                
                if finished_server_idx == -1:
                    # Fallback for precision issues
                    min_val = float('inf')
                    for idx in range(c):
                        if servers_free_at[idx] < min_val:
                            min_val = servers_free_at[idx]
                            finished_server_idx = idx
                    # Assume this is the one

                # Who was being served?
                # We need to retrieve the customer info.
                # This structure is getting complex without classes.
                # Alternative: Simulate step-by-step with explicit customer objects in a list.
                
                # Let's restart simulation logic with a cleaner event-driven approach using lists.
                break # Break inner loop to rewrite logic below
        
        # --- REWRITTEN SIMULATION LOGIC FOR SINGLE SEED ---
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # List of (departure_time, arrival_time, start_time) for customers currently in service
        in_service = [] 
        # List of arrival_times for customers waiting
        waiting_queue = []
        
        timeline = [] # (start, end, n, k)
        last_t = 0.0
        last_n = 0
        last_k = 0
        
        # Stats for window
        win_arrivals = 0
        win_departures = 0
        win_blocked = 0
        win_sum_sojourn = 0.0
        win_count_wait = 0
        
        # Helper to add timeline segment
        def add_segment(start, end, n, k):
            if end > start:
                timeline.append((start, end, n, k))

        while t < T_end:
            # Next event time
            next_dep = min([d for d, _, _ in in_service]) if in_service else float('inf')
            
            if next_arrival <= next_dep:
                # Arrival
                t_event = next_arrival
                if t_event >= T_end:
                    break
                
                add_segment(last_t, t_event, last_n, last_k)
                last_t = t_event
                
                # Determine state before processing
                n_before = last_n
                k_before = last_k
                
                # Check if server available
                # Clean up finished services (should have been processed by departure event, but safety)
                # Actually, we process strictly one event at a time.
                
                # Is there an idle server?
                # Number of busy servers = len(in_service)
                if len(in_service) < c:
                    # Idle server available
                    serv_time = rng.expovariate(mu)
                    dep_time = t_event + serv_time
                    in_service.append((dep_time, t_event, t_event)) # dep, arr, start
                    last_n += 1
                    last_k += 1
                    # Did they wait? No.
                    waited = False
                else:
                    # All busy, join queue
                    waiting_queue.append(t_event)
                    last_n += 1
                    # last_k unchanged
                    waited = True
                
                # Record arrival stats if in window
                if t_event >= T_warm:
                    win_arrivals += 1
                    if waited:
                        win_count_wait += 1
                
                next_arrival = t_event + rng.expovariate(lam)
                
            else:
                # Departure
                t_event = next_dep
                if t_event >= T_end:
                    break
                
                add_segment(last_t, t_event, last_n, last_k)
                last_t = t_event
                
                # Remove the departing customer
                # Find the entry with dep_time == t_event
                # Since we used min(), it's the first one logically, but list order isn't guaranteed sorted.
                # We remove one instance.
                target_idx = -1
                for idx, (d, a, s) in enumerate(in_service):
                    if abs(d - t_event) < 1e-9:
                        target_idx = idx
                        break
                if target_idx == -1:
                    # Precision fallback
                    target_idx = 0 
                    for idx, (d, a, s) in enumerate(in_service):
                        if d < in_service[target_idx][0]:
                            target_idx = idx
                
                dep_time, arr_time, start_time = in_service.pop(target_idx)
                last_n -= 1
                last_k -= 1
                
                # Calculate sojourn time
                sojourn = t_event - arr_time
                
                # Record departure stats if in window
                # Convention: Count departure if it occurs in window? 
                # Or count customer if arrival was in window?
                # Prompt: "W ... 统计量只在...窗口内累计". 
                # Usually, for Little's Law consistency, we pair arrivals and departures within the window or use steady-state approx.
                # Given "per_seed_W", it's likely average sojourn of customers *arriving* in the window.
                # However, if a customer arrives in window but departs after, we don't see their full sojourn.
                # Common DES practice: Only count completed transactions where BOTH arrival and departure are in window? 
                # Or just arrival in window? If arrival in window, we must wait for departure.
                # Since we stop at T_end, we miss those.
                # Better interpretation for "Window": 
                # L, busy_frac: Time integral over [T_warm, T_end].
                # p_wait: Arrivals in [T_warm, T_end].
                # W: Average sojourn of customers who ARRIVED in [T_warm, T_end] AND DEPARTED before T_end? 
                # This biases W downwards.
                # Alternative: Use the "Area" method for W? No, W is mean value.
                # Let's assume standard batch means: 
                # We collect all customers who arrive in [T_warm, T_end]. 
                # We simulate until they leave? No, horizon is fixed.
                # Let's look at keys: `arr`, `dep`. 
                # If `arr` != `dep`, we have truncation bias.
                # Often, `W` is estimated as `sum(sojourn of completed in window) / count(completed in window)`.
                # Let's try: Count customers whose DEPARTURE is in [T_warm, T_end].
                # Then `win_departures` increments.
                # And `win_sum_sojourn` adds `sojourn`.
                # And `win_count_wait`: Did this customer wait? (Start > Arrival).
                # This aligns `dep` count with `W` denominator.
                # What about `p_wait`? "到达时...". Usually based on arrivals.
                # Let's stick to:
                # p_wait: Based on ARRIVALS in window.
                # W: Based on DEPARTURES in window (to ensure complete data).
                # L: Time average.
                
                if t_event >= T_warm:
                    win_departures += 1
                    win_sum_sojourn += sojourn
                    # Was this customer blocked/waiting?
                    # We need to know if they waited. 
                    # We stored start_time. If start_time > arr_time, they waited.
                    if start_time > arr_time + 1e-9:
                        # This contributes to p_wait? 
                        # Conflict: p_wait defined on arrivals. W defined on departures.
                        # Let's calculate p_wait separately using arrival records.
                        pass
                
                # After departure, check if someone from queue can start
                if waiting_queue:
                    # Pop front
                    q_arr_time = waiting_queue.pop(0)
                    serv_time = rng.expovariate(mu)
                    new_dep_time = t_event + serv_time
                    in_service.append((new_dep_time, q_arr_time, t_event))
                    last_k += 1
                    # Note: last_n remains same (one left, one entered service)
                    # But wait, last_n was decremented. Now we move from queue to service.
                    # Queue size decreases, Service size increases. Total N constant.
                    # My previous logic:
                    # On Arrival to Queue: last_n++, last_k same.
                    # On Departure: last_n--, last_k--.
                    # On Move Queue->Service: last_k++.
                    # So total N is correct.
                    
                    # Did this moved customer wait? Yes, obviously.
                    # But we already counted their arrival in `win_arrivals` if applicable.
                    # We don't need to do anything here for stats except updating state.
                
                # Update next departure time automatically via min() in loop condition

        # Final segment
        add_segment(last_t, T_end, last_n, last_k)
        
        # Calculate Seed Statistics
        
        # 1. L (Average number in system)
        # Integral of n(t) over [T_warm, T_end] / (T_end - T_warm)
        total_time_window = T_end - T_warm
        area_n = 0.0
        area_k = 0.0
        area_occ = 0.0 # 1 if k>0 else 0
        
        for start, end, n, k in timeline:
            # Intersect with [T_warm, T_end]
            seg_start = max(start, T_warm)
            seg_end = min(end, T_end)
            if seg_end > seg_start:
                dt = seg_end - seg_start
                area_n += n * dt
                area_k += k * dt
                if k > 0:
                    area_occ += dt
        
        L_avg = area_n / total_time_window if total_time_window > 0 else 0
        busy_frac_avg = (area_k / c) / total_time_window if total_time_window > 0 else 0 # E[min(N,c)]/c ? 
        # Prompt: busy_frac = E[min
