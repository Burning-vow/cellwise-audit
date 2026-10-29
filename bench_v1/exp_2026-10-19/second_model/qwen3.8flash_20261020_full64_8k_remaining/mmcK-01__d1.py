import sys, json, random, math
from collections import deque

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if argv[i].startswith('--'):
            key = argv[i][2:]
            val = argv[i+1] if i+1 < len(argv) else None
            args[key] = val
    
    seeds_n = int(args.get('seeds', '5'))
    horizon = float(args.get('horizon', '100.0'))
    seed_start = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    
    # Parameters: Poisson arrival rate lambda (per hour), Service time mu (per hour)
    # Base: lambda=6/hr, mean service=12min=0.2hr -> mu=5/hr
    lam_base = 6.0
    mu_base = 5.0
    c = 2
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_lam_eff = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_runtime_units = 0.0
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        # Simulation state
        t = 0.0
        next_arrival = -rng.expovariate(lam) if lam > 0 else float('inf')
        servers_free_at = [0.0] * c
        queue = deque() # Stores (arrival_time, service_duration)
        n_in_system = 0 # Including those in service and waiting
        
        # Statistics accumulators for warmup removal
        # We need to track events to compute integrals over the window [warmup_end, horizon]
        # Warmup is first 25% of horizon
        warmup_end = 0.25 * horizon
        
        # To correctly integrate L and busy time only after warmup, we can simulate step-by-step
        # but store history or just reset accumulators at warmup_end? 
        # Resetting is tricky because an event might span across warmup boundary.
        # Better approach: Simulate full horizon, record intervals.
        
        # Let's use a simpler discrete-event simulation loop that records state changes.
        # But standard DES with infinite horizon logic is complex for exact area integration post-warmup.
        # Alternative: Run simulation, collect all event times and states. Then filter.
        
        events = [] # List of (time, type, data)
        
        # Initial state
        # We will generate arrivals and departures dynamically.
        
        # For simplicity and correctness regarding "area before change", we maintain running totals
        # but we need to subtract the pre-warmup part.
        # Let's accumulate raw stats and also track when warmup ends.
        
        # Actually, let's just run the sim and keep track of:
        # 1. Total time spent in each state N (for L integral)
        # 2. Total time servers were busy (for busy_frac)
        # 3. Counts of arrivals, blocks, departures, waits
        
        # Since we need to exclude first 25%, we can't just sum everything.
        # Strategy: Simulate until horizon. Keep a list of "state segments".
        # Segment: (start_time, end_time, num_in_system, num_servers_busy)
        
        segments = []
        last_event_time = 0.0
        current_N = 0
        current_busy_servers = 0
        
        # Helper to add segment
        def add_segment(t_start, t_end, n_val, b_val):
            if t_end > t_start:
                segments.append((t_start, t_end, n_val, b_val))
        
        # Initialize first segment placeholder
        # We don't know the first event yet.
        
        # Event loop
        while True:
            # Determine next event time
            min_t = float('inf')
            event_type = None
            
            # Arrival
            if next_arrival < min_t:
                min_t = next_arrival
                event_type = 'arr'
            
            # Departure from any server
            for i in range(c):
                if servers_free_at[i] < min_t:
                    min_t = servers_free_at[i]
                    event_type = 'dep'
                    dep_server_idx = i
            
            if min_t >= horizon:
                break
                
            # Add segment up to this event
            add_segment(last_event_time, min_t, current_N, current_busy_servers)
            last_event_time = min_t
            
            if event_type == 'arr':
                # Process arrival
                if n_in_system < K:
                    # Accept
                    arr_count += 1
                    # Assign to server if free, else queue
                    assigned = False
                    for i in range(c):
                        if servers_free_at[i] <= min_t:
                            # Start service immediately
                            dur = rng.expovariate(mu)
                            servers_free_at[i] = min_t + dur
                            current_busy_servers += 1
                            n_in_system += 1
                            current_N = n_in_system
                            # Store departure info implicitly via servers_free_at
                            # For W calculation, we need to link customer to departure.
                            # This simple model doesn't track individual customers easily for W.
                            # Need to restructure slightly for W.
                            
                            # Let's switch to a more explicit customer tracking for W.
                            pass
                    if not assigned:
                        # Queue
                        dur = rng.expovariate(mu)
                        queue.append((min_t, dur))
                        n_in_system += 1
                        current_N = n_in_system
                        wait_count += 1 # Waited means entered queue
                else:
                    blk_count += 1
                
                # Schedule next arrival
                next_arrival = min_t + rng.expovariate(lam)
                
            elif event_type == 'dep':
                # Server i finishes
                # Check if queue has people
                if queue:
                    arr_time, dur = queue.popleft()
                    # Start service for queued person
                    servers_free_at[dep_server_idx] = min_t + dur
                    # Customer leaves system? No, moves to service.
                    # System count remains same (one left queue, one enters service)
                    # But for L, N is constant.
                    # For W, this customer's service starts now.
                    # We need to calculate W for this customer later.
                    # How to track W? 
                    # When a customer departs the system entirely, we compute their W.
                    
                    # Who departed? The one who was in service on dep_server_idx.
                    # We lost track of their arrival time.
                    # Fix: servers should hold (arrival_time, start_service_time, duration) or similar.
                    # Or simpler: Just track completion times.
                    
                    # Let's restart the design for W accuracy.
                    # State: 
                    #   servers: list of dicts {end_time, arrival_time}
                    #   queue: list of dicts {arrival_time, service_duration}
                    
                    # This requires rewriting the loop structure significantly.
                    # Given constraints, I will implement a cleaner version below.
                    pass
                else:
                    # Server becomes idle
                    servers_free_at[dep_server_idx] = float('inf')
                    current_busy_servers -= 1
                    n_in_system -= 1
                    current_N = n_in_system
                    dep_count += 1
                    # Calculate W for this departing customer
                    # We need their arrival time.
                    # In the previous block, I didn't store it properly.
                    
                    # Let's abort this partial attempt and write the final clean code.
                    break 

        # The above logic is getting messy due to lack of class definitions allowed? 
        # "Do not define classes". I can use tuples/dicts.
        
        # Re-implementing cleanly inside the loop using dictionaries/tuples.
        
        # Reset for actual implementation
        rng = random.Random(current_seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # servers: list of [end_time, arrival_time_of_current_cust]
        # If idle, end_time = inf, arrival_time = None
        servers = [[float('inf'), None] for _ in range(c)]
        # queue: list of [arrival_time, service_duration]
        queue = []
        
        n_sys = 0
        busy_cnt = 0
        
        # Stats
        arr_c = 0
        blk_c = 0
        dep_c = 0
        wait_c = 0 # Customers who waited (entered queue)
        
        # For W accumulation
        w_sum = 0.0
        
        # For Area/L accumulation
        # We need to integrate N(t) and Busy(t) over [warmup_end, horizon]
        # We'll track segments again.
        segs = []
        last_t = 0.0
        cur_n = 0
        cur_b = 0
        
        while True:
            # Find next event
            min_t = float('inf')
            ev_type = None
            ev_idx = -1
            
            if next_arrival < min_t:
                min_t = next_arrival
                ev_type = 'A'
            
            for i in range(c):
                if servers[i][0] < min_t:
                    min_t = servers[i][0]
                    ev_type = 'D'
                    ev_idx = i
                    
            if min_t >= horizon:
                # Final segment
                if horizon > last_t:
                    segs.append((last_t, horizon, cur_n, cur_b))
                break
            
            # Record segment ending at min_t
            if min_t > last_t:
                segs.append((last_t, min_t, cur_n, cur_b))
            last_t = min_t
            
            if ev_type == 'A':
                if n_sys < K:
                    arr_c += 1
                    # Generate service duration
                    dur = rng.expovariate(mu)
                    
                    # Find free server
                    free_idx = -1
                    for i in range(c):
                        if servers[i][0] <= min_t: # Idle
                            free_idx = i
                            break
                    
                    if free_idx != -1:
                        # Start service immediately
                        servers[free_idx] = [min_t + dur, min_t] # EndTime, ArrivalTime
                        busy_cnt += 1
                        cur_b = busy_cnt
                    else:
                        # Join queue
                        queue.append([min_t, dur])
                        wait_c += 1
                        
                    n_sys += 1
                    cur_n = n_sys
                else:
                    blk_c += 1
                
                next_arrival = min_t + rng.expovariate(lam)
                
            elif ev_type == 'D':
                # Server ev_idx completes service
                cust_arr_time = servers[ev_idx][1]
                # Calculate W for this customer
                w = min_t - cust_arr_time
                w_sum += w
                dep_c += 1
                
                # Remove from system
                n_sys -= 1
                cur_n = n_sys
                
                # Check queue
                if queue:
                    # Next customer starts service
                    q_item = queue.pop(0)
                    q_arr_time, q_dur = q_item
                    servers[ev_idx] = [min_t + q_dur, q_arr_time]
                    # Busy count stays same (one finished, one started)
                    # cur_b remains busy_cnt
                else:
                    servers[ev_idx] = [float('inf'), None]
                    busy_cnt -= 1
                    cur_b = busy_cnt

        # Post-process segments for statistics within [warmup_end, horizon]
        win_len = horizon - warmup_end
        if win_len <= 0:
            win_len = 0.0001 # Avoid div by zero
            
        l_integral = 0.0
        busy_integral = 0.0
        
        for st, en, n_val, b_val in segs:
            # Overlap with [warmup_end, horizon]
            os = max(st, warmup_end)
            oe = min(en, horizon)
            if oe > os:
                dt = oe - os
                l_integral += n_val * dt
                busy_integral += b_val * dt
                
        avg_L = l_integral / win_len
        avg_busy_frac = busy_integral / win_len # Fraction of time station is not empty? 
        # Definition: busy_frac = 1 - pi_0 = P(N>0).
        # My b_val is number of busy servers.
        # Station is not empty if N > 0.
        # I tracked cur_n. So I should integrate (cur_n > 0).
        
        # Recalculate busy_frac based on N>0
        non_empty_integral = 0.0
        for st, en, n_val, b_val in segs:
            os = max(st, warmup_end)
            oe = min(en, horizon)
            if oe > os:
                dt = oe - os
                if n_val > 0:
                    non_empty_integral += dt
        
        p_non_empty = non_empty_integral / win_len
        
        # busy_util = E[min(N,c)]/c
        # Integrate min(n_val, c)
        util_integral = 0.0
        for st, en, n_val, b_val in segs:
            os = max(st, warmup_end)
            oe = min(en, horizon)
            if oe > os:
                dt = oe - os
                util_integral += min(n_val, c) * dt
        busy_util = (util_integral / win_len) / c
        
        # W
        if dep_c > 0:
            avg_W_min = (w_sum / dep_c) * 60.0 # Convert hours to minutes
        else:
            avg_W_min = 0.0
            
        # Probabilities
        total_events = arr_c + blk_c
        p_loss = blk_c / total_events if total_events > 0 else 0.0
        p_wait = wait_c / arr_c if arr_c > 0 else 0.0
        
        # Rates
        dep_rate = dep_c / win_len if win_len > 0 else 0.0 # Per hour
        lam_eff = arr_c / win_len if win_len > 0 else 0.0
        
        # Store per-seed
        per_seed_L.append(avg_L)
        per_seed_W.append(avg_W_min)
        per_seed_busy_frac.append(p_non_empty)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)
        
        all_L.append(avg_L)
        all_W.append(avg_W_min)
        all_busy_frac.append(p_non_empty)
        all_p_loss.append(p_loss)
        all_p_wait.append(p_wait)
        all_arr.append(arr_c)
        all_blk.append(blk_c)
        all_dep.append(dep_c)
        all_busy_util.append(busy_util)
        all_lam_eff.append(lam_eff)
        all_dep_rate.append(dep_rate)
        
        total_runtime_units += horizon

    # Aggregate
    n_seeds = len(per_seed_L)
    if n_seeds == 0:
        print(json.dumps({"error": "no seeds"}))
        return
        
    mean_L = sum(all_L) / n_seeds
    mean_W = sum(all_W) / n_seeds
    mean_busy_frac = sum(all_busy_frac) / n_seeds
    mean_p_loss = sum(all_p_loss) / n_seeds
    mean_p_wait = sum(all_p_wait) / n_seeds
    mean_arr = sum(all_arr) / n_seeds
    mean_blk = sum(all_blk) / n_seeds
    mean_dep = sum(all_dep) / n_seeds
    mean_busy_util = sum(all_busy_util) / n_seeds
    mean_lam_eff = sum(all_lam_eff) / n_seeds
    mean_dep_rate = sum(all_dep_rate) / n_seeds
    
    seed_list = [seed_start + i for i in range(n_seeds)]
    
    result = {
        "L": round(mean_L, 6),
        "W": round(mean_W, 6),
        "busy_frac": round(mean_busy_frac, 6),
        "p_loss": round(mean_p_loss, 6),
        "runtime_units": round(total_runtime_units, 6),
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": time_unit,
        "win": round(horizon - 0.25*horizon, 6),
        "arr": round(mean_arr, 6),
        "blk": round(mean_blk, 6),
        "busy_util": round(mean_busy_util, 6),
        "dep": round(mean_dep, 6),
        "dep_rate": round(mean_dep_rate, 6),
        "lam_eff": round(mean_lam_eff, 6),
        "p_wait": round(mean_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(mean_busy_frac, 6)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
