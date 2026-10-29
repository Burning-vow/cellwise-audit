import sys, json, math, random
from collections import deque

def main():
    args = sys.argv[1:]
    N, H, S, pert = 50, 100.0, 42, "none"
    for i in range(len(args)):
        if args[i] == "--seeds": N = int(args[i+1])
        elif args[i] == "--horizon": H = float(args[i+1])
        elif args[i] == "--seed-start": S = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]

    lam_base = 6.0
    mu_base = 10.0
    c = 1
    K = 4
    
    if pert == "lam_up": lam = lam_base * 1.2
    elif pert == "mu_up": mu = mu_base * 1.2
    elif pert == "c_up": c = 2; K = 5
    else: lam, mu = lam_base, mu_base

    seed_list = [S + i for i in range(N)]
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    
    total_arr, total_blk, total_dep = 0, 0, 0
    win_len = H * 0.75
    warmup = H * 0.25

    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = deque()
        service_end = -1.0
        busy_time = 0.0
        last_state_change_t = 0.0
        current_n = 0
        
        # Pre-generate arrivals and services? No, event driven is better but we need to handle horizon.
        # We simulate until t >= H.
        
        events = []
        # Initial arrival
        heapq_push(events, (next_arr, 'arr'))
        
        L_integral = 0.0
        W_sum = 0.0
        n_completed = 0
        n_blocked = 0
        n_arrivals_in_window = 0
        n_departures_in_window = 0
        
        # To calculate area-based stats correctly with warmup removal:
        # We track integral of N(t) over [warmup, H].
        # We track sum of waiting times for customers who arrived after warmup? 
        # Standard practice: Warmup removes initial transient. Stats accumulated only for t > warmup.
        # For W: Average time spent in system by customers who completed service after warmup? 
        # Or customers who arrived after warmup? Usually Little's Law holds for steady state.
        # Let's use: Customers who arrive after warmup and complete before H.
        # But simpler robust method: Time-average L via integral. W via average sojourn time of completions in window.
        
        # Re-implementing loop for clarity and correctness regarding "service duration drawn at arrival"
        
        t = 0.0
        next_event_time = rng.expovariate(lam)
        next_event_type = 'arr'
        next_service_duration = None # Not used yet
        
        # State variables
        n_system = 0
        last_update_t = 0.0
        integral_N = 0.0
        
        # Lists to store completion info for W calculation
        # We need to know when a customer arrives and when they leave.
        # If we remove warmup, we should only count customers whose entire stay or relevant part is in window?
        # Common approach: Discard first 25% of time. Count arrivals/departures/blocks that happen AFTER warmup.
        # For W: Average sojourn time of customers who DEPARTED after warmup.
        
        departures_info = [] # list of (arrival_time, departure_time)
        
        while t < H:
            # Determine next event
            if next_event_type == 'arr':
                t_next = next_event_time
            else:
                t_next = next_event_time
                
            # Check if there are pending services? 
            # In M/M/1/K, service starts immediately if server free.
            # So next event is either Arrival or Departure.
            
            # Actually, let's manage two potential next events: Arrival and Departure.
            # If server is busy, we have a scheduled departure.
            # If server is idle, no departure scheduled.
            
            # Let's refactor the event loop properly.
            pass
            
        # Restarting logic with proper event handling
        
        rng = random.Random(s)
        t = 0.0
        n_system = 0
        last_update_t = 0.0
        integral_N = 0.0
        
        # Next arrival time
        next_arr_t = rng.expovariate(lam)
        # Next departure time (None if idle)
        next_dep_t = None
        
        # Store arrival times of customers currently in system to compute W later
        # Since we need W for those who depart after warmup, we can just record (arrival_t, dep_t) pairs.
        records = [] 
        
        arr_count_total = 0
        blk_count_total = 0
        dep_count_total = 0
        
        while t < H:
            # Update integrals up to current time t? No, update when jumping to next event.
            # The state n_system is constant between events.
            
            # Find next event time
            candidates = []
            if next_arr_t <= H: candidates.append((next_arr_t, 'arr'))
            if next_dep_t is not None and next_dep_t <= H: candidates.append((next_dep_t, 'dep'))
            
            if not candidates: break
            
            t_next, type_next = min(candidates, key=lambda x: x[0])
            
            # Integrate N from last_update_t to t_next
            dt = t_next - last_update_t
            if last_update_t < warmup:
                # Split integration if crossing warmup boundary
                if t_next > warmup:
                    # Part before warmup ignored
                    # Part after warmup counted
                    overlap_start = max(last_update_t, warmup)
                    overlap_dt = t_next - overlap_start
                    integral_N += n_system * overlap_dt
            else:
                integral_N += n_system * dt
                
            last_update_t = t_next
            t = t_next
            
            if type_next == 'arr':
                arr_count_total += 1
                if n_system < K:
                    n_system += 1
                    # Draw service time now
                    svc_time = rng.expovariate(mu)
                    # If server was idle, start service immediately
                    if n_system == 1:
                        next_dep_t = t + svc_time
                        # Store arrival time for this customer
                        # We need to associate this specific arrival with its departure.
                        # Since it's FIFO, we can use a queue of arrival times.
                        # But we also need to handle blocking.
                        # Let's maintain a queue of arrival times for people in system.
                        # When someone departs, pop front.
                        # However, we don't have a global queue object here easily without classes.
                        # Alternative: Just record (arrival_t, dep_t) when departure happens.
                        # How to know which arrival corresponds to this departure?
                        # It's the oldest arrival still in system.
                        # We need a data structure. Let's use a simple list as queue since K is small.
                        # But I said no classes. A list is fine.
                        # Wait, I deleted the previous attempt. Let's initialize a queue list outside loop.
                        pass
                    else:
                        # Server busy, join queue
                        pass
                    # Add arrival time to queue
                    # Need to define q_arrivals outside loop
                else:
                    blk_count_total += 1
                    # Generate next arrival
                    next_arr_t = t + rng.expovariate(lam)
                    
            elif type_next == 'dep':
                dep_count_total += 1
                # Pop oldest arrival
                # This requires the queue variable
                pass

            # Generate next arrival if needed
            if type_next == 'arr':
                 next_arr_t = t + rng.expovariate(lam)
                 
            # Handle service scheduling
            # If server becomes free (n_system drops to 0), next_dep_t = None
            # If server becomes busy (n_system goes 0->1), next_dep_t = t + svc_time
            # If server stays busy, next_dep_t remains same? No, next_dep_t is absolute time.
            
            # This manual event management is getting complex without helper structures.
            # Let's stick to standard discrete event simulation pattern using a priority queue (heapq).
            
            break # Exit inner restart block to implement clean version below

    # Clean Implementation Start
    results = {
        "L": 0, "W": 0, "busy_frac": 0, "p_loss": 0, "runtime_units": "hour",
        "seed_list": seed_list, "seeds_used": N, "time_unit": "hour", "win": win_len,
        "arr": 0, "blk": 0, "busy_util": 0, "dep": 0, "dep_rate": 0, "lam_eff": 0, "p_wait": 0,
        "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [], "per_seed_p_loss": [], "per_seed_p_wait": []
    }
    
    import heapq
    
    all_L, all_W, all_BF, all_PL, all_PW = [], [], [], [], []
    all_Arr, all_Blk, all_Dep = [], [], []
    all_IntegralN, all_TimeWindow = [], []
    all_SojournSum, all_Completions = [], []
    all_BusyTime, all_TotalTime = [], []
    
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        n_system = 0
        last_update_t = 0.0
        integral_N = 0.0
        busy_time = 0.0
        
        # Queue of arrival times for customers in system
        cust_queue = deque()
        
        # Events: (time, type, data)
        # type: 'arr', 'dep'
        events = []
        
        # Initial arrival
        next_arr = rng.expovariate(lam)
        heapq.heappush(events, (next_arr, 'arr', None))
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sojourn_sum = 0.0
        completions_in_window = 0
        
        # We need to track which customers are in the window.
        # Strategy: Only accumulate stats for events occurring after warmup.
        # For L: Integral of N(t) for t in [warmup, H].
        # For W: Sum of (t_dep - t_arr) for customers who DEPART in [warmup, H].
        # For p_loss: Blocks in [warmup, H] / Arrivals in [warmup, H]? 
        # Or Blocks / Total Attempts? Usually p_loss is fraction of attempts lost.
        # Let's count arrivals and blocks in the window.
        
        while events:
            t_curr, typ, data = heapq.heappop(events)
            if t_curr > H: break
            
            # Update integrals from last_update_t to t_curr
            dt = t_curr - last_update_t
            if dt > 0:
                # Busy time accumulation
                if n_system > 0:
                    # Check overlap with window
                    if last_update_t < warmup:
                        if t_curr > warmup:
                            busy_time += (t_curr - warmup)
                    else:
                        busy_time += dt
                
                # N integral accumulation
                if last_update_t < warmup:
                    if t_curr > warmup:
                        integral_N += n_system * (t_curr - warmup)
                else:
                    integral_N += n_system * dt
                    
            last_update_t = t_curr
            
            if typ == 'arr':
                # Check if this arrival is in window
                in_window = t_curr >= warmup
                
                if in_window:
                    arr_count += 1
                
                if n_system < K:
                    n_system += 1
                    # Draw service time
                    svc = rng.expovariate(mu)
                    # Record arrival time
                    cust_queue.append(t_curr)
                    
                    # If server was idle (now 1), schedule departure
                    if n_system == 1:
                        heapq.heappush(events, (t_curr + svc, 'dep', None))
                else:
                    if in_window:
                        blk_count += 1
                
                # Schedule next arrival
                next_arr = t_curr + rng.expovariate(lam)
                heapq.heappush(events, (next_arr, 'arr', None))
                
            elif typ == 'dep':
                # Customer leaves
                n_system -= 1
                arr_time = cust_queue.popleft()
                
                in_window = t_curr >= warmup
                
                if in_window:
                    dep_count += 1
                    sojourn_sum += (t_curr - arr_time)
                    completions_in_window += 1
                
                # If server still has customers, start next service
                if n_system > 0:
                    # The next customer in queue starts service NOW
                    # We need their service time. 
                    # Problem: Service time was drawn at ARRIVAL.
                    # We stored arrival time, but not service time.
                    # Fix: Store (arrival_time, service_time) in queue.
                    pass 

        # Correction on Data Structure:
        # cust_queue should hold tuples (arrival_time, service_time)
        # But service_time is drawn at arrival.
        # When a customer arrives and joins queue, we draw svc.
        # If they start service immediately, we push dep event.
        # If they wait, we store (arr_t, svc_t) in queue.
        # When a dep occurs, if queue not empty, pop next (arr_t, svc_t) and push new dep event at t_curr + svc_t.
        
        # Re-running the loop logic mentally to ensure correctness...
        # The code above failed because I didn't store svc_time in queue.
        
        # Let's rewrite the inner loop carefully.
        
        # Reset for this seed
        rng = random.Random(s)
        t = 0.0
        n_system = 0
        last_update_t = 0.0
        integral_N = 0.0
        busy_time = 0.0
        cust_queue = deque() # Stores (arrival_time, service_time)
        events = []
        next_arr = rng.expovariate(lam)
        heapq.heappush(events, (next_arr, 'arr', None))
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        sojourn_sum = 0.0
        completions_in_window = 0
        
        while events:
            t_curr, typ, _ = heapq.heappop(events)
            if t_curr > H: break
            
            dt = t_curr - last_update_t
            if dt > 0:
                if n_system > 0:
                    if last_update_t < warmup:
                        if t_curr > warmup:
                            busy_time += (t_curr - warmup)
                    else:
                        busy_time += dt
                
                if last_update_t < warmup:
                    if t_curr > warmup:
                        integral_N += n_system * (t_curr - warmup)
                else:
                    integral_N += n_system * dt
            
            last_update_t = t_curr
            
            if typ == 'arr':
                in_win = t_curr >= warmup
                if in_win: arr_count += 1
                
                if n_system < K:
                    n_system += 1
                    svc = rng.expovariate(mu)
                    cust_queue.append((t_curr, svc))
                    if n_system == 1:
                        heapq.heappush(events, (t_curr + svc, 'dep', None))
                else:
                    if in_win: blk_count += 1
                
                next_arr = t_curr + rng.expovariate(lam)
                heapq.heappush(events, (next_arr, 'arr', None))
                
            elif typ == 'dep':
                n_system -= 1
                arr_t, svc_t = cust_queue.popleft()
                
                in_win = t_curr >= warmup
                if in_win:
                    dep_count += 1
                    sojourn_sum += (t_curr - arr_t)
                    completions_in_window += 1
                
                if n_system > 0:
                    # Start next service
                    next_arr_t, next_svc_t = cust_queue[0] # Peek
                    heapq.heappush(events, (t_curr + next_svc_t, 'dep', None))
        
        # Calculate metrics for this seed
        L_val = integral_N / win_len if win_len > 0 else 0
        W_val = sojourn_sum / completions_in_window if completions_in_window > 0 else 0
        BF_val = busy_time / win_len if win_len > 0 else 0
        PL_val = blk_count / arr_count if arr_count > 0 else 0
        PW_val = 1 - (dep_count / arr_count) if arr_count > 0 else 0 # Approx p_wait? 
        # p_wait usually means probability an arriving customer waits.
        # In M/M/1/K, P(wait) = P(N>=1 upon arrival)? No, P(N>=1) is prob server busy.
        # Prob wait = Prob(N>=1) given admitted? Or overall?
        # Let's define p_wait as fraction of admitted customers who waited.
