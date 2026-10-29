import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 14.0 # per hour
    mu_base = 60.0 / 6.0 # per hour (mean service time 6 mins -> rate 10/hr)
    c = 2
    
    if args.pert == 'lam_up': lam = lam_base * 1.1
    elif args.pert == 'mu_up': mu = mu_base * 1.1
    elif args.pert == 'c_up': c = 3
    else: lam, mu = lam_base, mu_base
    
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * warmup_frac
    
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
    
    seeds_used = 0
    seed_list = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        customers = [] # list of dicts: {'arrival_time': float, 'service_time': float, 'start_service': float, 'end_service': float}
        queue = [] # indices or objects waiting
        servers_free_at = [0.0] * c
        
        total_area_N = 0.0
        total_area_minNC = 0.0
        count_arrivals_in_window = 0
        count_departures_in_window = 0
        count_blocked_in_window = 0
        count_waiting_on_arrival_in_window = 0
        total_wait_time_in_window = 0.0 # sum of (departure - arrival) for those who departed in window? 
        # W is avg time in system. Usually calculated as Total Time in System / Number of Departures.
        # But we need to handle the window carefully.
        # Let's track events.
        
        # State variables for integration
        last_event_time = 0.0
        current_N = 0
        current_minNC = 0
        
        # We need to simulate until horizon.
        # Events: Arrival, Departure
        
        while t < horizon:
            # Determine next event time
            next_dep = min(servers_free_at) if any(s > t for s in servers_free_at) else float('inf')
            # If no one is being served, next_dep is inf
            
            if next_arrival <= next_dep and next_arrival < horizon:
                # Process interval before arrival
                dt = next_arrival - last_event_time
                if last_event_time >= warmup_end:
                    total_area_N += current_N * dt
                    total_area_minNC += current_minNC * dt
                
                t = next_arrival
                last_event_time = t
                
                # Arrival logic
                # Check if anyone is waiting or if servers are busy
                # In FCFS with infinite buffer, "blocked" usually means loss system. 
                # Problem says "bank branch", implies queueing, not loss. 
                # However, output requires blk and p_loss. 
                # Standard M/M/c/K has blocking. M/M/c has infinite capacity.
                # If it's M/M/c, blk should be 0.
                # Let's assume infinite queue (M/M/2). So blk=0 always.
                
                # Draw service time now
                svc_time = rng.expovariate(mu)
                
                # Find a free server
                free_server_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_server_idx = k
                        break
                
                if free_server_idx != -1:
                    # Start immediately
                    start_t = t
                    end_t = t + svc_time
                    servers_free_at[free_server_idx] = end_t
                    # Add to active list? Or just track counts.
                    # For L calculation, N increases by 1.
                    current_N += 1
                    current_minNC = min(current_N, c)
                    
                    # Record departure event implicitly via servers_free_at
                    # We don't push to a global event queue easily without heap.
                    # Let's use a simple approach: maintain a list of future departures.
                    pass
                else:
                    # Queue up
                    # Wait for next server to become free
                    # This complicates the "next_dep" calculation if we don't have a heap.
                    # Let's switch to a priority queue (heapq) for events.
                    pass
                
                # Restarting with heapq approach for correctness and simplicity
                break # Break to restart loop structure below

        # --- RESTARTING SIMULATION LOGIC WITH HEAPQ ---
        import heapq
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [] # (time, type, data)
        # type: 0=Arrival, 1=Departure
        
        # Initial state
        servers_free_at = [0.0] * c
        queue = [] # List of (arrival_time, service_time)
        active_services = [] # List of (end_time, arrival_time, service_time) ? No, just track counts.
        
        # Better: Track number in system N, and number in queue Q.
        # N = Q + Served.
        # When arrival comes:
        #   If Served < c: Served++, schedule departure at t+svc.
        #   Else: Q++.
        # When departure comes:
        #   Served--.
        #   If Q > 0: Q--, Served++, schedule new departure from head of queue.
        
        num_served = 0
        num_queued = 0
        
        # Metrics accumulators for this seed
        area_N = 0.0
        area_minNC = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_prob_count = 0 # arrivals that found all servers busy
        total_system_time_sum = 0.0 # Sum of (dep - arr) for completed services in window
        
        last_t = 0.0
        
        # Push first arrival
        if next_arrival < horizon:
            heapq.heappush(events, (next_arrival, 0, None))
            
        while events or t < horizon:
            if not events:
                # Generate next arrival if within horizon
                if t < horizon:
                    next_arrival = t + rng.expovariate(lam)
                    if next_arrival < horizon:
                        heapq.heappush(events, (next_arrival, 0, None))
                    else:
                        break
                else:
                    break
            
            curr_t, ev_type, ev_data = heapq.heappop(events)
            
            if curr_t > horizon:
                break
                
            # Integrate areas from last_t to curr_t
            dt = curr_t - last_t
            if last_t >= warmup_end:
                N_curr = num_served + num_queued
                area_N += N_curr * dt
                area_minNC += min(N_curr, c) * dt
            
            last_t = curr_t
            t = curr_t
            
            if ev_type == 0: # Arrival
                # Draw service time
                svc = rng.expovariate(mu)
                
                # Check if blocked (loss system)? 
                # Problem description: "Bank branch... FCFS". Implies queue.
                # Output req: blk, p_loss. 
                # If it's M/M/c, blk=0. 
                # If it's M/M/c/K, K must be defined. Not defined. Assume infinite queue.
                # So blk is always 0.
                
                if last_t >= warmup_end:
                    arr_count_win += 1
                    if num_served >= c:
                        wait_prob_count += 1
                
                if num_served < c:
                    num_served += 1
                    dep_t = t + svc
                    heapq.heappush(events, (dep_t, 1, (t, svc)))
                else:
                    num_queued += 1
                    # Store customer info in queue
                    queue.append((t, svc))
                    
            elif ev_type == 1: # Departure
                # The departing customer was either in service or just started?
                # Actually, when a server becomes free, we pull from queue.
                # Here, a scheduled departure happens.
                # Who left? The one whose service ended.
                # We need to know their arrival time to calculate system time.
                # ev_data contains (arrival_time, service_time)
                arr_time, svc_time = ev_data
                
                if last_t >= warmup_end:
                    dep_count_win += 1
                    sys_time = t - arr_time
                    total_system_time_sum += sys_time
                
                num_served -= 1
                
                # If there are people in queue, start service for next
                if num_queued > 0:
                    next_cust = queue.pop(0)
                    num_queued -= 1
                    num_served += 1
                    dep_t = t + next_cust[1]
                    heapq.heappush(events, (dep_t, 1, next_cust))
                else:
                    # Server idle
                    pass
                    
            # Schedule next arrival if needed
            # Note: Poisson process memoryless property allows generating next inter-arrival on the fly
            # But we popped an event. We need to ensure the stream continues.
            # Easier: At each step, if no more arrivals scheduled, generate one.
            # But we might have multiple arrivals pending? No, we generate one at a time.
            # Let's check if we need to push next arrival.
            # We only pushed the first one.
            # After processing an arrival, we should push the next one.
            # But what if we processed a departure? We still need the next arrival.
            # Strategy: Keep a variable `next_arrival_time`.
            # If `next_arrival_time` is not in events, add it.
            
            # Correction: The above loop doesn't automatically generate subsequent arrivals.
            # Let's refactor slightly inside the loop.
            
            # Check if we need to add next arrival
            # We can do this after processing the event.
            # But we need to know if the previous arrival was consumed.
            # Simpler: Always keep one arrival in the queue if possible.
            
            # Let's re-evaluate the event generation.
            # Initialize: push first arrival.
            # On Arrival Event: 
            #   1. Process arrival.
            #   2. Generate next inter-arrival, set next_arrival_time = t + exp(lam).
            #   3. Push next_arrival_time if < horizon.
            # On Departure Event:
            #   1. Process departure.
            #   2. Do NOT generate arrival here. It's handled by the arrival stream.
            
            # Wait, if I push next arrival on every arrival event, I might miss the very first one if I didn't init properly.
            # And if I have a long gap between arrivals, the queue might empty out.
            
            # Revised Logic:
            # Maintain `next_arrival_time`.
            # Initially `next_arrival_time = rng.expovariate(lam)`.
            # Loop:
            #   Determine next event time: min(next_arrival_time, earliest_departure_in_events_heap?)
            #   Actually, using a single heap for both is cleaner.
            #   
            #   Let's stick to the heap but fix the arrival generation.
            #   When an Arrival event is popped:
            #     Process it.
            #     Calculate new `na = t + rng.expovariate(lam)`.
            #     If na < horizon, push (na, 0, None) to heap.
            #
            #   What about the initial state?
            #   Before loop: push (first_na, 0, None).
            
            # One issue: If the simulation ends due to horizon, we stop.
            
            # Let's implement this specific flow.
            
            if ev_type == 0:
                na = t + rng.expovariate(lam)
                if na < horizon:
                    heapq.heappush(events, (na, 0, None))

        # End of Seed Simulation
        
        win_len = horizon - warmup_end
        if win_len <= 0:
            continue
            
        L_est = area_N / win_len
        # W estimation: Little's Law W = L / lambda_eff? 
        # Or direct average: total_system_time_sum / dep_count_win
        # Direct average is better for finite windows.
        if dep_count_win > 0:
            W_est = total_system_time_sum / dep_count_win
        else:
            W_est = 0.0
            
        busy_frac_est = area_minNC / (win_len * c) # E[min(N,c)]/c
        busy_util_est = busy_frac_est # Same definition per prompt
        busy_occupied_est = 1.0 - (area_N - area_minNC)/area_N if area_N > 0 else 0.0 # Approx pi0? 
        # Prompt asks for busy_occupied = 1 - pi0.
        # pi0 is prob system empty.
        # Area where N=0 is part of area_N? No.
        # We need area_zero_N.
        # Let's recalculate area_zero_N during integration.
        
        # Re-run integration logic mentally to add area_zero_N
        # I will modify the code block above to include area_zero_N.
        
        # Since I cannot edit the executed code retroactively, I will rewrite the whole function cleanly.
        
        seeds_used += 1
        seed_list.append(seed)
        
        # Placeholder calculations based on the flawed loop above, will replace with clean version.
        # To save tokens and ensure correctness, I will write the final clean version directly.
        
        # ... (Skipping intermediate messy thought) ...
        
        # Final Clean Implementation follows in the print statement construction.
        
        # Collect results for this seed
        # Need to re-calculate with proper tracking of area_zero_N
        
        # Resetting for clean execution in the final code string:
        # I will construct the final Python code now.

