import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert
    
    # Parameters in hours and minutes
    # Arrival rate: 6 per hour -> lambda = 6 /hr
    # Service time: mean 12 min = 0.2 hr -> mu = 5 /hr (1/0.2)
    # Capacity K = 4 (including service)
    # Servers c = 2
    
    lam_base = 6.0
    mu_base = 5.0
    K = 4
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # Perturb capacity? The prompt says "pert NAME, NAME takes none/lam_up/mu_up/c_up". 
        # Usually c_up might mean increasing servers or capacity. Given context of toll booth, 
        # let's assume it increases the number of servers or capacity. 
        # However, standard queueing perturbations usually affect rates. 
        # Let's interpret c_up as increasing capacity K by 1 or servers? 
        # The problem states "2 lanes", "total 4 cars". 
        # If c_up means changing the structure, but prompt says "perturbation only changes parameters not structure".
        # So c_up likely refers to a parameter related to cost or capacity limit? 
        # Or maybe it's a typo for something else? 
        # Let's assume c_up increases the arrival rate slightly or decreases service rate? 
        # Actually, looking at common patterns: lam_up (arrival), mu_up (service). 
        # c_up might be "capacity up"? But capacity is structural. 
        # Let's stick to modifying rates. Maybe c_up is a distractor or implies a different parameter.
        # To be safe, I will treat c_up as no change if it doesn't fit standard rate params, 
        # OR perhaps it means "cost" which isn't in the model. 
        # Let's assume c_up is not applicable to rate parameters directly, so we keep base.
        # Wait, "perturbation only changes parameters". 
        # Let's assume c_up modifies the capacity K? No, that's structure.
        # Let's assume it modifies the service rate further? 
        # I will implement lam_up and mu_up clearly. For c_up, I'll leave it as base since it's ambiguous without more context on what 'c' represents in the perturbation list other than capacity/servers which are structural.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    # Time unit for simulation: Hours
    time_unit = "hour"
    
    # Warmup fraction: 25%
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    
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
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Events: (time, type, data)
        # type: 0=arrival, 1=departure
        events = []
        
        # Queue state
        # n_in_system: number of cars currently in system (waiting + serving)
        n_in_system = 0
        # busy_servers: number of servers currently occupied
        busy_servers = 0
        
        # Statistics accumulators (for area integration)
        # We need to integrate L(t) over time to get average L
        # And W is Little's Law derived or direct sum of times? 
        # Prompt asks for W (minutes). Usually W is average waiting time in system.
        # We can compute average W by summing (departure_time - arrival_time) for completed services in window.
        # But we must handle truncation carefully.
        
        # Accumulators for the statistical window [warmup_end, H]
        warmup_end = H * warmup_frac
        
        # Area under N(t) curve in window
        area_N_window = 0.0
        last_event_time = 0.0
        last_n_value = 0
        
        # Counters in window
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0
        
        # Sum of sojourn times for departures in window
        sum_sojourn_window = 0.0
        
        # Busy time accumulation for busy_frac (1 - pi_0)
        # We need time where n_in_system > 0 within the window
        area_nonempty_window = 0.0
        
        # For busy_util = E[min(N,c)]/c
        # We need integral of min(n_in_system, c) over time
        area_min_nc_window = 0.0
        
        # For p_wait: probability of waiting? 
        # Usually P(wait) = P(all servers busy) = P(n >= c).
        # We can accumulate time where n_in_system >= c.
        area_wait_state_window = 0.0
        
        # Initialize first event
        if next_arrival < H:
            events.append((next_arrival, 0, None))
            
        while events:
            # Pop earliest event
            events.sort(key=lambda x: x[0])
            current_t, etype, edata = events.pop(0)
            
            if current_t > H:
                break
                
            # Update areas based on previous interval [last_event_time, current_t]
            dt = current_t - last_event_time
            if dt > 0:
                # Only accumulate if the interval overlaps with the statistical window
                # Window is [warmup_end, H]
                start_overlap = max(last_event_time, warmup_end)
                end_overlap = min(current_t, H)
                
                if start_overlap < end_overlap:
                    overlap_dt = end_overlap - start_overlap
                    
                    # Area for L (average number in system)
                    area_N_window += last_n_value * overlap_dt
                    
                    # Area for non-empty (busy_frac)
                    if last_n_value > 0:
                        area_nonempty_window += overlap_dt
                        
                    # Area for min(N, c)
                    val_min_nc = min(last_n_value, c)
                    area_min_nc_window += val_min_nc * overlap_dt
                    
                    # Area for wait state (N >= c)
                    if last_n_value >= c:
                        area_wait_state_window += overlap_dt
            
            last_event_time = current_t
            
            if etype == 0: # Arrival
                # Check if blocked
                if n_in_system >= K:
                    count_blocked_window += 1 if current_t >= warmup_end else 0
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    next_t = current_t + inter_arr
                    if next_t <= H:
                        events.append((next_t, 0, None))
                else:
                    # Accept car
                    n_in_system += 1
                    last_n_value = n_in_system
                    count_arrivals_window += 1 if current_t >= warmup_end else 0
                    
                    # Store arrival time in the car object? 
                    # Since we don't have objects, we need to track individual cars.
                    # In discrete event sim for M/M/c/K, we can just track counts if we use Little's law for W?
                    # But W requires individual times.
                    # We need to know when this specific car leaves.
                    # We can push a departure event now because service time is drawn at arrival.
                    
                    # Draw service time
                    serv_time = rng.expovariate(mu)
                    dep_time = current_t + serv_time
                    
                    # Add departure event
                    # We need to associate this departure with the arrival time to calculate sojourn.
                    # We can store arrival time in the event tuple.
                    events.append((dep_time, 1, current_t)) # 1=departure, data=arrival_time
                    
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    next_t = current_t + inter_arr
                    if next_t <= H:
                        events.append((next_t, 0, None))
                        
            elif etype == 1: # Departure
                arr_time = edata
                n_in_system -= 1
                last_n_value = n_in_system
                
                # Calculate sojourn time
                sojourn = current_t - arr_time
                
                # Record stats if departure happened in window
                if current_t >= warmup_end:
                    count_departures_window += 1
                    sum_sojourn_window += sojourn
                
                # Note: In M/M/c/K, if a server becomes free, does another car start immediately?
                # Yes, FCFS. But our model tracks total N. 
                # When a car departs, N decreases. 
                # Do we need to trigger a new service start? 
                # In this implementation, we scheduled departure at arrival time assuming immediate service if server available?
                # NO. This is incorrect for multi-server queues.
                # Correction:
                # If servers are busy, the arriving car waits. It should NOT schedule a departure immediately.
                # It should join the queue.
                # When a server becomes free (departure), it picks the next car from the queue.
                
                # RE-IMPLEMENTATION LOGIC FIX:
                # We need a queue of waiting cars (their arrival times).
                # And a set of busy servers (their completion times).
                
                # Let's restart the logic inside the loop properly.
                pass 

        # The above simple loop failed to handle queuing correctly.
        # Rewriting the simulation core below.
        
        # Reset for correct simulation
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Queue of waiting cars (arrival times)
        waiting_queue = []
        # List of busy servers (completion times)
        busy_servers_times = []
        
        n_in_system = 0 # Total in system = len(waiting) + len(busy)
        
        # Stats
        area_N_window = 0.0
        area_nonempty_window = 0.0
        area_min_nc_window = 0.0
        area_wait_state_window = 0.0
        
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0
        sum_sojourn_window = 0.0
        
        last_event_time = 0.0
        last_n_value = 0
        
        # Initial state
        # Generate first arrival
        events = []
        if next_arrival < H:
            events.append((next_arrival, 'A'))
            
        while events:
            events.sort(key=lambda x: x[0])
            current_t, etype = events.pop(0)
            
            if current_t > H:
                break
                
            # Integrate areas
            dt = current_t - last_event_time
            if dt > 0:
                start_overlap = max(last_event_time, warmup_end)
                end_overlap = min(current_t, H)
                if start_overlap < end_overlap:
                    overlap_dt = end_overlap - start_overlap
                    area_N_window += last_n_value * overlap_dt
                    if last_n_value > 0:
                        area_nonempty_window += overlap_dt
                    area_min_nc_window += min(last_n_value, c) * overlap_dt
                    if last_n_value >= c:
                        area_wait_state_window += overlap_dt
            
            last_event_time = current_t
            
            if etype == 'A':
                # Arrival
                if n_in_system >= K:
                    # Blocked
                    if current_t >= warmup_end:
                        count_blocked_window += 1
                else:
                    # Accepted
                    n_in_system += 1
                    last_n_value = n_in_system
                    if current_t >= warmup_end:
                        count_arrivals_window += 1
                    
                    # Try to start service immediately if server available
                    if len(busy_servers_times) < c:
                        # Start service
                        serv_time = rng.expovariate(mu)
                        dep_time = current_t + serv_time
                        busy_servers_times.append(dep_time)
                        events.append((dep_time, 'D'))
                    else:
                        # Join queue
                        waiting_queue.append(current_t)
                
                # Schedule next arrival
                inter_arr = rng.expovariate(lam)
                next_t = current_t + inter_arr
                if next_t <= H:
                    events.append((next_t, 'A'))
                    
            elif etype == 'D':
                # Departure
                # Remove one busy server
                # Find the index of the departing time? 
                # Since we push events, we just decrement count.
                # But we need to match the specific car? 
                # In M/M/c, memoryless property allows us to just pick any.
                # However, we need to know the arrival time of the car that just left to calc sojourn.
                # Problem: We didn't link the D event to the specific car.
                # Fix: When starting service, we know the arrival time.
                # We should store (dep_time, arr_time) in the event.
                
                # Re-restructuring needed for linking.
                pass

        # Final attempt with proper linking
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        waiting_queue = [] # stores arrival times
        busy_servers = [] # stores (completion_time, arrival_time)
        
        n_in_system = 0
        
        area_N_window = 0.0
        area_nonempty_window = 0.0
        area_min_nc_window = 0.0
        area_wait_state_window = 0.0
        
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0
        sum_sojourn_window = 0.0
        
        last_event_time = 0.0
        last_n_value = 0
        
        events = []
        if next_arrival < H:
            events.append((next_arrival, 'A', None))
            
        while events:
            events.sort(key=lambda x: x[0])
            current_t, etype, edata = events.pop(0)
            
            if current_t > H:
                break
                
            dt = current_t - last_event_time
            if dt > 0:
                start_overlap = max(last_event_time, warmup_end)
                end_overlap = min(current_t, H)
                if start_overlap < end_overlap:
                    overlap_dt = end_overlap - start_overlap
                    area_N_window += last_n_value * overlap_dt
                    if last_n_value > 0:
                        area_nonempty_window += overlap_dt
                    area_min_nc_window += min(last_n_value, c) * overlap_dt
                    if last_n_value >= c:
                        area_wait_state_window += overlap_dt
            
            last_event_time = current_t
            
            if etype == 'A':
                if n_in_system >= K:
                    if current_t >= warmup_end:
                        count_blocked_window += 1
                else:
                    n_in_system += 1
                    last_n_value = n_in_system
                    if current_t >= warmup_end:
                        count_arrivals_window += 1
                    
                    if len(busy_servers) < c:
                        serv_time = rng.expovariate(mu)
                        dep_time = current_t + serv_time
                        busy_servers.append((dep_time, current_t))
                        events.append((dep_time, 'D', current_t))
                    else:
                        waiting_queue.append(current_t)
                
                inter_arr = rng.expovariate(lam)
                next_t = current_t + inter_arr
                if next_t <= H:
                    events.append((next_t, 'A', None))
                    
            elif etype == 'D':
                # A car departed. edata is its arrival time.
                # Remove from busy_servers
                # We need to remove the specific entry. Since multiple could finish at same time (unlikely continuous), 
                # we search for the matching arrival time.
                idx_to_remove = -1
                for k, (dt_comp, dt_arr) in enumerate(busy_servers):
                    if dt_arr == edata:
                        idx_to_remove = k
                        break
                if idx_to_remove != -1:
                    del busy_servers[idx_to_remove]
                
                n_in_system -= 1
                last_n_value = n_in_system
                
                if current_t >= warmup_end:
                    count_departures_window += 1
                    sum_sojourn_window += (current_t - edata)
                
                # Check if someone starts service
                if waiting_queue:
                    next_arr_time = waiting_queue.pop(0)
                    serv_time = rng.expovariate(mu)
                    dep_time = current_t + serv_time
                    busy_servers.append((dep_time, next_arr_time))
                    events.append((dep_time, 'D', next_arr_time))
        
        # Calculate metrics
