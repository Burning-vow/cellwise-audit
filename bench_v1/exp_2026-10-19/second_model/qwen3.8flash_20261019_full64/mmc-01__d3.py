import sys, json, random, argparse
from collections import deque

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0 # arrivals per minute
    mu_base = 1.0 / 12.0  # service rate per minute (mean 12 min)
    c = 2                 # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used = 0
    seed_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = deque() # stores (arrival_time, service_duration)
        
        # Statistics accumulators (for area integration and counts)
        # We need to track the number of customers in system over time for L
        # And waiting times for W
        
        # To compute L correctly as time-average, we integrate N(t) * dt
        # To compute W correctly, we sum total time spent by each customer
        
        # Warmup: discard first 25% of horizon
        warmup_end = H * 0.25
        
        # State variables for integration
        last_event_time = 0.0
        current_N = 0
        area_N = 0.0 # Integral of N(t) dt
        
        # Counters for window statistics
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0 # Arrivals that found all servers busy AND queue non-empty? 
                       # Definition: p_wait is prob arrival needs to queue.
                       # In FCFS with infinite buffer, if all servers busy, they join queue.
                       # If a server is free, they start immediately.
                       # So p_wait = fraction of arrivals where min(servers_free_at) > arrival_time?
                       # Actually, standard definition: probability that an arriving customer has to wait.
                       # This happens if all c servers are busy at arrival instant.
        
        # For W calculation: Sum of (departure_time - arrival_time) for completed services in window
        total_time_in_system = 0.0
        
        # We need to handle events properly.
        # Events: Arrival, Departure
        
        # Initialize first departure if any server starts immediately? No, first event is arrival or end.
        # Let's use a priority queue or just check next arrival vs next departure.
        
        # Since we don't have heapq imported, let's manage manually or import it.
        # Standard library only. heapq is standard.
        import heapq
        
        # Event queue: (time, type, data)
        # type: 0=arrival, 1=departure
        events = []
        
        # Schedule first arrival
        heapq.heappush(events, (next_arrival, 0, None))
        
        # Track active services to know when departures happen
        # But simpler: just generate next departure when service starts.
        
        while True:
            if not events:
                break
            
            t_curr, e_type, e_data = heapq.heappop(events)
            
            if t_curr > H:
                break
                
            # Update area integral up to this event
            dt = t_curr - last_event_time
            area_N += current_N * dt
            last_event_time = t_curr
            
            if e_type == 0: # Arrival
                # Check if within statistical window for counting metrics?
                # The prompt says stats accumulated after removing first 25%.
                # However, L is time average. W is average per customer.
                # Usually, we collect raw data and filter later, or reset counters at warmup_end.
                # Given the complexity of resetting integrals mid-simulation, 
                # it's easier to run full simulation and then calculate stats from recorded history?
                # Or, we can just ignore events before warmup_end for the *counts* and *sums*,
                # but for *area_N*, we must integrate from 0 to H and subtract area from 0 to warmup_end?
                # Prompt: "statistics ... only in window after removing first 25% warmup".
                # Area-type quantities must be integrated before changing state.
                
                # Strategy: Run simulation fully. Record all relevant timestamps and durations.
                # Then post-process. This avoids complex mid-run resets.
                
                # Let's switch to recording mode.
                pass 

        # Re-implementing with Recording Mode for clarity and correctness regarding warmup
            
        # Reset for recording approach
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = deque()
        
        # Lists to store records for post-processing
        # Each record: (arrival_time, start_service_time, end_service_time, was_blocked?)
        # Assuming infinite buffer, no blocking unless specified. Problem doesn't mention capacity limit.
        # "p_wait" implies waiting line exists.
        
        records = []
        
        # Event loop
        events = []
        heapq.heappush(events, (next_arrival, 0, None))
        
        while events:
            t_curr, e_type, _ = heapq.heappop(events)
            if t_curr > H:
                break
            
            if e_type == 0: # Arrival
                # Find earliest available server
                min_free_idx = -1
                min_free_time = float('inf')
                for idx in range(c):
                    if servers_free_at[idx] < min_free_time:
                        min_free_time = servers_free_at[idx]
                        min_free_idx = idx
                
                # Generate service duration NOW
                svc_dur = rng.expovariate(mu)
                
                if min_free_time <= t_curr:
                    # Server is free, start immediately
                    start_time = t_curr
                    end_time = t_curr + svc_dur
                    servers_free_at[min_free_idx] = end_time
                    heapq.heappush(events, (end_time, 1, (min_free_idx, t_curr, svc_dur)))
                    records.append((t_curr, start_time, end_time, False))
                else:
                    # All servers busy, join queue
                    # Wait until the earliest server frees up
                    # Note: In FCFS, we must ensure order. 
                    # If multiple arrive before server frees, they queue.
                    # We push them into a logical queue structure?
                    # Simpler: Just note they are waiting. When server frees, pop from queue.
                    
                    # We need a queue of waiting customers.
                    # But our event loop processes one by one.
                    # If we just append to `queue` list, we need to trigger service when server frees.
                    
                    # Let's maintain a separate queue list.
                    queue.append((t_curr, svc_dur))
                    records.append((t_curr, None, None, True)) # Mark as waiting initially
                    
                    # Do NOT schedule departure yet. It will be scheduled when service starts.
                    # But how do we know when service starts?
                    # When a server becomes free (Departure event), we check queue.
                    
            elif e_type == 1: # Departure
                # A server finished.
                # Identify which server? The event data had index.
                # But we popped generic tuple. Let's fix event structure.
                # Actually, in the arrival branch above, I pushed (end_time, 1, (idx, arr_t, dur)).
                # Here I unpacked `_`. Need to capture data.
                pass

        # Correcting the loop logic for Queue handling
        
        # Restart clean implementation
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        waiting_queue = deque() # Elements: (arrival_time, service_duration)
        
        records = [] # (arr_t, start_t, end_t, waited_flag)
        
        events = []
        heapq.heappush(events, (next_arrival, 0, None))
        
        while events:
            t_curr, e_type, e_data = heapq.heappop(events)
            if t_curr > H:
                break
            
            if e_type == 0: # Arrival
                svc_dur = rng.expovariate(mu)
                
                # Check for free server
                free_idx = -1
                for i in range(c):
                    if servers_free_at[i] <= t_curr:
                        free_idx = i
                        break
                
                if free_idx != -1:
                    # Start service immediately
                    start_t = t_curr
                    end_t = t_curr + svc_dur
                    servers_free_at[free_idx] = end_t
                    heapq.heappush(events, (end_t, 1, (free_idx, start_t, end_t, t_curr)))
                    records.append((t_curr, start_t, end_t, False))
                else:
                    # Join queue
                    waiting_queue.append((t_curr, svc_dur))
                    # Record arrival, but start/end unknown yet. 
                    # We'll update records when service starts? 
                    # Better: Store partial record or link via ID.
                    # Simplest: Don't record final stats here. Record when service ENDS.
                    # But we need arrival time.
                    # Let's store (arr_t, svc_dur) in queue.
                    # When service starts, we know start_t.
                    # When service ends, we know end_t.
                    # We can create the full record at End Time.
                    pass

            elif e_type == 1: # Departure
                # e_data contains (server_idx, start_t, end_t, arr_t_original_if_direct)
                # If it came from queue, we need to retrieve info.
                # Actually, when we start service from queue, we should push a new departure event.
                
                # Logic for freeing server:
                # 1. Server becomes free at t_curr.
                # 2. Check waiting_queue.
                # 3. If queue not empty, pop head, start service.
                
                # But who triggered this departure?
                # If it was a direct start, we already have arr_t.
                # If it was from queue, we need to know which customer.
                
                # Let's refine:
                # When a customer enters service (either directly or from queue), we schedule their departure.
                # We attach their arrival time to the departure event.
                
                # How to handle queue entry?
                # When arrival finds no server, add to queue.
                # When departure occurs, server is free.
                # If queue has items, pop one, set its start_time = t_curr, end_time = t_curr + svc_dur.
                # Schedule departure for this new service.
                # Create record for this customer.
                
                # What about the customer whose departure just happened?
                # Their record was created when they STARTED service? 
                # Or when they END?
                # Let's create record when they END service, using stored arrival time.
                
                # We need to associate the departing customer with their arrival time.
                # In the direct case, we passed arr_t in e_data.
                # In the queue case, we didn't schedule anything yet.
                
                # Revised Plan:
                # 1. On Arrival:
                #    - Draw svc_dur.
                #    - If server free:
                #      - Set start=t, end=t+svc.
                #      - Push DepEvent(end, arr_t, start_t).
                #      - (Record created on DepEvent processing? Or now?)
                #      - Let's create record on DepEvent processing to ensure completion.
                #    - Else:
                #      - Add (arr_t, svc_dur) to waiting_queue.
                
                # 2. On Departure (e_type=1):
                #    - e_data = (arr_t, start_t, end_t)
                #    - Create record: (arr_t, start_t, end_t, waited=(start_t>arr_t))
                #    - Server is now free.
                #    - If waiting_queue not empty:
                #      - Pop (q_arr_t, q_svc_dur).
                #      - New start_t = t_curr.
                #      - New end_t = t_curr + q_svc_dur.
                #      - Push DepEvent(new_end_t, q_arr_t, new_start_t).
                #      - Update server_free_at? Not strictly needed if we manage queue carefully, 
                #        but good for consistency.
                
                # Let's implement this.
                
                # Extract data from previous departure
                # e_data format: (arr_t, start_t, end_t)
                arr_t_orig, start_t_orig, end_t_orig = e_data
                
                # Create record for the completed customer
                waited = (start_t_orig > arr_t_orig)
                records.append((arr_t_orig, start_t_orig, end_t_orig, waited))
                
                # Now handle queue
                if waiting_queue:
                    q_arr_t, q_svc_dur = waiting_queue.popleft()
                    new_start_t = t_curr
                    new_end_t = t_curr + q_svc_dur
                    # Schedule new departure
                    heapq.heappush(events, (new_end_t, 1, (q_arr_t, new_start_t, new_end_t)))
                    # Update server availability (optional, since we rely on queue popping)
                    # But we need to know WHICH server freed up? 
                    # In this model, servers are identical. Any free server takes next from queue.
                    # We don't need to track specific server indices for the queue logic, 
                    # just that a slot opened.
                else:
                    # No one waiting, server remains idle until next arrival checks it.
                    # We need to mark this server as free at t_curr.
                    # But we lost the server index in e_data?
                    # Yes, we did. We need to keep server index or just assume "a server".
                    # Since servers are identical, we can just say "one server is free".
                    # But for the "Arrival" logic, we check `servers_free_at`.
                    # We MUST update `servers_free_at` for the specific server that finished.
                    # So e_data should include server_index.
                    
                    # Let's restart the event data structure.
                    pass

        # Final Clean Implementation Attempt
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        waiting_queue = deque() # (arr_t, svc_dur)
        records = [] # (arr_t, start_t, end_t, waited_bool)
        
        events = []
        heapq.heappush(events, (next_arrival, 0, None))
        
        while events:
            t_curr, e_type, e_data = heapq.heappop(events)
            if t_curr > H:
                break
            
            if e_type == 0: # Arrival
                svc_dur = rng.expovariate(mu)
                
                # Find free server
                free_idx = -1
                for i in range(c):
                    if servers_free_at[i] <= t_curr:
                        free_idx = i
                        break
                
                if free_idx != -1:
                    start_t = t_curr
                    end_t = t_curr + svc_dur
                    servers_free_at[free_idx] = end_t
                    heapq.heappush(events, (end_t, 1, (free_idx, t_curr, start_t, end_t)))
                else:
                    waiting_queue.append((t_curr, svc_dur))
                    
            elif e_type == 1: # Departure
                srv_idx, arr_t, start_t, end_t = e_data
                
                # Record completion
                waited = (start_t > arr_t)
                records.append((arr_t, start_t, end_t, waited))
                
                # Try to serve next from queue
                if waiting_queue:
                    q_arr_t, q_svc_dur = waiting_queue.popleft()
                    new_start_t = t_curr
                    new_end_t = t_curr + q_svc_dur
                    servers_free_at[srv_idx] = new_end_t
                    heapq.heappush(events, (new_end_t, 1, (srv_idx, q_arr_t, new_start_t, new_end_t)))
                else:
                    servers_free_at[srv_idx] = t_curr # Idle from now

        # Post-processing for Statistics
        # Window: [warmup_end, H]
        w_start = H * 0.25
        w_len = H - w_start