# Constructing the final code string
code_lines = [
"import sys, json, random, argparse, heapq",
"def main():",
"    p = argparse.ArgumentParser()",
"    p.add_argument('--seeds', type=int, default=1)",
"    p.add_argument('--horizon', type=float, default=100.0)",
"    p.add_argument('--seed-start', type=int, default=42)",
"    p.add_argument('--pert', type=str, default='none')",
"    args = p.parse_args()",
"    lam_base = 14.0",
"    mu_base = 10.0",
"    c = 2",
"    if args.pert == 'lam_up': lam = lam_base * 1.1",
"    elif args.pert == 'mu_up': mu = mu_base * 1.1",
"    elif args.pert == 'c_up': c = 3",
"    else: lam, mu = lam_base, mu_base",
"    horizon = args.horizon",
"    warmup_end = horizon * 0.25",
"    res_L, res_W, res_bf, res_pw, res_arr, res_dep, res_blk, res_bu, res_dr, res_le, res_pl, res_bo = [], [], [], [], [], [], [], [], [], [], [], []",
"    seeds_used = 0; seed_list = []",
"    for i in range(args.seeds):",
"        seed = args.seed_start + i",
"        rng = random.Random(seed)",
"        t = 0.0; last_t = 0.0",
"        next_arr = rng.expovariate(lam)",
"        events = []",
"        if next_arr < horizon: heapq.heappush(events, (next_arr, 0, None))",
"        num_served = 0; num_queued = 0; queue = []",
"        area_N = 0.0; area_minNC = 0.0; area_zeroN = 0.0",
"        cnt_arr = 0; cnt_dep = 0; cnt_blk = 0; cnt_wait = 0; sum_sys_time = 0.0",
"        while events:",
"            curr_t, typ, data = heapq.heappop(events)",
"            if curr_t > horizon: break",
"            dt = curr_t - last_t",
"            if last_t >= warmup_end:",
"                N = num_served + num_queued",
"                area_N += N * dt",
"                area_minNC += min(N, c) * dt",
"                if N == 0: area_zeroN += dt",
"            last_t = curr_t; t = curr_t",
"            if typ == 0:",
"                svc = rng.expovariate(mu)",
"                if last_t >= warmup_end:",
"                    cnt_arr += 1",
"                    if num_served >= c
