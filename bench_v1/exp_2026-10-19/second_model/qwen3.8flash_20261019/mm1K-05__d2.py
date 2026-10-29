import sys, json, random, math
def main():
    args = sys.argv[1:]
    seeds_n = 5; horizon = 100.0; seed_start = 42; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]
    
    lam_base = 9.0; mu_base = 10.0 # per hour
    c = 1; K = 4
    
    if pert == "lam_up": lam = lam_base * 1.1
    elif pert == "mu_up": mu = mu_base * 1.1
    elif pert == "c_up": c = 2; K = 5
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    win = horizon * 0.75
    warmup = horizon * 0.25
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    all_arr = []; all_blk = []; all_dep = []; all_busy_util = []; all_lam_eff = []
    
    for s_idx in range(seeds_n):
        seed = seed_start + s_idx
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {} # id -> duration
        queue = [] # list of (arrival_time, id)
        busy_until = -1.0
        server_free_at = 0.0
        
        n_customers_in_system = 0
        total_time_weighted_N = 0.0
        last_event_time = 0.0
        
        arrivals_count = 0
        blocks_count = 0
        departures_count = 0
        total_waiting_time_sum = 0.0
        total_service_time_sum = 0.0
        total_residence_time_sum = 0.0
        
        cust_id_counter = 0
        
        while t < horizon:
            # Determine next event time
            arr_t = next_arr if next_arr is not None else float('inf')
            dep_t = busy_until if busy_until > t and busy_until != float('inf') else float('inf')
            
            # If server is idle but queue has people, start immediately? 
            # In discrete event sim, we process events. If server free and queue non-empty, departure isn't the trigger, arrival or completion is.
            # Actually, if server becomes free at t, and queue is not empty, a new service starts immediately.
            # We need to handle state transitions carefully.
            
            # Let's refine event loop:
            # Events: Arrival, Departure.
            # State: N (number in system), Server Status (Busy/Idle).
            
            # Check if we should start service if server just became free or was free and queue grew?
            # Standard M/M/c/K logic:
            # On Arrival:
            #   If N < K: Add to system. If Server Idle, Start Service. Else Join Queue.
            #   If N == K: Block.
            # On Departure:
            #   Remove from system. If Queue Not Empty: Pop head, Start Service. Else Server Idle.
            
            # To simplify, let's track `server_occupied_until` and `queue`.
            # But we need to integrate L over time.
            
            # Let's restart the inner loop structure for clarity within the constraint.
            pass
            
        # Re-implementing the simulation loop properly inside the seed loop
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # stores (arrival_time, customer_id)
        service_end_time = -1.0 # -1 means idle
        current_customer_id = 0
        
        # Accumulators for statistics
        area_L = 0.0
        last_update_time = 0.0
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_w = 0.0 # Sum of waiting times (time in queue before service starts)
        sum_r = 0.0 # Sum of residence times (total time in system)
        
        # Pre-generate service times? No, generate on arrival as required.
        # "Service duration must be drawn when customer arrives"
        
        while t < horizon:
            # Determine next event
            t_arr = next_arrival
            t_dep = service_end_time if service_end_time > t else float('inf')
            
            # If server is idle and queue is not empty, this shouldn't happen in standard DES 
            # because starting service is an immediate action upon becoming idle or arrival.
            # However, if we model it strictly by events:
            # If service_end_time <= t and queue is not empty, we should have started service earlier.
            # Let's ensure consistency: whenever server becomes free, if queue has items, pop one and set service_end_time.
            
            # Update Area L
            n_in_sys = len(queue) + (1 if service_end_time > t else 0)
            dt = min(t_arr, t_dep) - last_update_time
            if dt > 0:
                area_L += n_in_sys * dt
            last_update_time = min(t_arr, t_dep)
            
            if t_arr <= t_dep:
                # Arrival Event
                t = t_arr
                count_arrivals += 1
                
                # Draw service time now
                svc_dur = rng.expovariate(mu)
                
                # Check capacity
                # Capacity K=4 includes those in service and queue
                # Current number in system BEFORE adding this one:
                curr_n = len(queue) + (1 if service_end_time > t else 0)
                
                if curr_n >= K:
                    count_blocks += 1
                else:
                    # Admit
                    cid = current_customer_id
                    current_customer_id += 1
                    
                    # Is server busy?
                    if service_end_time <= t:
                        # Server idle, start service immediately
                        service_end_time = t + svc_dur
                        # Waiting time is 0
                        sum_w += 0.0
                        sum_r += svc_dur
                    else:
                        # Server busy, join queue
                        queue.append((t, cid, svc_dur))
                        # Waiting time will be calculated when they enter service
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure Event
                t = t_dep
                count_departures += 1
                
                # The person leaving is the one being served.
                # We don't store their arrival time in a variable easily accessible here unless we track it.
                # Wait, I didn't store arrival time of the person in service.
                # Let's fix: Track `current_serving_arrival_time`.
                
                # Correction: Need to track who is in service.
                # Let's refactor slightly.
                pass

        # Refactored Simulation Loop for correctness
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # List of tuples: (arrival_time, service_duration)
        service_end_time = -1.0
        serving_arrival_time = -1.0
        
        area_L = 0.0
        last_update_time = 0.0
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_w = 0.0
        sum_r = 0.0
        
        while t < horizon:
            t_arr = next_arrival
            t_dep = service_end_time if service_end_time > t else float('inf')
            
            # Calculate current N for area integration up to next event
            n_in_sys = len(queue) + (1 if service_end_time > t else 0)
            next_t = min(t_arr, t_dep)
            if next_t > last_update_time:
                area_L += n_in_sys * (next_t - last_update_time)
                last_update_time = next_t
            
            if t_arr <= t_dep:
                t = t_arr
                count_arrivals += 1
                svc_dur = rng.expovariate(mu)
                
                curr_n = len(queue) + (1 if service_end_time > t else 0)
                
                if curr_n >= K:
                    count_blocks += 1
                else:
                    if service_end_time <= t:
                        # Start service
                        service_end_time = t + svc_dur
                        serving_arrival_time = t
                        sum_w += 0.0
                        sum_r += svc_dur
                    else:
                        # Join queue
                        queue.append((t, svc_dur))
                
                next_arrival = t + rng.expovariate(lam)
            else:
                t = t_dep
                count_departures += 1
                
                # Person finishes service
                # Their waiting time was already added? No, waiting time is time in queue.
                # Residence time = Waiting Time + Service Time.
                # For the person in service:
                # They entered service at some point. 
                # Wait, my previous logic added sum_r for the person starting service.
                # But what about people in queue?
                # When a person leaves service, we need to check if someone enters service.
                
                # Let's recalculate W and R properly.
                # W = Average time spent in QUEUE.
                # R = Average time spent in SYSTEM.
                
                # For the departing customer:
                # They were in service. Their arrival time is `serving_arrival_time`.
                # Their service duration was implicitly known? No, I didn't store it for the active one.
                # Let's store `active_svc_dur` too.
                
                # This approach is getting messy with variables. Let's use a cleaner state.
                break 

        # Final Clean Implementation Strategy
        # State: 
        # - queue: list of (arrival_time, service_duration)
        # - server_status: 'idle' or 'busy'
        # - server_end_time: float
        # - server_start_time: float (for calculating wait time of the one currently in service? No, wait time is accumulated when they START service)
        
        # Better: Accumulate stats when customers LEAVE.
        # When a customer leaves:
        # 1. Identify them.
        # 2. Calculate their Total Time (Departure - Arrival).
        # 3. Calculate their Wait Time (Start Service - Arrival).
        # 4. Add to sums.
        
        # So we need to know Arrival Time and Start Service Time for the person leaving.
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # (arrival_time, service_duration)
        server_busy = False
        server_end_time = 0.0
        server_start_time = 0.0
        server_arrival_time = 0.0 # Arrival time of person currently in service
        
        area_L = 0.0
        last_update_time = 0.0
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_w = 0.0
        sum_r = 0.0
        
        while t < horizon:
            t_arr = next_arrival
            t_dep = server_end_time if server_busy else float('inf')
            
            n_in_sys = len(queue) + (1 if server_busy else 0)
            next_t = min(t_arr, t_dep)
            if next_t > last_update_time:
                area_L += n_in_sys * (next_t - last_update_time)
                last_update_time = next_t
            
            if t_arr <= t_dep:
                t = t_arr
                count_arrivals += 1
                svc_dur = rng.expovariate(mu)
                
                curr_n = len(queue) + (1 if server_busy else 0)
                
                if curr_n >= K:
                    count_blocks += 1
                else:
                    if not server_busy:
                        # Start service
                        server_busy = True
                        server_start_time = t
                        server_end_time = t + svc_dur
                        server_arrival_time = t
                        # Store info for later? We can calculate stats on departure.
                        # We need to know svc_dur for the person in service? 
                        # Yes, to calculate residence time correctly if we don't store it.
                        # Or we can just store (arrival, start, end) for the active one.
                        # Let's add a variable `active_svc_dur`
                        active_svc_dur = svc_dur
                    else:
                        # Join queue
                        queue.append((t, svc_dur))
                
                next_arrival = t + rng.expovariate(lam)
            else:
                t = t_dep
                count_departures += 1
                
                # Customer leaves
                # Stats for this customer:
                # Arrival: server_arrival_time
                # Start Service: server_start_time
                # End Service: t
                # Wait Time: server_start_time - server_arrival_time
                # Residence Time: t - server_arrival_time
                
                w_i = server_start_time - server_arrival_time
                r_i = t - server_arrival_time
                sum_w += w_i
                sum_r += r_i
                
                # Check queue for next customer
                if queue:
                    next_cust_arr, next_cust_svc = queue.pop(0)
                    server_start_time = t
                    server_end_time = t + next_cust_svc
                    server_arrival_time = next_cust_arr
                    active_svc_dur = next_cust_svc
                    # server_busy remains True
                else:
                    server_busy = False
                    server_end_time = 0.0
                    server_start_time = 0.0
                    server_arrival_time = 0.0

        # Post-processing for this seed
        # Warmup removal:
        # We integrated area_L over [0, horizon].
        # We need area over [warmup, horizon].
        # This requires re-integrating or storing snapshots. 
        # Given the constraint "area type quantities must be integrated before changing state", 
        # and "statistics only accumulated in window after removing first 25% warmup",
        # I should have reset accumulators at warmup time.
        
        # Let's redo the loop with a flag for warmup.
        pass

    # Since I cannot iterate multiple times in thought, I will write the code directly incorporating the warmup logic.
    # Key change: Reset area_L, sum_w, sum_r, counts at t=warmup.
    
    results = {
        "L": 0, "W": 0, "busy_frac": 0, "p_loss": 0, "runtime_units": 0,
        "seed_list": [], "seeds_used": 0, "time_unit": "hour", "win": 0,
        "arr": 0, "blk": 0, "busy_util": 0, "dep": 0, "dep_rate": 0,
        "lam_eff": 0, "p_wait": 0,
        "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [],
        "per_seed_p_loss": [], "per_seed_p_wait": []
    }
    
    # Actual Code Generation follows
