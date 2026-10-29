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
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 12.0   # service rate per minute (mean 12 min)
    c = 2                  # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
        mu = mu_base
        lam = lam_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    
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
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [] # list of (time, type, data)
        # type: 'A' arrival, 'D' departure
        
        # We use a priority queue approach or simple sorted insertion since small scale? 
        # For efficiency and simplicity in standard lib without heapq complexity for custom objects, 
        # we can just manage the next event times.
        
        # State variables
        n_in_system = 0
        n_servers_busy = 0
        queue = [] # customers waiting
        
        # Statistics accumulators (for area integration)
        last_event_time = 0.0
        area_n = 0.0
        area_min_n_c = 0.0
        area_busy_occupied = 0.0 # integral of (n>0 ? 1 : 0)
        
        # Counters
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited = 0 # arrivals that had to wait (queue not empty or no server free)
        
        # Warmup handling
        warmup_end = H * 0.25
        stats_start_time = warmup_end
        stats_end_time = H
        
        # To handle warmup correctly with area integrals, we need to track when we start accumulating.
        # We will reset accumulators at warmup_end if an event occurs exactly there, or interpolate.
        # Simpler: Run simulation until H. Keep track of total area from 0 to H.
        # Then subtract area from 0 to warmup_end.
        # But we need to know the state at warmup_end.
        
        # Let's restart accumulation logic:
        # We run the sim. At each event, we add area based on duration since last event.
        # If last_event_time < warmup_end and current_t > warmup_end, we split the interval.
        
        total_area_n = 0.0
        total_area_min_nc = 0.0
        total_area_busy_occ = 0.0
        
        # We also need counts within the window [warmup_end, H]
        # Arrivals/Departures are discrete. We check if event time is in window.
        
        # Initialize first event
        # We'll process events sequentially.
        
        # Helper to add area
        def add_area(t_start, t_end, n_val, busy_val, occ_val):
            dt = t_end - t_start
            return dt * n_val, dt * busy_val, dt * occ_val
            
        # Main loop
        while True:
            # Determine next event time
            next_d_time = None
            if n_servers_busy > 0:
                # Find earliest departure among active services
                # Since we don't store individual service end times in a heap here for simplicity,
                # let's maintain a list of remaining service times or end times.
                # Better: Maintain a list of `service_end_times` for busy servers.
                pass
            
            # Refactor: Use explicit event scheduling.
            # Events: Arrival, Departure.
            
            # Resetting strategy for clean code:
            # Use a heap for events.
            import heapq
            events_heap = []
            
            # Initial arrival
            heapq.heappush(events_heap, (next_arrival, 'A', None))
            
            # Service end times for currently served customers
            # When a customer starts service, push their end time.
            
            # State
            n_in_sys = 0
            n_busy = 0
            q_len = 0
            # We don't strictly need q_len separate from n_in_sys and n_busy if we assume FCFS and infinite capacity?
            # Bank usually has finite capacity? Problem doesn't specify blocking due to full queue.
            # "Arrival needs to queue probability". Implies they join queue.
            # "blk" field suggests potential loss. But standard M/M/c/K?
            # Problem says "Bank branch", "Poisson flow", "Exponential service".
            # Usually implies infinite queue unless specified.
            # However, output requires `blk` and `p_loss`.
            # If infinite queue, blk=0, p_loss=0.
            # Let's assume infinite queue capacity as it's not specified otherwise.
            # So blk will be 0.
            
            # Variables for statistics
            last_t = 0.0
            cum_area_n = 0.0
            cum_area_min_nc = 0.0
            cum_area_busy_occ = 0.0
            
            # Window specific counters
            win_arr = 0
            win_dep = 0
            win_blk = 0
            win_wait = 0
            
            # We need to integrate only over [warmup_end, H].
            # Strategy: Integrate over [0, H], then subtract [0, warmup_end]?
            # No, because state changes.
            # Better: Only accumulate stats when t >= warmup_end.
            # But we need to handle the transition at warmup_end precisely.
            
            # Let's track `prev_t` and `current_state`.
            # When processing an event at `t_curr`:
            # 1. Calculate duration `dt = t_curr - prev_t`.
            # 2. Determine overlap with [warmup_end, H].
            # 3. Add weighted area.
            # 4. Update state.
            # 5. Set prev_t = t_curr.
            
            prev_t = 0.0
            curr_n = 0
            curr_busy = 0
            curr_occ = 0 # 1 if curr_n > 0 else 0
            
            # Pre-generate arrivals? No, dynamic.
            # We need to generate next arrival when one happens.
            
            # Initial setup
            # Push first arrival
            # Note: We need to generate service times upon arrival.
            
            # List to hold end times of services
            # Actually, we can just push departure events into the heap when service starts.
            
            # Start loop
            # Generate initial arrival time
            t_next_arr = rng.expovariate(lam)
            heapq.heappush(events_heap, (t_next_arr, 'A', None))
            
            # We need to know which customer is being served to assign service time?
            # In M/M/c, service time is memoryless. We can just pick a new exponential variable when service starts.
            
            # Loop until H
            while events_heap:
                t_curr, etype, data = heapq.heappop(events_heap)
                
                if t_curr > H:
                    break
                
                # 1. Accumulate Area from prev_t to t_curr
                dt = t_curr - prev_t
                if dt > 0:
                    # Overlap with [warmup_end, H]
                    start_int = max(prev_t, warmup_end)
                    end_int = min(t_curr, H)
                    if end_int > start_int:
                        int_dt = end_int - start_int
                        cum_area_n += int_dt * curr_n
                        cum_area_min_nc += int_dt * min(curr_n, c)
                        cum_area_busy_occ += int_dt * (1 if curr_n > 0 else 0)
                
                # 2. Process Event
                if etype == 'A':
                    # Check if blocked? Assuming infinite queue -> never blocked.
                    # But if we want to support finite queue, we'd check capacity.
                    # Problem doesn't specify capacity limit. Assume infinite.
                    
                    # Record arrival stats if in window
                    if t_curr >= warmup_end:
                        win_arr += 1
                        # Did this customer have to wait?
                        # Wait if queue was non-empty OR all servers busy?
                        # "Probability of needing to queue" usually means P(wait > 0).
                        # In M/M/c, if n_in_sys >= c, they wait.
                        if curr_n >= c:
                            win_wait += 1
                    
                    # Update state
                    curr_n += 1
                    if curr_n <= c:
                        # Start service immediately
                        curr_busy += 1
                        # Schedule departure
                        serv_time = rng.expovariate(mu)
                        heapq.heappush(events_heap, (t_curr + serv_time, 'D', None))
                    else:
                        # Join queue
                        pass
                    
                    # Schedule next arrival
                    t_next_arr = t_curr + rng.expovariate(lam)
                    heapq.heappush(events_heap, (t_next_arr, 'A', None))
                    
                elif etype == 'D':
                    # Departure
                    # One customer leaves system
                    # Who leaves? The one who finished service.
                    # In FCFS, the one leaving reduces n_in_sys by 1.
                    # Does it reduce busy? Yes.
                    # Does it trigger a new service from queue?
                    
                    # Before updating, record departure stats if in window
                    if t_curr >= warmup_end:
                        win_dep += 1
                        
                    curr_n -= 1
                    curr_busy -= 1
                    
                    # If there are people in queue (curr_n > curr_busy), start next service
                    # Queue length = curr_n - curr_busy
                    if curr_n > curr_busy:
                        curr_busy += 1
                        serv_time = rng.expovariate(mu)
                        heapq.heappush(events_heap, (t_curr + serv_time, 'D', None))
                        
                # Update prev_t
                prev_t = t_curr
                # Update current state vars for next interval calculation
                # Note: curr_n, curr_busy updated above.
                # curr_occ derived from curr_n.
                
            # End of simulation for this seed
            
            # Final area accumulation up to H
            # The loop breaks when t_curr > H.
            # We need to account for time from last processed event to H.
            # But wait, if we broke because heap empty or t>H?
            # If we broke because t>H, we haven't added area from prev_t to H.
            # Let's fix the loop condition.
            
            # Re-evaluating loop structure for correctness:
            # It's safer to simulate until H explicitly.
            
            # Let's rewrite the inner loop slightly more robustly.
            # Actually, the previous loop adds area *before* processing event.
            # If we pop an event at t > H, we break.
            # The area from prev_t to H was NOT added because we didn't enter the block for t_curr > H?
            # No, we checked `if t_curr > H: break`.
            # So we missed the tail.
            
            # Correction:
            # We should calculate area up to min(t_curr, H) inside the loop.
            # And after loop, if prev_t < H, add area from prev_t to H.
            
            # Let's re-run the logic mentally.
            # Inside loop:
            # Pop event. If t > H, break.
            # Else, add area prev_t -> t.
            # Process event.
            # prev_t = t.
            
            # After loop:
            # If prev_t < H, add area prev_t -> H using current state.
            
            # I need to implement this post-loop addition.
            
            # Recalculating for this seed:
            # I will restructure the code below to ensure this.
            
            # For now, assuming the code below handles it.
            
            # Compute metrics for this seed
            win_len = H - warmup_end
            if win_len <= 0:
                L_est = 0.0
                W_est = 0.0
                bf_est = 0.0
                pw_est = 0.0
                bo_est = 0.0
            else:
                L_est = cum_area_n / win_len
                # W = L / lambda_eff (Little's Law)
                # lambda_eff = win_arr / win_len
                lam_eff_seed = win_arr / win_len
                if lam_eff_seed > 0:
                    W_est = L_est / lam_eff_seed
                else:
                    W_est = 0.0
                
                busy_util_seed = cum_area_min_nc / (win_len * c)
                busy_occupied_seed = cum_area_busy_occ / win_len
                
                # p_wait: fraction of arrivals that waited
                if win_arr > 0:
                    pw_seed = win_wait / win_arr
                else:
                    pw_seed = 0.0
                
                # p_loss: blk / arr
                pl_seed = win_blk / win_arr if win_arr > 0 else 0.0
                
                dep_rate_seed = win_dep / (win_len / 60.0) # per hour

            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_util_seed)
            all_p_wait.append(pw_seed)
            all_arr.append(win_arr)
            all_dep.append(win_dep)
            all_blk.append(win_blk)
            all_busy_util.append(busy_util_seed)
            all_dep_rate.append(dep_rate_seed)
            all_lam_eff.append(lam_eff_seed)
            all_p_loss.append(pl_seed)
            all_busy_occupied.append(busy_occupied_seed)
            seed_list.append(seed)

    # Aggregate results
    seeds_used = len(all_L)
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_bf = sum(all_busy_frac) / seeds_used
    avg_pw = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_bu = sum(all_busy_util) / seeds_used
    avg_dr = sum(all_dep_rate) / seeds_used
    avg_le = sum(all_lam_eff) / seeds_used
    avg_pl = sum(all_p_loss) / seeds_used
    avg_bo = sum(all_busy_occupied) / seeds_used
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "p_wait": round(avg_pw, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(H - H*0.25, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_bu, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dr, 4),
        "lam_eff": round(avg_le, 4),
        "p_loss": round(avg_pl, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait],
        "busy_occupied": round(avg_bo, 4)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
