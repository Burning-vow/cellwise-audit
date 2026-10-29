import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0) # hours
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H_horizon = args.horizon
    S_start = args.seed_start
    pert_name = args.pert

    # Parameters in minutes
    lam_per_hour = 4.0
    service_time_min = 6.0
    
    if pert_name == 'lam_up':
        lam_per_hour *= 1.1
    elif pert_name == 'mu_up':
        service_time_min /= 1.1
    elif pert_name == 'c_up':
        pass # c is fixed at 1 for this problem description "single automatic car wash"

    time_unit = 'minute'
    horizon_min = H_horizon * 60.0
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_blocked = 0 # Not applicable for infinite queue, but keep for structure
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    seeds_used = 0

    for i in range(N_seeds):
        current_seed = S_start + i
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival_t = rng.expovariate(lam_per_hour / 60.0) # rate per minute
        
        queue = [] # List of tuples: (arrival_time, service_duration)
        server_free_t = 0.0
        busy_intervals = [] # List of (start, end) for integration
        
        arrivals_in_window = 0
        departures_in_window = 0
        wait_times_in_window = []
        system_times_in_window = []
        
        # Simulation loop
        while t < horizon_min:
            # Determine next event time
            arr_t = next_arrival_t
            dep_t = float('inf')
            if queue:
                # If server is free and queue not empty, departure happens immediately? 
                # No, we process events chronologically.
                # We need to know when the current service ends if server is busy.
                if t >= server_free_t and queue:
                    # Server was idle or just became idle, start next service
                    pass
                
                # Calculate next potential departure based on current state
                # This logic is tricky with discrete events. Let's use a standard event-driven approach.
                
                # Actually, let's simplify: 
                # Events are Arrivals and Departures.
                # State: Queue length, Server status (busy until T).
                
                # Let's restart the inner loop logic properly.
                break 

        # Re-implementing simulation loop correctly
        t = 0.0
        next_arrival_t = rng.expovariate(lam_per_hour / 60.0)
        queue = [] # Stores arrival times
        server_free_t = 0.0
        last_event_t = 0.0
        current_busy_state = False
        
        # For area calculation L
        area_L = 0.0
        # For busy fraction
        area_busy = 0.0
        
        # Stats collection
        local_arrivals = 0
        local_departures = 0
        local_waits = []
        local_systems = []
        
        while t < horizon_min:
            # Find next event
            next_dep_t = float('inf')
            if queue and server_free_t > t:
                 # If there are people waiting and server is busy, next dep is server_free_t
                 # But if server_free_t <= t, it means server is free, so we should have started service already.
                 # In DES, we handle transitions.
                 pass
            
            # Correct Event Selection:
            # Candidate 1: Next Arrival
            cand_arr = next_arrival_t
            # Candidate 2: Next Departure
            # If server is busy (server_free_t > t), next dep is server_free_t
            # If server is idle (server_free_t <= t) and queue is not empty, we must start service immediately.
            # So effectively, if queue is not empty, the "next departure" is determined by the service time of the head of the queue.
            
            if queue:
                if server_free_t <= t:
                    # Start service for first person
                    serv_dur = service_time_min
                    server_free_t = t + serv_dur
                    # Remove from queue? No, they are being served. 
                    # We need to track who is being served separately or just update server_free_t.
                    # The person leaves at server_free_t.
                    next_dep_t = server_free_t
                else:
                    next_dep_t = server_free_t
            else:
                next_dep_t = float('inf')
            
            next_event_t = min(cand_arr, next_dep_t)
            
            if next_event_t > horizon_min:
                break
                
            dt = next_event_t - t
            
            # Integrate Area for L (Number in system)
            # Number in system = len(queue) + (1 if server_free_t > t else 0)
            # Note: At exact event time, state changes. We integrate over [t, next_event_t).
            n_sys = len(queue)
            if server_free_t > t:
                n_sys += 1
            
            area_L += n_sys * dt
            
            # Integrate Busy Time
            if server_free_t > t:
                area_busy += dt
            
            t = next_event_t
            
            if t == cand_arr:
                # Arrival
                local_arrivals += 1
                if t >= warmup_end:
                    pass # Counted later
                
                queue.append(t) # Store arrival time
                
                # Generate next arrival
                next_arrival_t = t + rng.expovariate(lam_per_hour / 60.0)
                
            elif t == next_dep_t:
                # Departure
                # Who departed? The one at the front of the queue that started service.
                # Wait, my queue management above was slightly flawed regarding "who is being served".
                # Let's refine:
                # queue holds arrival times of those WAITING.
                # When service starts, we pop from queue? Or do we keep them in queue until departure?
                # Standard M/M/1: Queue includes those in service? Or separate?
                # Let's say `queue` contains ALL customers in system (waiting + serving).
                # But we need to know when the CURRENT service ends.
                
                # Correction:
                # Let's maintain `in_service` flag or just rely on `server_free_t`.
                # If `queue` stores all customers, then `len(queue)` is N.
                # When a customer arrives, append to queue.
                # If server is free, set `server_free_t = t + service_time`.
                # When `t == server_free_t`, remove the FIRST element from queue (FIFO).
                
                # Let's re-run the loop logic with this clear definition.
                pass

        # Resetting for clean implementation
        t = 0.0
        next_arrival_t = rng.expovariate(lam_per_hour / 60.0)
        queue = [] # List of arrival times of all customers currently in system
        server_free_t = 0.0
        
        area_L = 0.0
        area_busy = 0.0
        local_arrivals = 0
        local_departures = 0
        local_waits = []
        local_systems = []
        
        while t < horizon_min:
            # Determine next departure time
            if queue:
                # If server is free, start service for the first person in queue
                if server_free_t <= t:
                    # Pop the first person? No, they stay in queue until departure.
                    # Just set the finish time.
                    server_free_t = t + service_time_min
                
                next_dep_t = server_free_t
            else:
                next_dep_t = float('inf')
            
            next_event_t = min(next_arrival_t, next_dep_t)
            
            if next_event_t > horizon_min:
                # Advance to horizon
                dt = horizon_min - t
                n_sys = len(queue)
                if server_free_t > t:
                    n_sys += 1 # Should be covered by queue length if we don't pop immediately?
                    # My model: Queue contains everyone. So n_sys = len(queue).
                    # If server_free_t > t, someone is being served. They are in queue.
                    # So n_sys = len(queue).
                    pass
                
                area_L += len(queue) * dt
                if server_free_t > t:
                    area_busy += dt
                t = horizon_min
                break
            
            dt = next_event_t - t
            
            # Integrate
            area_L += len(queue) * dt
            if server_free_t > t:
                area_busy += dt
            
            t = next_event_t
            
            if t == next_arrival_t:
                local_arrivals += 1
                queue.append(t)
                next_arrival_t = t + rng.expovariate(lam_per_hour / 60.0)
                
            elif t == next_dep_t:
                # Departure
                # Remove the first person from queue
                if queue:
                    arr_time = queue.pop(0)
                    local_departures += 1
                    
                    # Record stats if in window
                    if t >= warmup_end:
                        w = t - arr_time # System time (W)
                        # Wait time = System time - Service time
                        wt = w - service_time_min
                        local_waits.append(wt)
                        local_systems.append(w)
                    
                    # Update server_free_t? 
                    # Since we popped, if queue is still not empty, the next person starts service NOW.
                    if queue:
                        server_free_t = t + service_time_min
                    else:
                        server_free_t = float('inf') # Idle
        
        # End of simulation for this seed
        
        # Calculate metrics for this seed
        sim_duration = horizon_min
        win_duration = sim_duration * (1 - warmup_frac)
        
        # L = Average number in system
        # Area integral was over full horizon. Need to adjust for warmup?
        # Requirement: "Statistics only accumulated in window after removing first 25% warmup"
        # "Area-type quantities must be integrated before changing state" -> This usually refers to the integration step itself.
        # To get steady state L, we should ideally integrate only over the window.
        # My previous code integrated over full horizon. I need to fix this.
        
        # Refactoring integration to respect window:
        # It's easier to store intervals or just reset accumulators at warmup_end.
        # Given the complexity of resetting mid-loop without missing partial intervals, 
        # I will re-run the logic mentally:
        # I'll accumulate `area_L_window` and `area_busy_window` starting from `warmup_end`.
        
        # Let's rewrite the inner loop part specifically for window accumulation.
        
        # Re-initializing for correct window stats
        t = 0.0
        next_arrival_t = rng.expovariate(lam_per_hour / 60.0)
        queue = []
        server_free_t = 0.0
        
        area_L_win = 0.0
        area_busy_win = 0.0
        count_arr_win = 0
        count_dep_win = 0
        waits_win = []
        systems_win = []
        
        # Helper to add to window if t >= warmup_end
        def add_to_window(dt, n_sys, is_busy):
            nonlocal area_L_win, area_busy_win
            if t >= warmup_end:
                area_L_win += n_sys * dt
                if is_busy:
                    area_busy_win += dt
            elif t + dt > warmup_end:
                # Partial interval crossing boundary
                split_dt = warmup_end - t
                rem_dt = dt - split_dt
                # First part not in window
                # Second part in window
                area_L_win += n_sys * rem_dt
                if is_busy:
                    area_busy_win += rem_dt

        while t < horizon_min:
            if queue:
                if server_free_t <= t:
                    server_free_t = t + service_time_min
                next_dep_t = server_free_t
            else:
                next_dep_t = float('inf')
            
            next_event_t = min(next_arrival_t, next_dep_t)
            
            if next_event_t > horizon_min:
                dt = horizon_min - t
                n_sys = len(queue)
                is_busy = server_free_t > t
                add_to_window(dt, n_sys, is_busy)
                t = horizon_min
                break
            
            dt = next_event_t - t
            n_sys = len(queue)
            is_busy = server_free_t > t
            add_to_window(dt, n_sys, is_busy)
            
            t = next_event_t
            
            if t == next_arrival_t:
                if t >= warmup_end:
                    count_arr_win += 1
                queue.append(t)
                next_arrival_t = t + rng.expovariate(lam_per_hour / 60.0)
                
            elif t == next_dep_t:
                if queue:
                    arr_time = queue.pop(0)
                    if t >= warmup_end:
                        count_dep_win += 1
                        w = t - arr_time
                        wt = w - service_time_min
                        waits_win.append(wt)
                        systems_win.append(w)
                    
                    if queue:
                        server_free_t = t + service_time_min
                    else:
                        server_free_t = float('inf')

        # Compute Seed Metrics
        win_len = horizon_min - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        L_est = area_L_win / win_len
        W_est = sum(systems_win) / len(systems_win) if systems_win else 0.0
        busy_frac_est = area_busy_win / win_len
        
        p_loss_est = 0.0 # Infinite buffer
        p_wait_est = sum(1 for w in waits_win if w > 0) / len(waits_win) if waits_win else 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seed_list.append(current_seed)
        
        total_L_sum += L_est
        total_W_sum += W_est
        total_busy_time += area_busy_win
        total_arrivals += count_arr_win
        total_departures += count_dep_win
        seeds_used += 1

    # Aggregate Metrics
    avg_L = total_L_sum / seeds_used if seeds_used else 0
    avg_W = total_W_sum / seeds_used if seeds_used else 0
    avg_busy_frac = total_busy_time / (seeds_used * (horizon_min - warmup_end)) if seeds_used else 0
    
    # Identity checks
    # L = lambda_eff * W
    # lambda_eff = total_arrivals / total_window_time
    total_window_time = seeds_used * (horizon_min - warmup_end)
    lam_eff = total_arrivals / total_window_time if total_window_time > 0 else 0
    
    # Convert rates to per hour for output
    dep_rate_per_hour = (total_departures / total_window_time) * 60.0 if total_window_time > 0 else 0
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": "minutes",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(horizon_min - warmup_end, 4),
        "arr": round(total_arrivals / seeds_used, 4) if seeds_used else 0,
        "blk": 0,
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(total_departures / seeds_used, 4) if seeds_used else 0,
        "dep_rate": round(dep_rate_per_hour, 4),
        "lam_eff": round(lam_eff * 60.0, 4), # Per hour
        "p_loss": 0.0,
        "p_wait": round(sum(per_seed_p_wait)/seeds_used, 4) if seeds_used else 0,
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
