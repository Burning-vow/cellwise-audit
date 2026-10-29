import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in hours and minutes
    # Arrival rate: 6 per hour
    lam = 6.0 
    # Service time mean: 7.5 min for stage 1, 5 min for stage 2
    mu1_mean_min = 7.5
    mu2_mean_min = 5.0
    
    # Convert service rates to per hour if needed, or keep time unit as minute?
    # Let's use MINUTES as internal time unit for precision with small numbers.
    # Arrival rate: 6 per hour = 6/60 = 0.1 per minute
    lam_per_min = 6.0 / 60.0
    mu1_rate_per_min = 1.0 / mu1_mean_min
    mu2_rate_per_min = 1.0 / mu2_mean_min
    
    # Perturbations
    if pert == 'lam_up':
        lam_per_min *= 1.1
    elif pert == 'mu_up':
        mu1_rate_per_min *= 1.1
        mu2_rate_per_min *= 1.1
    elif pert == 'c_up':
        # Cost perturbation doesn't affect queueing stats directly unless defined otherwise
        pass

    horizon_min = H * 60.0 # If H is in hours? The prompt says "H is integer style simulation horizon length, unit consistent with self-reported time_unit".
    # Prompt example: --horizon H. Usually H is large. Let's assume H is in the same unit as time_unit.
    # I set time_unit = 'minute'. So H should be interpreted as minutes?
    # But standard DES often uses hours for arrival rates.
    # Let's stick to time_unit = 'minute' and interpret H as minutes.
    # Wait, "H is integer style... unit consistent with self-reported time_unit".
    # If I report time_unit='minute', then H is minutes.
    
    total_time = H 
    
    warmup_frac = 0.25
    warmup_end = total_time * (1 - warmup_frac)
    window_len = total_time * warmup_frac
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_dep = []
    results_blk = []
    
    seed_list = []
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        # Queue 1, Queue 2
        q1 = [] # list of (arrival_time, service_duration)
        q2 = []
        
        # Server status
        srv1_free_at = 0.0
        srv2_free_at = 0.0
        
        # Event list: (time, type, data)
        # Types: 'arr', 'dep1', 'dep2'
        events = []
        
        # Generate initial arrivals up to horizon
        t = 0.0
        while True:
            inter_arr = rng.expovariate(lam_per_min)
            t += inter_arr
            if t > total_time:
                break
            # Draw service times immediately upon arrival
            s1 = rng.expovariate(mu1_rate_per_min)
            s2 = rng.expovariate(mu2_rate_per_min)
            events.append((t, 'arr', (s1, s2)))
            
        events.sort(key=lambda x: x[0])
        
        # Statistics accumulators for the window [warmup_end, total_time]
        # We need to track system state over time to calculate L (area under curve)
        # And W (sum of sojourn times for completed jobs in window)
        
        # For L calculation via area:
        # We need to know number of items in system at any time.
        # Items are in System if they have arrived but not yet departed Stage 2.
        # They are in Q1 or being served by 1, or in Q2 or being served by 2.
        
        # To compute area accurately, we can integrate step functions.
        # We'll process events chronologically.
        
        # Track active jobs in system
        # A job is active from its arrival time until its final departure time.
        # However, we don't know final departure time until it happens.
        # Alternative: Maintain count of jobs in system. Update on Arr (+1) and Dep (-1).
        # Integrate count over time.
        
        current_count = 0
        last_event_time = 0.0
        area_sum = 0.0 # Integral of count over time
        
        # For W: Sum of (departure_time - arrival_time) for jobs departing in window.
        w_sum = 0.0
        dep_count_window = 0
        
        # For Busy Fraction:
        busy1_time = 0.0
        busy2_time = 0.0
        last_srv1_change = 0.0
        last_srv2_change = 0.0
        srv1_is_busy = False
        srv2_is_busy = False
        
        # For Loss/Wait probabilities:
        # In this model, no loss (infinite buffer implied by "queueing"). p_loss = 0.
        # p_wait: fraction of arrivals that had to wait? Or fraction of time queues non-empty?
        # Usually p_wait refers to probability an arriving customer waits.
        # Let's track: did the customer start service immediately?
        # If arrival time >= server free time, no wait. Else wait.
        # We need to check this at arrival event.
        
        arr_count_window = 0
        wait_count_window = 0
        
        # Process events
        # We need to handle the fact that service completion might trigger next start.
        
        # Helper to add event
        def add_event(time, etype, data):
            events.append((time, etype, data))
            # Since we are iterating through a sorted list, adding new events requires re-sorting or using a heap.
            # Given constraints, let's use a simple approach: collect all events first? 
            # No, service completions depend on previous states.
            # Use heapq.
            import heapq
            heapq.heappush(events_heap, (time, etype, data))

        # Re-implement with Heap
        import heapq
        events_heap = []
        
        # Initial arrivals
        t = 0.0
        while True:
            inter_arr = rng.expovariate(lam_per_min)
            t += inter_arr
            if t > total_time:
                break
            s1 = rng.expovariate(mu1_rate_per_min)
            s2 = rng.expovariate(mu2_rate_per_min)
            heapq.heappush(events_heap, (t, 'arr', (s1, s2)))
            
        # Initialize accumulators
        current_count = 0
        last_time = 0.0
        area_sum = 0.0
        
        busy1_time = 0.0
        busy2_time = 0.0
        srv1_free_at = 0.0
        srv2_free_at = 0.0
        srv1_busy_until = 0.0
        srv2_busy_until = 0.0
        
        # Queues
        q1 = [] # stores (arrival_time, s1, s2)
        q2 = [] # stores (arrival_time, s2)
        
        w_sum = 0.0
        dep_count_window = 0
        arr_count_window = 0
        wait_count_window = 0
        
        # We need to update integrals when time advances.
        # Function to advance time and update areas/busy times
        def update_integrals(now):
            nonlocal area_sum, busy1_time, busy2_time, last_time, srv1_busy_until, srv2_busy_until
            
            dt = now - last_time
            if dt < 0: return
            
            # Area
            area_sum += current_count * dt
            
            # Busy times
            # Server 1 is busy if now <= srv1_busy_until? 
            # Actually, we track intervals.
            # Simpler: Check if server was busy during [last_time, now]
            # This logic is tricky with discrete events.
            # Better: When a server starts/stops, record the interval.
            # Let's maintain `srv1_last_start` and `srv1_last_stop`.
            # Or just accumulate based on state changes.
            
            # Let's change strategy: Accumulate busy time only when state changes.
            # Pass.
            pass

        # Let's restart the loop logic more carefully.
        
        # Reset
        events_heap = []
        t = 0.0
        while True:
            inter_arr = rng.expovariate(lam_per_min)
            t += inter_arr
            if t > total_time:
                break
            s1 = rng.expovariate(mu1_rate_per_min)
            s2 = rng.expovariate(mu2_rate_per_min)
            heapq.heappush(events_heap, (t, 'arr', (s1, s2)))
            
        current_count = 0
        last_time = 0.0
        area_sum = 0.0
        
        # Server states
        srv1_status = 'idle' # idle, busy
        srv2_status = 'idle'
        srv1_job = None # (arrival_time, s1, s2)
        srv2_job = None # (arrival_time, s2)
        
        busy1_accum = 0.0
        busy2_accum = 0.0
        
        q1 = []
        q2 = []
        
        w_sum = 0.0
        dep_count_window = 0
        arr_count_window = 0
        wait_count_window = 0
        
        # Helper to flush time
        def flush_time(now):
            nonlocal area_sum, busy1_accum, busy2_accum, last_time
            dt = now - last_time
            if dt > 0:
                area_sum += current_count * dt
                if srv1_status == 'busy':
                    busy1_accum += dt
                if srv2_status == 'busy':
                    busy2_accum += dt
            last_time = now

        while events_heap:
            time, etype, data = heapq.heappop(events_heap)
            
            if time > total_time:
                break
                
            flush_time(time)
            
            if etype == 'arr':
                s1, s2 = data
                arrival_t = time
                
                # Check if within window for stats
                in_window = (arrival_t >= warmup_end)
                
                if in_window:
                    arr_count_window += 1
                
                # Add to system
                current_count += 1
                
                # Try to start service 1
                if srv1_status == 'idle':
                    srv1_status = 'busy'
                    srv1_job = (arrival_t, s1, s2)
                    end_t = time + s1
                    heapq.heappush(events_heap, (end_t, 'dep1', (arrival_t, s2)))
                    if in_window:
                        wait_count_window += 0 # No wait
                else:
                    q1.append((arrival_t, s1, s2))
                    if in_window:
                        wait_count_window += 1 # Waited
                        
            elif etype == 'dep1':
                arrival_t, s2 = data
                # Job leaves stage 1
                srv1_status = 'idle'
                srv1_job = None
                
                # Start next from q1 if available
                if q1:
                    next_job = q1.pop(0)
                    n_arr, n_s1, n_s2 = next_job
                    srv1_status = 'busy'
                    srv1_job = (n_arr, n_s1, n_s2)
                    end_t = time + n_s1
                    heapq.heappush(events_heap, (end_t, 'dep1', (n_arr, n_s2)))
                
                # Move to stage 2
                # Try to start service 2
                if srv2_status == 'idle':
                    srv2_status = 'busy'
                    srv2_job = (arrival_t, s2)
                    end_t = time + s2
                    heapq.heappush(events_heap, (end_t, 'dep2', arrival_t))
                else:
                    q2.append((arrival_t, s2))
                    
            elif etype == 'dep2':
                arrival_t = data
                # Job leaves system
                srv2_status = 'idle'
                srv2_job = None
                
                # Start next from q2 if available
                if q2:
                    next_job = q2.pop(0)
                    n_arr, n_s2 = next_job
                    srv2_status = 'busy'
                    srv2_job = (n_arr, n_s2)
                    end_t = time + n_s2
                    heapq.heappush(events_heap, (end_t, 'dep2', n_arr))
                
                # Remove from system
                current_count -= 1
                
                # Stats for W
                if time >= warmup_end:
                    sojourn = time - arrival_t
                    w_sum += sojourn
                    dep_count_window += 1
                    
        # Final flush
        flush_time(total_time)
        
        # Calculate metrics for this seed
        # L = Area / Window Length
        if window_len > 0:
            L_est = area_sum / window_len
        else:
            L_est = 0.0
            
        # W = Sum(Sojourn) / Count(Departures in window)
        if dep_count_window > 0:
            W_est = w_sum / dep_count_window
        else:
            W_est = 0.0
            
        # Busy Frac
        bf1 = busy1_accum / total_time if total_time > 0 else 0
        bf2 = busy2_accum / total_time if total_time > 0 else 0
        # Average busy frac of system? Or max? Usually utilization of bottleneck or average.
        # Let's report average of both servers? Or just one?
        # "busy_frac" usually implies overall system utilization or specific server.
        # Given single line JSON, likely average utilization of the two servers.
        avg_busy = (bf1 + bf2) / 2.0
        
        # p_loss: 0 (no blocking/loss modeled)
        p_loss = 0.0
        
        # p_wait: fraction of arrivals in window that waited
        if arr_count_window > 0:
            p_wait = wait_count_window / arr_count_window
        else:
            p_wait = 0.0
            
        results_L.append(L_est)
        results_W.append(W_est)
        results_busy_frac.append(avg_busy)
        results_p_loss.append(p_loss)
        results_p_wait.append(p_wait)
        results_arr.append(arr_count_window)
        results_dep.append(dep_count_window)
        results_blk.append(0)

    # Aggregate across seeds
    if N > 0:
        avg_L = sum(results_L) / N
        avg_W = sum(results_W) / N
        avg_bf = sum(results_busy_frac) / N
        avg_pl = sum(results_p_loss) / N
        avg_pw = sum(results_p_wait) / N
        avg_arr = sum(results_arr) / N
        avg_dep = sum(results_dep) / N
        avg_blk = sum(results_blk) / N
        
        # Effective lambda
        # dep_rate is departures per hour.
        # Total departures in window across seeds / (N * window_len_in_hours)
        # window_len is in minutes.
        win_hours = window_len / 60.0
        if win_hours > 0 and N > 0:
            dep_rate = (avg_dep) / win_hours
        else:
            dep_rate = 0.0
            
        lam_eff = dep_rate # Assuming stable, eff arrival = eff departure
        
    else:
        avg_L = 0.0
        avg_W = 0.0
        avg_bf = 0.0
        avg_pl = 0.0
        avg_pw = 0.0
        avg_arr = 0.0
        avg_dep = 0.0
        avg_blk = 0.0
        dep_rate = 0.0
        lam_eff = 0.0

    output = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": "minute",
        "win": round(window_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_bf, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_pl, 4),
        "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x, 4) for x in results
