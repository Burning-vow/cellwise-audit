import sys, json, math, random
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 50; horizon = 200.0; seed_start = 1000; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]

    # Parameters: lambda=8/hr, mu=12/hr (mean service 5 min)
    lam = 8.0
    mu = 12.0
    c = 1
    
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": mu *= 1.1
    elif pert == "c_up": c += 1 # Though problem says 1 server, perturbation might change structure? Prompt says "perturbation only changes parameters not structure". So c_up likely invalid or ignored for M/M/1. Let's assume standard M/M/1 logic holds. If c>1, it becomes M/M/c. But prompt implies single server context. I will stick to c=1 unless specified otherwise by a valid perturbation that doesn't break the model definition. Actually, "c_up" usually means increasing capacity. If the model is strictly M/M/1, this might be a trick or just increase effective rate? No, let's treat it as changing the number of servers if allowed, but the problem statement says "only 1 clerk". The constraint says "perturbation only changes parameters not structure". Changing c from 1 to 2 changes structure. So c_up probably does nothing or is an error case. I'll ignore structural changes and keep c=1. Or maybe it increases service rate? No, mu_up does that. I will leave c=1.

    time_unit = "hour"
    warmup_frac = 0.25
    win_len = horizon * (1 - warmup_frac)
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_busy = 0.0
    total_time_area = 0.0 # Integral of N(t) over window
    total_wait_time_sum = 0.0 # Sum of waiting times for customers who waited? Or system time? W is system time.
    total_system_time_sum = 0.0
    total_customers_in_window = 0
    
    seed_list = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        seed_list.append(current_seed)
        rng = random.Random(current_seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn at arrival. We need a queue.
        # For M/M/1 with FCFS, we can track completion times.
        # However, standard discrete event simulation uses events.
        # Events: Arrival, Departure.
        
        # To handle "service duration drawn at arrival", we store it.
        # Queue stores (arrival_time, service_duration).
        # Server status: busy_until_time
        
        queue = deque()
        busy_until = 0.0
        n_in_sys = 0
        
        # Statistics accumulators for this seed
        local_time_area = 0.0
        local_last_event_time = 0.0
        local_last_n = 0
        
        local_arr_count = 0
        local_dep_count = 0
        local_blk_count = 0
        local_busy_time = 0.0
        local_last_busy_state_time = 0.0
        local_was_busy = False
        
        local_system_time_sum = 0.0
        local_wait_time_sum = 0.0 # Waiting time before service starts
        local_customers_served_in_window = 0
        
        # Warmup boundary
        warmup_end = horizon * warmup_frac
        
        # We simulate until horizon.
        # We need to integrate area under N(t) curve.
        # Area += N(t) * dt between events.
        
        while True:
            # Determine next event time
            arr_t = next_arrival if next_arrival < horizon else float('inf')
            dep_t = busy_until if (busy_until > t and busy_until < horizon) else float('inf')
            
            # If queue is empty and server idle, dep_t is inf.
            # If server busy, dep_t is busy_until.
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= horizon:
                # Process remaining time up to horizon
                dt = horizon - t
                if t < warmup_end:
                    pass # Ignore pre-warmup stats accumulation for final metrics? 
                    # Requirement: "Statistics accumulated only in window after removing first 25% warmup"
                    # "Area type quantities must be integrated before changing state"
                    # This implies we integrate over the whole timeline but only add to sum if within window?
                    # Or we reset integrators at warmup_end?
                    # Easier: Integrate always, but subtract pre-warmup part? 
                    # Or: Only start accumulating when t >= warmup_end.
                    # Let's accumulate only when t >= warmup_end.
                
                # Update area for the segment [t, horizon]
                if t >= warmup_end:
                    local_time_area += n_in_sys * (horizon - t)
                    if local_was_busy:
                        local_busy_time += (horizon - t)
                elif horizon > warmup_end:
                    # Segment crosses warmup boundary
                    split_t = warmup_end
                    # Part before warmup: ignore
                    # Part after warmup:
                    local_time_area += n_in_sys * (horizon - split_t)
                    if local_was_busy:
                        local_busy_time += (horizon - split_t)
                
                t = horizon
                break
            
            # Advance time to next_t
            dt = next_t - t
            if dt > 0:
                if t >= warmup_end:
                    local_time_area += n_in_sys * dt
                    if local_was_busy:
                        local_busy_time += dt
                elif next_t > warmup_end:
                    # Crosses boundary
                    split_dt = warmup_end - t
                    rem_dt = next_t - warmup_end
                    # Before split: ignore
                    # After split:
                    local_time_area += n_in_sys * rem_dt
                    if local_was_busy:
                        local_busy_time += rem_dt
                
                t = next_t
            
            # Handle Event
            if next_t == arr_t:
                # Arrival
                local_arr_count += 1
                svc_dur = rng.expovariate(mu)
                
                # Check if blocked? Problem says "System stable", infinite buffer implied for M/M/1 queueing theory standard unless specified loss system.
                # Output keys include p_loss and blk. In M/M/1 with infinite buffer, p_loss=0.
                # If it were M/M/1/K, there would be losses.
                # Given "average hourly 8 people... stable", it's likely infinite buffer.
                # So blk should be 0.
                
                if len(queue) == 0 and t >= busy_until:
                    # Start service immediately
                    busy_until = t + svc_dur
                    n_in_sys += 1
                    if not local_was_busy:
                        local_was_busy = True
                else:
                    # Join queue
                    queue.append((t, svc_dur))
                    n_in_sys += 1
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif next_t == dep_t:
                # Departure
                # Who departs? The one currently being served.
                # We need to know their arrival time to calculate system time.
                # We didn't store the arrival time of the person in service explicitly in a variable accessible here easily without restructuring.
                # Let's maintain `current_service_start` and `current_service_end`.
                # When service starts, we record start time.
                
                # Wait, in the arrival block above, if service started immediately, we set busy_until.
                # We need to track the arrival time of the customer in service.
                # Let's add a variable `in_service_arrival_time`.
                
                # Correction: Need to refactor slightly to track in-service customer details.
                pass 

        # Re-implementing loop with proper tracking of in-service customer arrival time
        
        # Reset variables for correct implementation
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = deque()
        busy_until = 0.0
        n_in_sys = 0
        in_service_arrival_time = None
        
        local_time_area = 0.0
        local_arr_count = 0
        local_dep_count = 0
        local_blk_count = 0
        local_busy_time = 0.0
        local_was_busy = False
        local_system_time_sum = 0.0
        local_wait_time_sum = 0.0
        local_customers_completed_in_window = 0
        
        warmup_end = horizon * warmup_frac
        
        while t < horizon:
            arr_t = next_arrival if next_arrival < horizon else float('inf')
            dep_t = busy_until if (busy_until > t and busy_until < horizon) else float('inf')
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= horizon:
                dt = horizon - t
                if t >= warmup_end:
                    local_time_area += n_in_sys * dt
                    if local_was_busy:
                        local_busy_time += dt
                elif horizon > warmup_end:
                    rem_dt = horizon - warmup_end
                    local_time_area += n_in_sys * rem_dt
                    if local_was_busy:
                        local_busy_time += rem_dt
                t = horizon
                break
            
            dt = next_t - t
            if dt > 0:
                if t >= warmup_end:
                    local_time_area += n_in_sys * dt
                    if local_was_busy:
                        local_busy_time += dt
                elif next_t > warmup_end:
                    rem_dt = next_t - warmup_end
                    local_time_area += n_in_sys * rem_dt
                    if local_was_busy:
                        local_busy_time += rem_dt
            
            t = next_t
            
            if abs(next_t - arr_t) < 1e-9:
                # Arrival
                local_arr_count += 1
                svc_dur = rng.expovariate(mu)
                
                # Infinite buffer assumption -> no blocking
                # If buffer was finite, check here.
                
                if n_in_sys == 0:
                    # Idle server
                    busy_until = t + svc_dur
                    in_service_arrival_time = t
                    n_in_sys = 1
                    local_was_busy = True
                else:
                    # Busy or Queue non-empty
                    queue.append((t, svc_dur))
                    n_in_sys += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(next_t - dep_t) < 1e-9:
                # Departure
                local_dep_count += 1
                n_in_sys -= 1
                
                # Calculate System Time for departing customer
                if in_service_arrival_time is not None:
                    sys_time = t - in_service_arrival_time
                    wait_time = max(0, t - (in_service_arrival_time + svc_dur_of_first_in_queue_if_any? No.))
                    # Wait time = Time spent in queue before service starts.
                    # Service start time = ?
                    # We don't have explicit service start time stored for the *departing* customer if they waited.
                    # But we know:
                    # 1. They arrived at `in_service_arrival_time`.
                    # 2. They departed at `t`.
                    # 3. Their service duration was fixed at arrival.
                    # How to get wait time?
                    # Wait time = (Service Start Time) - (Arrival Time).
                    # Service Start Time = Departure Time - Service Duration.
                    # We need the service duration of the departing customer.
                    # We lost it!
                    
                    # Fix: Store service duration of the customer in service.
                    pass

        # Refactoring again to store service duration of in-service customer
        # Variables needed:
        # in_service_arrival_time
        # in_service_duration
        
        # Let's rewrite the inner loop cleanly.
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = deque() # Stores (arrival_time, service_duration)
        busy_until = 0.0
        n_in_sys = 0
        cur_svc_arr = None
        cur_svc_dur = None
        
        local_time_area = 0.0
        local_arr_count = 0
        local_dep_count = 0
        local_blk_count = 0
        local_busy_time = 0.0
        local_was_busy = False
        local_sys_time_sum = 0.0
        local_wait_time_sum = 0.0
        local_custs_in_window = 0 # Count of departures in window for averaging W? Or arrivals? Usually W is avg over completed customers.
        
        warmup_end = horizon * warmup_frac
        
        while t < horizon:
            arr_t = next_arrival if next_arrival < horizon else float('inf')
            dep_t = busy_until if (busy_until > t and busy_until < horizon) else float('inf')
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= horizon:
                dt = horizon - t
                if t >= warmup_end:
                    local_time_area += n_in_sys * dt
                    if local_was_busy:
                        local_busy_time += dt
                elif horizon > warmup_end:
                    rem_dt = horizon - warmup_end
                    local_time_area += n_in_sys * rem_dt
                    if local_was_busy:
                        local_busy_time += rem_dt
                t = horizon
                break
            
            dt = next_t - t
            if dt > 0:
                if t >= warmup_end:
                    local_time_area += n_in_sys * dt
                    if local_was_busy:
                        local_busy_time += dt
                elif next_t > warmup_end:
                    rem_dt = next_t - warmup_end
                    local_time_area += n_in_sys * rem_dt
                    if local_was_busy:
                        local_busy_time += rem_dt
            
            t = next_t
            
            if abs(next_t - arr_t) < 1e-9:
                local_arr_count += 1
                svc_dur = rng.expovariate(mu)
                
                if n_in_sys == 0:
                    busy_until = t + svc_dur
                    cur_svc_arr = t
                    cur_svc_dur = svc_dur
                    n_in_sys = 1
                    local_was_busy = True
                else:
                    queue.append((t, svc_dur))
                    n_in_sys += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(next_t - dep_t) < 1e-9:
                local_dep_count += 1
                n_in_sys -= 1
                
                # Stats for departing customer
                sys_time = t - cur_svc_arr
                # Wait time = sys_time - service_time
                wait_time = sys_time - cur_svc_dur
                
                # Accumulate only if departure happened in window
                if t >= warmup_end:
                    local_sys_time_sum += sys_time
                    local_wait_time_sum += wait_time
                    local_custs_in_window += 1
                
                # Next customer from queue?
                if queue:
                    nxt_arr, nxt_dur = queue.popleft()
                    cur_svc_arr = nxt_arr
                    cur_svc_dur = nxt_dur
                    busy_until = t + nxt_dur
                    # Server remains busy
                    local_was_busy = True
                else:
                    busy_until = float('inf')
                    cur_svc_arr = None
                    cur_svc_dur = None
                    local_was_busy = False

        # End of simulation for this seed
        
        # Compute Seed Metrics
        # L = Average Number in System = Time Area / Window Length
        # W = Average System Time = Total System Time Sum / Count of Customers Completed in Window
        # Busy Frac = Busy Time / Window Length
        # P(Wait) = Fraction of customers who waited? Or probability that an arriving customer waits?
        # Standard definition: P(wait) = fraction of time server is busy? No, that's utilization.
        # P(wait) usually means probability that an arriving customer has to wait.
        # In M/M/1, P(wait) = rho = lambda/mu.
        # Empirically: Count(Arrivals where n_in_sys > 0) / Total Arrivals in Window?
        # Or Count(Departures where wait_time > 0) / Total Departures?
        # Let's use Arrivals based on state at arrival time.
        # We didn't track "arrived and waited" count separately.
        # We can infer: If an arrival found n_in_sys > 0, they waited.
        # We need to track this during arrival event.
        
        # Re-run logic mentally: I missed tracking "did this arrival wait?"
        # I will add a counter `local_arr_waited` inside the loop.
        
        # Since I cannot re-edit the code block above easily in thought process, I will incorporate it in
