import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed-start
    pert = args.pert
    
    lam_base = 6.0
    mu_base = 12.0
    c = 1
    K = 6
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
        K = 7
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_time_busy = 0.0
    total_time_area = 0.0
    total_wait_sum = 0.0
    total_served_count = 0
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} 
        queue = [] 
        server_free_time = 0.0 
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        
        last_event_time = 0.0
        area_integral = 0.0
        busy_time_integral = 0.0
        current_N = 0
        
        wait_times = []
        
        while t < H:
            if not queue and (next_arrival >= H or (server_free_time > H and next_arrival > H)):
                break
                
            next_service_end = None
            if queue:
                 # If there are people waiting, the next departure is determined by who is currently being served?
                 # In this simulation model, we track server_free_time.
                 # If server_free_time <= t, server is idle.
                 # If server_free_time > t, server is busy with someone from queue[0] (conceptually).
                 pass
            
            # Determine next event time
            events = []
            if next_arrival < H:
                events.append(('arr', next_arrival))
            
            # Departure logic:
            # We need to know when the current service ends.
            # If queue is not empty, the person at front is being served.
            # But our state representation needs care.
            # Let's use a standard discrete event approach.
            # State: t, queue (list of arrival times), server_status (idle/busy_until)
            
            # Actually, simpler: maintain a priority queue of future events?
            # Or just step through.
            
            # Let's restart the loop structure for clarity within constraints.
            pass

    # Re-implementing the core loop cleanly inside the seed loop
        
    results = {
        "L": 0, "W": 0, "busy_frac": 0, "p_loss": 0, "runtime_units": time_unit,
        "seed_list": [], "seeds_used": 0, "time_unit": time_unit, "win": win,
        "arr": 0, "blk": 0, "busy_util": 0, "dep": 0, "dep_rate": 0, "lam_eff": 0,
        "p_wait": 0, "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [],
        "per_seed_p_loss": [], "per_seed_p_wait": []
    }
    
    all_L = []
    all_W = []
    all_busy = []
    all_loss = []
    all_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_time = []
    all_area = []
    all_wait_sum = []
    all_served = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Queue stores tuples: (arrival_time, service_duration)
        # The first element in queue is currently being served if server is busy
        # But we need to handle the transition carefully.
        # Standard MM1K:
        # Events: Arrival, Departure
        # State: List of customers in system (including one in service).
        # Each customer has an arrival time and a pre-drawn service time.
        
        customers_in_system = [] # List of dicts: {'arr_t': ..., 'svc_t': ...}
        
        # To find next departure, we need to know when the current service finishes.
        # If len(customers_in_system) > 0, the first one is in service.
        # Its finish time is max(t, start_of_service) + svc_t?
        # No, start_of_service is known.
        
        # Let's track:
        # - next_arrival_time
        # - list of customers in system. 
        #   For each customer, we know their arrival time and service duration.
        #   The completion time of the customer at index 0 depends on when they started service.
        #   Customer 0 starts service at max(arrival_time, previous_departure_time).
        
        # Better approach: Maintain a variable `server_next_free_time`.
        # And a queue of waiting customers (arrival times and service durations).
        
        server_next_free_time = 0.0
        waiting_queue = [] # List of (arrival_time, service_duration)
        
        arr_count = 0
        blk_count = 0
        dep_count = 0
        
        # Statistics accumulators for this seed
        area_integral = 0.0 # Integral of N(t) dt
        busy_time_integral = 0.0 # Integral of I(N>0) dt
        wait_sum = 0.0 # Sum of waiting times for those who waited? Or total time in system?
        # W usually means Time in System (Sojourn time) or Waiting Time?
        # Problem says "W (minutes)". Usually Little's Law L = lambda * W uses Sojourn time.
        # Let's assume W is average time in system (sojourn).
        # However, p_wait suggests waiting probability.
        # Let's calculate Sojourn Time for W.
        
        sojourn_sum = 0.0
        served_count = 0
        
        last_event_time = 0.0
        current_N = 0
        
        # Pre-generate service times upon arrival
        
        while True:
            # Determine next event time
            next_arrival_evt = next_arrival if next_arrival < H else float('inf')
            
            # Next departure:
            # If waiting_queue is not empty OR server is busy?
            # Server is busy if server_next_free_time > t AND (waiting_queue was non-empty before or someone is in service)
            # Actually, if waiting_queue is not empty, the head of the queue is in service?
            # No, let's say:
            # If waiting_queue is not empty, the first person is in service.
            # Their finish time is server_next_free_time.
            # If waiting_queue is empty, server is idle.
            
            next_departure_evt = float('inf')
            if waiting_queue:
                next_departure_evt = server_next_free_time
            
            if next_arrival_evt == float('inf') and next_departure_evt == float('inf'):
                break
                
            t_next = min(next_arrival_evt, next_departure_evt)
            
            if t_next > H:
                # Integrate up to H
                dt = H - last_event_time
                area_integral += current_N * dt
                if current_N > 0:
                    busy_time_integral += dt
                break
            
            # Integrate from last_event_time to t_next
            dt = t_next - last_event_time
            area_integral += current_N * dt
            if current_N > 0:
                busy_time_integral += dt
            
            t = t_next
            last_event_time = t
            
            if t == next_arrival_evt:
                # Arrival
                arr_count += 1
                svc_dur = rng.expovariate(mu)
                
                if len(waiting_queue) < K:
                    # Accept
                    waiting_queue.append((t, svc_dur))
                    # Update server_next_free_time
                    # If server was idle (queue was empty before adding?), then service starts now.
                    # But we added to queue.
                    # Logic:
                    # If len(waiting_queue) == 1 (just became non-empty), then this person starts service immediately.
                    # server_next_free_time = max(server_next_free_time, t) + svc_dur
                    # Wait, if server was idle, server_next_free_time should be <= t.
                    
                    if len(waiting_queue) == 1:
                        # Start service immediately
                        server_next_free_time = t + svc_dur
                    else:
                        # Just join queue, no change to server_next_free_time yet
                        pass
                    
                    current_N = len(waiting_queue)
                else:
                    # Blocked
                    blk_count += 1
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif t == next_departure_evt:
                # Departure
                # Remove head of queue
                arr_t, svc_dur = waiting_queue.pop(0)
                dep_count += 1
                served_count += 1
                
                # Calculate sojourn time
                sojourn = t - arr_t
                sojourn_sum += sojourn
                
                # Check if it waited
                # It waited if arr_t < start_of_service_time
                # Start of service time for this person was:
                # If it was the only one in queue when arrived, start = arr_t.
                # Else, start = previous server_next_free_time.
                # This is hard to reconstruct without storing start time.
                # Let's store start time in queue tuple.
                
                # Correction: Store (arrival_time, service_duration, start_time)
                # But we don't know start_time until we pop?
                # When we push, if queue becomes size 1, start_time = arrival_time.
                # If queue size > 1, start_time = unknown (depends on previous departures).
                # Better: When we pop, we know the start time was the previous server_next_free_time BEFORE this service started?
                # No.
                
                # Let's refine the queue item: (arrival_time, service_duration)
                # When a person enters service, we can record their start time.
                # But in this simple loop, we process events sequentially.
                
                # Alternative for W calculation:
                # Average Sojourn Time = Total Area / Total Arrivals? No, that's L.
                # W = L / lambda_eff.
                # We can compute W from L and effective arrival rate.
                # But we also want per-seed W directly?
                # The prompt asks for W. Little's law holds.
                # Let's rely on L and lambda_eff for global W, but for per_seed_W, we can use sum(sojourn)/served.
                # To get sojourn accurately, we need start time.
                
                # Let's modify queue storage to include start time when service begins.
                # But service begins when the person moves from "waiting" to "in service".
                # In our model, the head of the queue IS the one in service.
                # So when we add to queue:
                # If queue was empty, new head starts now.
                # If queue was not empty, new head is behind.
                
                # When we remove head:
                # The next head (if any) starts service NOW.
                # So we need to update the start time of the NEXT head?
                # No, we just need the sojourn of the CURRENT head.
                # Current head's start time:
                # If it was the first in queue when added, start = arrival.
                # Else, start = time when previous head departed.
                
                # Let's store (arrival_time, service_duration, start_time) in queue.
                # When adding:
                # If queue empty: start_time = t.
                # Else: start_time = None (will be set when it becomes head).
                
                # When removing head:
                # If queue not empty after removal:
                # Set start_time of new head to t.
                
                # This requires modifying the tuple in place or using a class/list.
                # Since we can't define classes, we'll use lists for mutable items.
                # Item: [arrival_time, service_duration, start_time]
                
                # Refactoring the arrival/departure logic slightly in my head...
                # I will rewrite the inner loop part in the final code block.
                
                # For now, continuing the draft...
                
                # After popping, check if queue is not empty
                if waiting_queue:
                    # The new head starts service now
                    # Update its start time
                    # But we stored it as a tuple earlier. Need list.
                    pass
                
                # Update server_next_free_time
                # The next service will end at t + next_svc_dur?
                # No, server_next_free_time should be updated to reflect the END of the CURRENT service?
                # We just finished a service.
                # If queue is not empty, the next person starts NOW.
                # Their end time will be t + their_svc_dur.
                # So server_next_free_time = t + waiting_queue[0][1] (service duration)
                # But we need to know their service duration.
                
                # If queue is empty, server is idle.
                # server_next_free_time = t (effectively)
                
                if waiting_queue:
                    # New head starts service
                    # Set start time for new head
                    # And update server_next_free_time
                    new_head = waiting_queue[0]
                    # Assuming new_head is a list [arr_t, svc_t, start_t]
                    new_head[2] = t
                    server_next_free_time = t + new_head[1]
                else:
                    server_next_free_time = t # Idle
                
                current_N = len(waiting_queue)
                
            # Update next_arrival if it was processed
            if t == next_arrival_evt:
                # Already handled above, but ensure next_arrival is advanced
                pass

        # End of seed loop
        
        # Calculate stats for this seed
        # Warmup: discard first 25%
        warmup_time = 0.25 * H
        # We integrated over whole period. Need to re-integrate or subtract?
        # Easier: Run simulation again? No, too slow.
        # Modify integration to ignore warmup.
        # I will adjust the integration logic in the final code to only accumulate after warmup.
        
        # Placeholder calculations assuming correct integration
        L_val = area_integral / H
        busy_frac_val = busy_time_integral / H
        p_loss_val = blk_count / arr_count if arr_count > 0 else 0
        p_wait_val = 0 # Need to count how many waited
        
        # W_val = sojourn_sum / served_count if served_count > 0 else 0
        
        all_L.append(L_val)
        all_busy.append(busy_frac_val)
        all_loss.append(p_loss_val)
        # ...
        
    # Aggregate
    seeds_used = N_seeds
    avg_L = sum(all_L) / seeds_used
    # ...
    
    print(json.dumps(results))

if __name__ == "__main__":
    main()
