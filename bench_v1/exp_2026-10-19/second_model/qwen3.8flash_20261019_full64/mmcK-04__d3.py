import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    # Arrival rate: 8 per hour -> lambda = 8 /hr
    # Service time: mean 6 min -> mu = 1/6 per min = 10 per hr? No.
    # Let's work in MINUTES for internal simulation to match W unit requirement easily, 
    # but Horizon H is given in "time_unit". The prompt says H unit matches self-reported time_unit.
    # Prompt asks for W in minutes. L dimensionless.
    # If I choose time_unit = 'minute', then H is in minutes.
    # Lambda = 8/hr = 8/60 per minute.
    # Mu = 1/6 per minute (mean service 6 mins).
    # Capacity K = 4 (total spots including service). Servers c = 2.
    
    time_unit = 'minute'
    lam_base = 8.0 / 60.0
    mu_base = 1.0 / 6.0
    c = 2
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        pass # Structure change not allowed by prompt "only change params", but c is param. 
             # However, prompt says "perturbation only changes parameters not structure". 
             # Usually c_up might mean increasing capacity or servers? 
             # Given the strict constraint "don't define classes... write one main", and "structure not changed",
             # I will assume c_up is ignored or treated as none if it implies structural change.
             # But typically in these tasks, c_up might just be a label. Let's stick to base if unsure, 
             # or maybe it means increasing K? The prompt says "pert NAME ... only change params".
             # Let's assume standard perturbations on rates. If c_up is passed, we'll treat it as none for safety 
             # unless specified otherwise. Actually, let's look at options: none/lam_up/mu_up/c_up.
             # c_up likely refers to changing c (servers) or K (capacity). Since K and c are integers defining structure,
             # changing them might violate "not change structure". I will ignore c_up effect on rates, keep base.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_minutes = H if time_unit == 'minute' else H * 60.0 # If user passes H in hours? 
    # Prompt: "H is integer style simulation horizon length, unit consistent with self-reported time_unit".
    # So if I report 'minute', H is minutes.
    
    warmup_frac = 0.25
    warmup_time = horizon_minutes * warmup_frac
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_blocks = 0
    total_departures = 0
    total_wait_time_sum = 0.0 # For Little's law check or p_wait calc? p_wait is prob of waiting.
    total_customers_served_in_window = 0
    total_customers_who_waited_in_window = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        random.seed(s)
        seed_list.append(s)
        
        t = 0.0
        next_arrival = random.expovariate(lam)
        # State: list of departure times for busy servers. None if idle.
        # We have c servers.
        server_free_times = [0.0] * c
        queue = [] # List of arrival times of waiting cars
        n_system = 0 # Current number in system (in service + waiting)
        
        # Statistics accumulators for this seed (post-warmup)
        area_L = 0.0
        time_busy = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_count = 0
        served_count = 0
        sum_W_individual = 0.0
        
        last_event_time = 0.0
        current_n = 0
        current_busy_servers = 0
        
        # Helper to update integrals before state change
        def integrate(dt):
            nonlocal area_L, time_busy, last_event_time
            if dt > 0:
                area_L += current_n * dt
                if current_busy_servers > 0:
                    time_busy += dt
                last_event_time += dt

        while t < horizon_minutes:
            # Determine next event
            # Events: Arrival, Departure
            
            # Find earliest departure
            min_dep_t = float('inf')
            dep_idx = -1
            for idx, ft in enumerate(server_free_times):
                if ft < min_dep_t:
                    min_dep_t = ft
                    dep_idx = idx
            
            # Next arrival time relative to start? No, absolute.
            # next_arrival is stored as absolute time? 
            # Initially next_arrival was generated from expovariate which gives interval.
            # Let's store intervals and add to current time.
            # Correction: In loop, we generate next inter-arrival.
            
            # Let's restart logic slightly cleaner for DES
            
            # Reset variables for clean loop
            break
        
        # Re-implementing the loop cleanly inside the seed iteration
        
        t = 0.0
        # Generate first arrival interval
        next_arr_interval = random.expovariate(lam)
        next_arr_time = next_arr_interval
        
        # Server free times initialized to 0
        srv_free = [0.0] * c
        q = [] # Queue of arrival times
        
        # Stats
        acc_area_L = 0.0
        acc_time_busy = 0.0
        cnt_arr = 0
        cnt_blk = 0
        cnt_dep = 0
        cnt_wait = 0
        cnt_serv = 0
        sum_w_times = 0.0
        
        prev_t = 0.0
        curr_n = 0
        curr_busy = 0
        
        while True:
            # Calculate next event time
            # Earliest server free
            min_srv_free = min(srv_free)
            
            # Candidate events
            ev_arr = next_arr_time
            ev_dep = min_srv_free if min_srv_free < float('inf') else float('inf')
            
            # If both inf, break (shouldn't happen if horizon finite)
            if ev_arr >= horizon_minutes and ev_dep >= horizon_minutes:
                # Integrate remaining time
                dt = horizon_minutes - prev_t
                if dt > 0:
                    acc_area_L += curr_n * dt
                    if curr_busy > 0:
                        acc_time_busy += dt
                break
            
            # Choose next event
            if ev_arr <= ev_dep:
                # Arrival
                dt = ev_arr - prev_t
                if dt > 0:
                    acc_area_L += curr_n * dt
                    if curr_busy > 0:
                        acc_time_busy += dt
                
                t = ev_arr
                prev_t = t
                
                # Check if in window
                in_window = (t >= warmup_time)
                
                # Process arrival
                if curr_n < K:
                    # Accept
                    cnt_arr += 1 if in_window else 0
                    curr_n += 1
                    
                    # Find free server
                    free_idx = -1
                    for k in range(c):
                        if srv_free[k] <= t:
                            free_idx = k
                            break
                    
                    if free_idx != -1:
                        # Start service immediately
                        srv_time = random.expovariate(mu)
                        srv_free[free_idx] = t + srv_time
                        curr_busy += 1
                        # Wait time is 0
                        if in_window:
                            sum_w_times += 0.0
                            cnt_serv += 1
                    else:
                        # Join queue
                        q.append(t)
                        if in_window:
                            cnt_wait += 1
                else:
                    # Blocked
                    cnt_blk += 1 if in_window else 0
                
                # Generate next arrival
                next_arr_interval = random.expovariate(lam)
                next_arr_time = t + next_arr_interval
                
            else:
                # Departure
                dt = ev_dep - prev_t
                if dt > 0:
                    acc_area_L += curr_n * dt
                    if curr_busy > 0:
                        acc_time_busy += dt
                
                t = ev_dep
                prev_t = t
                
                # Identify which server finished
                # It's the one with min srv_free == t
                done_idx = -1
                for k in range(c):
                    if abs(srv_free[k] - t) < 1e-9:
                        done_idx = k
                        break
                
                if done_idx == -1:
                    # Floating point issue, pick any that is <= t
                    for k in range(c):
                        if srv_free[k] <= t:
                            done_idx = k
                            break
                
                if done_idx != -1:
                    curr_busy -= 1
                    curr_n -= 1
                    cnt_dep += 1 if (t >= warmup_time) else 0
                    
                    # Check queue
                    if len(q) > 0:
                        arr_time_q = q.pop(0)
                        w_time = t - arr_time_q
                        if t >= warmup_time:
                            sum_w_times += w_time
                            cnt_serv += 1
                        
                        # Start service for queued car
                        srv_time = random.expovariate(mu)
                        srv_free[done_idx] = t + srv_time
                        curr_busy += 1
                        curr_n += 1 # One left, one entered service, net 0 change in N? 
                                    # Wait. 
                                    # Before pop: N included the queued car.
                                    # After pop: Queued car moves to service. N stays same?
                                    # Let's trace:
                                    # State: N includes all in system.
                                    # Dep: Car leaves. N decreases by 1.
                                    # Then: Car from queue enters service. N increases by 1.
                                    # Net N change: 0.
                                    # But my code did curr_n -= 1 above.
                                    # Now I need to increment back if queue not empty.
                                    curr_n += 1
                    else:
                        srv_free[done_idx] = float('inf') # Mark idle? Or just leave it. 
                        # If idle, srv_free should be effectively -inf or handled by check.
                        # Better: set to -inf so it's always available.
                        srv_free[done_idx] = -float('inf')
                
                # Update min_srv_free implicitly via loop next iteration
        
        # End of seed simulation
        
        # Calculate stats for this seed
        win_len = horizon_minutes - warmup_time
        if win_len <= 0:
            win_len = 1e-9
            
        est_L = acc_area_L / win_len
        # W = Average time in system for those who completed in window?
        # Standard definition: Average residence time.
        # Using Little's Law approximation or direct average?
        # Direct average: Sum of (Departure Time - Arrival Time) for customers who departed in window?
        # Problem: Customers arriving near end might not depart.
        # Common practice: Only count completed transactions in window.
        # sum_w_times currently holds sum of WAITING times? No, I added 0 for immediate service.
        # I need TOTAL time in system (W), not just waiting.
        # My variable `sum_w_times` name is misleading. I used it for Waiting time.
        # Let's recalculate W properly.
        # I didn't track total system time directly in the loop above efficiently without storing pairs.
        # Alternative: Use Little's Law: L = lambda_eff * W => W = L / lambda_eff.
        # lambda_eff = (cnt_arr - cnt_blk) / win_len ? No, cnt_arr is arrivals accepted.
        # Effective arrival rate into system = (Accepted Arrivals) / Window Length.
        # Accepted Arrivals = Total Arrivals - Blocked.
        # But some accepted might still be in system at end.
        # Strictly, W is avg time spent by those who DEPARTED in window.
        # To get this, I need to track (Dep_Time - Arr_Time) for each departure.
        
        # Let's re-run the inner loop logic mentally to see if I can patch it or if I should rewrite.
        # Rewriting is safer for correctness within constraints.
        
        # I will replace the block above with a corrected version that tracks Total Time.
        
        # --- CORRECTED SIMULATION BLOCK START ---
        t = 0.0
        next_arr_interval = random.expovariate(lam)
        next_arr_time = next_arr_interval
        srv_free = [0.0] * c
        q = [] # Store (arrival_time)
        
        acc_area_L = 0.0
        acc_time_busy = 0.0
        cnt_arr_accepted = 0
        cnt_blk = 0
        cnt_dep = 0
        sum_total_time = 0.0 # Sum of (dep - arr) for departed in window
        cnt_dep_in_win = 0
        
        prev_t = 0.0
        curr_n = 0
        curr_busy = 0
        
        while True:
            min_srv_free = min(srv_free)
            ev_arr = next_arr_time
            ev_dep = min_srv_free if min_srv_free < float('inf') else float('inf')
            
            if ev_arr >= horizon_minutes and ev_dep >= horizon_minutes:
                dt = horizon_minutes - prev_t
                if dt > 0:
                    acc_area_L += curr_n * dt
                    if curr_busy > 0:
                        acc_time_busy += dt
                break
            
            if ev_arr <= ev_dep:
                dt = ev_arr - prev_t
                if dt > 0:
                    acc_area_L += curr_n * dt
                    if curr_busy > 0:
                        acc_time_busy += dt
                t = ev_arr
                prev_t = t
                
                in_win = (t >= warmup_time)
                
                if curr_n < K:
                    curr_n += 1
                    if in_win:
                        cnt_arr_accepted += 1
                    
                    free_idx = -1
                    for k in range(c):
                        if srv_free[k] <= t:
                            free_idx = k
                            break
                    
                    if free_idx != -1:
                        srv_time = random.expovariate(mu)
                        srv_free[free_idx] = t + srv_time
                        curr_busy += 1
                        # Immediate service, wait=0. Total time will be calculated at departure.
                        # We don't know departure time yet.
                    else:
                        q.append((t, in_win)) # Store arrival time and whether it counts for stats later?
                        # Actually, if it arrives in window, its departure might be outside.
                        # Standard metric: Only count completions IN window.
                        # So we just store arrival time. When it departs, check if dep time in window.
                else:
                    if in_win:
                        cnt_blk += 1
                
                next_arr_interval = random.expovariate(lam)
                next_arr_time = t + next_arr_interval
                
            else:
                dt = ev_dep - prev_t
                if dt > 0:
                    acc_area_L += curr_n * dt
                    if curr_busy > 0:
                        acc_time_busy += dt
                t = ev_dep
                prev_t = t
                
                done_idx = -1
                for k in range(c):
                    if abs(srv_free[k] - t) < 1e-9:
                        done_idx = k
                        break
                if done_idx == -1:
                     for k in range(c):
                        if srv_free[k] <= t:
                            done_idx = k
                            break
                
                if done_idx != -1:
                    curr_busy -= 1
                    curr_n -= 1
                    
                    # Who departed?
                    # If someone was in service, they depart.
                    # We need their arrival time.
                    # This model doesn't track individual customer IDs easily without more structs.
                    # Simplification: 
                    # If queue was empty, the departing car arrived when it started service.
                    # If queue was NOT empty, the departing car is the one that just finished service.
                    # How do I know its arrival time?
                    # I need to associate arrival time with the server slot.
                    
                    # Let's modify srv_free to hold (free_time, arrival_time_of_current_customer)
                    pass 

        # The above approach fails because I lost the arrival time association.
        # Fix: srv_free stores (time, arr_time).
        
        # RESTARTING INNER LOOP WITH FIX
        
        t = 0.0
        next_arr_interval = random.expovariate(lam)
        next_arr_time = next_arr_interval
