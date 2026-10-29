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
    
    lam_base = 8.0 / 60.0  # per minute
    mu_base = 1.0 / 12.0   # per minute
    c = 3
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else (H * 60 if time_unit == "hour" else H / 60)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_win = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [] 
        # Event types: 0=arrival, 1=departure
        # We use a simple list-based priority queue since stdlib heapq is allowed but not imported? 
        # Actually heapq is standard library. Let's import it.
        import heapq
        
        heap = []
        heapq.heappush(heap, (next_arrival, 0, None))
        
        n_in_system = 0
        busy_servers = 0
        total_time_occupied = 0.0
        last_event_time = 0.0
        
        arrivals_count = 0
        blocked_count = 0
        departures_count = 0
        sum_waiting_times = 0.0
        sum_service_times = 0.0 # Not needed directly for W, but for L via Little's law check maybe?
        
        # For area integration of L and Busy Fraction
        area_L = 0.0
        area_busy = 0.0
        
        # Warmup removal: first 25% of horizon
        warmup_end = 0.25 * horizon_min
        
        # We need to track state changes to integrate properly.
        # Instead of complex event-driven integration with warmup cut-off mid-event,
        # we can simulate the whole thing and then filter or adjust.
        # However, "area-type quantities must be integrated before changing state".
        # And statistics only accumulated after removing first 25% warmup.
        
        # Strategy: Simulate full horizon. Record intervals [t_prev, t_curr] with constant N.
        # Then compute areas over [warmup_end, horizon].
        
        timeline = [] # List of (start_time, end_time, n_in_system, is_busy)
        
        current_n = 0
        current_is_busy = False # Station not empty means n > 0
        
        while True:
            if not heap:
                break
            t_curr, etype, data = heapq.heappop(heap)
            
            if t_curr > horizon_min:
                break
                
            # Integrate from last_event_time to t_curr
            dt = t_curr - last_event_time
            if dt > 0:
                timeline.append((last_event_time, t_curr, current_n, current_n > 0))
                
            last_event_time = t_curr
            
            if etype == 0: # Arrival
                arrivals_count += 1
                if current_n < K:
                    # Accept
                    current_n += 1
                    # Schedule departure
                    service_time = rng.expovariate(mu)
                    dep_time = t_curr + service_time
                    heapq.heappush(heap, (dep_time, 1, None))
                    
                    # If this arrival causes waiting? No, immediate service if server free.
                    # But here we just count system size. Waiting time calculation needs more detail.
                    # To calculate W accurately, we need to know when each customer starts service.
                    # This simple M/M/c/K model requires tracking individual customers or using 
                    # birth-death process properties. 
                    # Since we are doing discrete event simulation, let's attach info to events.
                    pass
                else:
                    blocked_count += 1
                    
            elif etype == 1: # Departure
                departures_count += 1
                current_n -= 1
                
        # Final interval
        if last_event_time < horizon_min:
            timeline.append((last_event_time, horizon_min, current_n, current_n > 0))
            
        # Calculate metrics over post-warmup window [warmup_end, horizon_min]
        win_len = horizon_min - warmup_end
        if win_len <= 0:
            continue
            
        area_L_post = 0.0
        area_busy_post = 0.0
        
        for start, end, n, is_b in timeline:
            s = max(start, warmup_end)
            e = min(end, horizon_min)
            if s < e:
                dt = e - s
                area_L_post += n * dt
                if is_b:
                    area_busy_post += dt
                    
        L_est = area_L_post / win_len
        busy_frac_est = area_busy_post / win_len
        
        # For W, p_wait, etc., we need more detailed simulation or analytical approximation?
        # The prompt asks for DES. Calculating W exactly in DES for M/M/c/K requires tracking 
        # entry/exit times of accepted customers.
        
        # Re-run simulation logic to capture customer details for W and p_wait?
        # Or modify the loop above. Let's redo the loop structure to capture customer lifetimes.
        
        # Reset for detailed run
        rng = random.Random(seed)
        heap = []
        next_arrival = rng.expovariate(lam)
        heapq.heappush(heap, (next_arrival, 0, None))
        
        n_in_sys = 0
        # Queue of customers waiting for service? In M/M/c/K, if n < c, service starts immediately.
        # If c <= n < K, they wait.
        # We need to track when service starts for each customer to get W.
        # Customer object: (arrival_time, service_duration, start_service_time)
        
        active_customers = [] # Those currently in system (waiting or serving)
        completed_customers = [] # Those who left
        
        # State variables for integration
        last_t = 0.0
        timeline_detail = []
        
        # We also need to handle the fact that service completion depends on which customer finishes.
        # With exponential distribution, memoryless property allows us to just schedule completions.
        # But to get W, we need to link completions to specific arrivals.
        
        # Let's maintain a list of scheduled departures linked to customer IDs.
        cust_id_counter = 0
        # Map: dep_time -> cust_id
        # But multiple deps at same time possible? Rare with continuous dists.
        
        # Better approach: Each arrival creates a customer.
        # If servers available, assign immediately.
        # Else, put in queue.
        # When a departure happens, pop from queue if any.
        
        # Simulation Loop
        t = 0.0
        next_arrival = rng.expovariate(lam)
        heap = [(next_arrival, 0, None)] # (time, type, id)
        
        n_in_sys = 0
        n_serving = 0
        queue = [] # List of customer IDs waiting
        
        # Track customer stats
        cust_stats = {} # id -> {arr_time, start_serv_time, end_time}
        
        last_t = 0.0
        timeline = []
        
        while heap:
            curr_t, etype, cid = heapq.heappop(heap)
            if curr_t > horizon_min:
                break
            
            dt = curr_t - last_t
            if dt > 0:
                timeline.append((last_t, curr_t, n_in_sys, n_in_sys > 0))
            last_t = curr_t
            
            if etype == 0: # Arrival
                new_cid = cust_id_counter
                cust_id_counter += 1
                cust_stats[new_cid] = {'arr': curr_t, 'start': None, 'end': None}
                
                if n_in_sys < K:
                    n_in_sys += 1
                    if n_serving < c:
                        # Start service immediately
                        n_serving += 1
                        serv_dur = rng.expovariate(mu)
                        dep_t = curr_t + serv_dur
                        cust_stats[new_cid]['start'] = curr_t
                        heapq.heappush(heap, (dep_t, 1, new_cid))
                    else:
                        # Wait
                        queue.append(new_cid)
                else:
                    # Blocked
                    pass
                    
            elif etype == 1: # Departure
                # cid is the customer leaving
                if cid in cust_stats:
                    cust_stats[cid]['end'] = curr_t
                    n_in_sys -= 1
                    n_serving -= 1
                    
                    # Check if someone can start service
                    if queue:
                        next_cid = queue.pop(0)
                        n_serving += 1
                        serv_dur = rng.expovariate(mu)
                        dep_t = curr_t + serv_dur
                        cust_stats[next_cid]['start'] = curr_t
                        heapq.heappush(heap, (dep_t, 1, next_cid))
                        
        if last_t < horizon_min:
            timeline.append((last_t, horizon_min, n_in_sys, n_in_sys > 0))
            
        # Compute Metrics Post-Warmup
        win_len = horizon_min - warmup_end
        
        area_L = 0.0
        area_busy = 0.0
        
        for s, e, n, b in timeline:
            ss = max(s, warmup_end)
            ee = min(e, horizon_min)
            if ss < ee:
                d = ee - ss
                area_L += n * d
                if b:
                    area_busy += d
                    
        L_val = area_L / win_len
        busy_frac_val = area_busy / win_len
        
        # Count arrivals, blocks, departures in window
        arr_w = 0
        blk_w = 0
        dep_w = 0
        wait_times_sum = 0.0
        num_completed_in_window = 0
        num_blocked_in_window = 0
        
        # Iterate through customers to find those relevant to window
        # A customer is counted in "arr" if their arrival time is in window?
        # Usually flow rates are based on events occurring in window.
        
        for cid, st in cust_stats.items():
            if st['arr'] >= warmup_end and st['arr'] <= horizon_min:
                arr_w += 1
                if st['start'] is None: # Was blocked? No, if start is None and end is None, it might still be in system or blocked.
                    # If it was blocked, it never entered system.
                    # How do we distinguish blocked vs still waiting?
                    # Blocked ones were rejected at arrival. They don't have an ID in cust_stats if we didn't add them?
                    # In my code, I added them to cust_stats even if blocked? 
                    # No, look at arrival block:
                    # if n_in_sys < K: ... else: pass (blocked).
                    # So blocked customers are NOT in cust_stats.
                    pass
                else:
                    # It entered system.
                    if st['end'] is not None and st['end'] <= horizon_min:
                        dep_w += 1
                        w = st['end'] - st['arr']
                        wait_times_sum += w
                        num_completed_in_window += 1
                    elif st['end'] is None:
                        # Still in system at end of horizon. Exclude from W average?
                        # Standard practice: exclude incomplete observations.
                        pass
                        
        # Blocked count: Total arrivals - Accepted arrivals.
        # Accepted arrivals = those in cust_stats with arr in window.
        # But some accepted might still be in system.
        # Let's count blocked explicitly during sim?
        # Easier: Re-scan or keep counter.
        # Let's assume arr_w includes both accepted and blocked?
        # In my loop, I incremented `arrivals_count` globally earlier, but here I'm iterating cust_stats.
        # cust_stats only has accepted ones.
        # So I need to count blocked ones separately.
        
        # Let's re-evaluate counting.
        # I will count events in the window by checking timestamps.
        
        # Recalculate counts properly
        arr_total_w = 0
        blk_total_w = 0
        dep_total_w = 0
        wait_sum_w = 0.0
        count_wait_w = 0
        
        # We lost the global counters in the second run. Let's use the timeline/events?
        # No, let's just iterate through all generated customers (accepted) and infer blocked?
        # Can't infer blocked easily without storing them.
        
        # Fix: Store blocked arrivals too? Or just count them in the loop.
        # I'll restart the detailed sim part mentally to ensure correctness.
        # Actually, I can just count `arrivals` as those where `n_in_sys < K` was true?
        # No, `arrivals` usually means Poisson stream hits.
        
        # Let's assume the previous loop logic:
        # `cust_stats` contains only ACCEPTED customers.
        # I need to count BLOCKED customers in the window.
        # I didn't store them.
        
        # Correction: In the arrival branch, if blocked, I should record it.
        # Since I can't change the code structure now without rewriting, I will estimate p_loss 
        # using the ratio of (Total Arrivals - Accepted) / Total Arrivals.
        # But I don't have Total Arrivals stored per window either.
        
        # Let's rely on the fact that I can re-run or fix the logic.
        # Given the constraints, I will output a best-effort JSON.
        # For the purpose of this task, I will assume standard definitions.
        
        # To make it work, I'll count blocked customers in the loop.
        # I'll rewrite the inner loop slightly in my head to include blocked tracking.
        
        # Okay, final plan for the code below:
        # 1. Simulate.
        # 2. Track: 
        #    - List of all arrival events (time, status: accepted/blocked)
        #    - List of all departure events (time, customer_id)
        #    - Customer records (arr_time, start_time, end_time)
        # 3. Filter by window [warmup, horizon].
        # 4. Compute L, BusyFrac via area integration.
        # 5. Compute W via average of (end-arr) for completed customers in window.
        # 6. Compute p_loss via blocked/total_arrivals in window.
        # 7. Compute p_wait via fraction of accepted customers who had start > arr.
        
        # Implementing this robustly.
        
        # Reset RNG for consistency? No, reuse the one from the detailed run above.
        # But I need to re-run because I didn't save blocked info.
        # I will perform the simulation again inside the seed loop with correct tracking.
        
        rng = random.Random(seed)
        heap = []
        next_arr = rng.expovariate(lam)
        heapq.heappush(heap, (next_arr, 0, None))
        
        n_in_sys = 0
        n_serving = 0
        queue = []
        
        # Tracking lists
        all_events = [] # (time, type, data)
        # type 0: arrival, data: (cid, accepted_bool)
        # type 1: departure, data: cid
        
        cust_records = {} # cid -> dict
        
        last_t = 0.0
        timeline = []
        
        cid_gen = 0
        
        while heap:
            t_curr, etype, data = heapq.heappop(heap)
            if t_curr > horizon_min:
                break
            
            dt = t_curr - last_t
            if dt > 0:
                timeline.append((last_t, t_curr, n_in_sys, n_in_sys > 0))
            last_t = t_curr
            
            if etype == 0: # Arrival
                cid = cid_gen
                cid_gen += 1
                accepted = False
                if n_in_sys < K:
                    accepted = True
                    n_in_sys += 1
                    cust_records[cid] = {'arr': t_curr, 'start': None, 'end': None}
                    if n_serving < c:
                        n_serving += 1
                        dur = rng.expovariate(mu)
                        dep_t = t_curr + dur
                        cust_records[cid]['start'] = t_curr
                        heapq.heappush(heap, (dep_t, 1, cid))
                    else:
                        queue.append(cid)
                else:
                    # Blocked
                    pass
                
                all_events.append((t_curr,
