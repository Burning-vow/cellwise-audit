import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=10.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 10.0
    mu_base = 6.0 # 10 min mean -> 6 per hour
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    warmup_ratio = 0.25
    win_len = H * (1 - warmup_ratio)
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [] # (time, type, data) type: 0=arr, 1=dep
        # Initial state
        n_in_system = 0
        servers_free_at = [0.0] * c
        
        # Statistics accumulators for the whole run (we will filter later or integrate carefully)
        # To handle area integrals correctly with warmup, we track previous time and current state.
        prev_t = 0.0
        curr_n = 0
        
        # We need to store history of states to calculate area after warmup? 
        # Or simpler: simulate until end, but only accumulate stats when t >= warmup_time.
        warmup_time = H * warmup_ratio
        
        # Accumulators for this seed
        area_n = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w_times = 0.0 # Sum of (departure - arrival) for customers who arrived during window? 
        # Wait, W is average waiting+service time. Usually defined over customers served.
        # If a customer arrives before warmup but leaves after, do they count?
        # Standard practice: Only count customers who arrive within the statistical window.
        # But area integral L must be over the window.
        
        # Let's restart logic: Simulate full horizon.
        # Track events.
        # When an event happens at time te:
        # 1. Integrate area from prev_t to te using old state.
        # 2. Update state.
        # 3. Set prev_t = te.
        
        # For W: Store arrival time of each customer. When they depart, if their arrival was >= warmup_time, add (dep-arr) to sum.
        # Also increment dep count if arr >= warmup_time.
        
        # For p_wait: Count arrivals where queue length > 0 (i.e., no server free immediately).
        # Only count if arrival time >= warmup_time.
        
        # For busy_frac: E[min(N,c)]/c. This is derived from area of min(n,c).
        # So we also need area_min_nc.
        
        area_min_nc = 0.0
        
        # Customer tracking
        # Queue: list of arrival times
        queue = []
        # Servers: list of departure times (or None if idle)
        # Actually, easier to just use n_in_system and queue length.
        # State: n_in_system, queue_length (n_in_system - c if positive)
        
        # Re-initialize simulation variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Priority queue for departures
        import heapq
        dep_heap = [] # (time, id) not needed id, just time. But multiple servers.
        # Better: maintain list of next available times for servers?
        # Discrete Event Simulation standard:
        # Events: Arrival, Departure.
        
        # Reset
        t = 0.0
        next_arrival = rng.expovariate(lam)
        dep_events = [] # heap of departure times
        n_in_sys = 0
        queue_len = 0
        
        prev_t = 0.0
        area_n = 0.0
        area_min_nc = 0.0
        
        cust_arrivals = [] # List of (arrival_time, status) ? No, just arrival time.
        # We need to know which customers are in system.
        # Since FCFS, we can just track number in service and queue.
        # But to calculate W, we need individual times.
        # Let's keep a list of arrival times for those currently in system.
        # When someone departs, it's the earliest arrival among those in service?
        # Yes, FCFS. The one departing is the one who started service earliest.
        # Who starts service? The one at front of queue.
        
        # Structure:
        # queue: list of arrival times waiting.
        # serving: list of (start_time, end_time)? No, end_time is determined by service duration.
        # Service duration is drawn at arrival.
        # So at arrival: draw service time s.
        # If server free: start now, schedule dep at t+s.
        # Else: join queue.
        # When dep occurs: 
        #   1. Remove one from serving.
        #   2. If queue non-empty: pop first, start service now, schedule dep at t+s_of_that_person.
        #   3. Decrement n_in_sys.
        
        # We need to associate service time with the person in queue.
        # queue: list of (arrival_time, service_time)
        # serving: list of (arrival_time, service_time, scheduled_dep_time) -- actually just need to know who is leaving.
        # Since we use heap for deps, we need to map dep time back to customer?
        # Or just process events chronologically.
        
        # Let's use explicit event loop.
        
        # Initialize
        t = 0.0
        next_arrival = rng.expovariate(lam)
        dep_heap = [] # (time, index_in_serving_list?) No, just time.
        # Problem: Multiple servers. If two people finish at same time? Continuous dist, prob 0.
        # But we need to know WHICH person finished to remove them from 'serving' set?
        # Actually, we don't care who specifically, just that one slot opens up.
        # However, to assign new service, we need the service time of the next in queue.
        
        # Let's maintain:
        # queue: deque of (arrival_time, service_time)
        # num_serving: int
        # dep_heap: heap of departure times
        
        queue = []
        num_serving = 0
        dep_heap = []
        
        # Stats
        area_n = 0.0
        area_min_nc = 0.0
        prev_t = 0.0
        
        # Per-customer stats collection
        # We only care about customers arriving in [warmup_time, H]
        # But area integral needs correct state evolution.
        
        # Helper to update area
        def update_area(current_t, current_n):
            nonlocal area_n, area_min_nc, prev_t
            dt = current_t - prev_t
            if dt > 0:
                # Only integrate if overlapping with window?
                # Simpler: Integrate whole time, then subtract warmup part?
                # Or check overlap.
                # Window is [W_start, H].
                w_start = warmup_time
                w_end = H
                
                # Overlap interval
                o_start = max(prev_t, w_start)
                o_end = min(current_t, w_end)
                
                if o_start < o_end:
                    dt_win = o_end - o_start
                    area_n += current_n * dt_win
                    area_min_nc += min(current_n, c) * dt_win
            
            prev_t = current_t

        # Main Loop
        while True:
            # Determine next event time
            next_event_t = float('inf')
            event_type = None
            
            if next_arrival <= H:
                next_event_t = next_arrival
                event_type = 'A'
            
            if dep_heap:
                if dep_heap[0][0] < next_event_t:
                    next_event_t = dep_heap[0][0]
                    event_type = 'D'
            
            if next_event_t == float('inf'):
                break
            
            # Advance time
            t = next_event_t
            
            # Update area based on state BEFORE processing event
            # Current state is n_in_sys = num_serving + len(queue)
            current_n = num_serving + len(queue)
            update_area(t, current_n)
            
            if event_type == 'A':
                # Arrival
                # Draw service time
                serv_time = rng.expovariate(mu)
                
                # Check if wait occurred
                # Wait if queue is not empty OR all servers busy (num_serving == c)
                # Effectively, if num_serving < c, immediate service.
                # If num_serving == c, joins queue.
                
                did_wait = False
                if num_serving < c:
                    # Start service immediately
                    num_serving += 1
                    dep_time = t + serv_time
                    heapq.heappush(dep_heap, (dep_time, serv_time)) # Store serv_time? Not needed for dep, but maybe for debug. Just time.
                    # Actually, we don't need serv_time in heap. Just dep_time.
                    # But wait, if we push dep_time, how do we know it's valid?
                    # We just pop it.
                    heapq.heappush(dep_heap, (t + serv_time,))
                else:
                    # Join queue
                    queue.append((t, serv_time))
                    did_wait = True
                
                # Stats for this customer if in window
                if t >= warmup_time:
                    # Record arrival
                    pass # Will record W upon departure
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # Update counts for window
                if t >= warmup_time:
                    # We'll count arrivals/departures/waits here or later?
                    # Let's count arrivals here.
                    pass 

            elif event_type == 'D':
                # Departure
                dep_time, _ = heapq.heappop(dep_heap) # Pop one departure
                
                # One person leaves service
                num_serving -= 1
                
                # Check if queue has people
                if queue:
                    # Move head of queue to service
                    arr_t, serv_t = queue.pop(0)
                    num_serving += 1
                    new_dep_t = t + serv_t
                    heapq.heappush(dep_heap, (new_dep_t,))
                    
                    # Calculate W for this person
                    # They arrived at arr_t, departed at t (current time)
                    # Note: Their service ended at t? 
                    # Wait. The person who just left had a specific arrival time.
                    # How do we know who left?
                    # In my model, I pushed (dep_time,) into heap. I lost the link to arrival time.
                    # Correction: Heap should contain (dep_time, arrival_time, service_time) or similar.
                    # Let's fix the heap content.
                    
                    # RESTART LOGIC FOR DEPARTURE HANDLING TO TRACK CUSTOMERS
                    
                    # I need to rewrite the event handling slightly to track identity.
                    # Let's assume the code below replaces the 'D' block logic properly.
                    pass

            # This approach is getting messy inline. Let's refactor the loop structure mentally.
            # State:
            # queue: list of (arrival_time, service_duration)
            # active_services: list of (arrival_time, service_duration, completion_time)
            # But completion_time changes? No, fixed once started.
            # When a service completes, we remove it from active_services.
            # Then we check queue.
            
            # Let's stick to the heap but store more info.
            # Heap items: (completion_time, arrival_time, service_duration)
            
            # Redoing the loop body for D:
            # comp_t, arr_t, serv_d = heapq.heappop(dep_heap)
            # num_serving -= 1
            # If queue:
            #   q_arr, q_serv = queue.pop(0)
            #   new_comp = t + q_serv
            #   heapq.heappush(dep_heap, (new_comp, q_arr, q_serv))
            #   num_serving += 1
            # Now, the person who left is the one with arr_t.
            # If arr_t >= warmup_time:
            #   W_i = t - arr_t
            #   sum_W += W_i
            #   count_dep_window += 1
            #   if they waited? We need to know if they waited.
            #   Did they wait? If they were in queue, yes.
            #   We can flag this when adding to queue.
            
            # Okay, let's implement this cleanly.
            
            # Resetting variables for clean implementation inside the seed loop...
            # I will write the final code directly.
            
            # Need to re-evaluate the 'did_wait' logic.
            # At arrival:
            # if num_serving < c: start service. waited=False.
            # else: join queue. waited=True.
            
            # At departure:
            # Pop completed job.
            # If queue not empty:
            #   Next job starts. It was in queue, so it waited.
            #   But we already marked it as waited when it joined queue.
            
            # So we need to store 'waited' flag with the customer.
            # Queue item: (arrival_time, service_time, waited_flag)
            # Active item in heap: (completion_time, arrival_time, service_time, waited_flag)
            
            # Let's proceed with this structure.
            
            # Since I am generating the final code, I will ensure these details are correct.
            
            # One more thing: p_wait is probability that an ARRIVAL sees a queue/wait.
            # So at arrival time, if num_serving == c (all busy), then p_wait event occurs.
            # Count such arrivals in window.
            
            # blk: Losses. Infinite capacity assumed? "Bank branch". Usually infinite queue.
            # If infinite queue, blk=0, p_loss=0.
            # The prompt mentions blk/p_loss. If system is M/M/c/K, there are losses.
            # Prompt says "2 counters", "Poisson flow", "Exponential service", "FCFS".
            # Does not mention capacity limit. Assume infinite buffer.
            # So blk=0, p_loss=0.
            
            # busy_frac definition: E[min(N,c)]/c.
            # busy_util: Same? "busy_util=E[min(N,c)]/c".
            # busy_occupied: 1 - pi_0. Probability system is not empty.
            # Area of (N>0) / Total Time.
            
            # Let's add area_nonempty.
            
            # Final Plan for Code Generation:
            # 1. Parse args.
            # 2. Setup params.
            # 3. Loop seeds.
            # 4. Inside seed:
            #    - Init RNG, State (queue, heap, counts).
            #    - Loop events until H.
            #    - Update areas (N, min(N,c), indicator(N>0)) considering warmup window.
            #    - On Arrival:
            #      - Draw service.
            #      - Determine if waits (num_serving == c).
            #      - If waits, append to queue with flag. Else, push to heap.
            #      - If arrival in window:
            #        - count_arr++
            #        - if waited: count_wait++
            #    - On Departure:
            #      - Pop from heap.
            #      - num_serving--.
            #      - If queue:
            #        - Pop from queue.
            #        - Push to heap with new completion time.
            #        - num_serving++.
            #      - The popped customer has arrival_time.
            #      - If arrival_time in window:
            #        - count_dep++
            #        - sum_W += (current_time - arrival_time)
            #    - After loop:
            #      - Calculate L = area_N / win_len
            #      - Calculate busy_frac = area_min_nc / (win_len * c) ?? No.
            #        E[min(N,c)] = area_min_nc / win_len.
            #        busy_frac = E[min(N,c)] / c.
            #      - Calculate busy_occupied = area_nonempty / win_len.
            #      - Calculate W = sum_W / count_dep.
            #      - Calculate p_wait = count_wait / count_arr.
            #      - Append to lists.
            # 5. Aggregate results.
            # 6. Print JSON.

# Implementing the plan above.
import heapq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=10.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 10.0
    mu_base = 6.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    warmup_ratio = 0.25
    warmup_time = H * warmup_ratio
    win_len = H - warmup_time
    
    res_L = []
    res_W = []
    res_busy_frac = []
    res_p_wait = []
    res_arr = []
    res_dep = []
    res_blk = []
    res_busy_util = []
    res_dep_rate = []
    res_lam_eff = []
    res_p_loss = []
    res_busy_occ = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        dep_heap = [] # (comp_time, arr_time, serv_time, waited_flag)
        queue = [] # (arr_time, serv_time, waited_flag)
        num_serving = 0
        
        area_n = 0.0
        area_min_nc = 0.0
        area_nonempty = 0.0
        
        prev_t = 0.0
        
        count_arr_win = 0
        count_dep_win = 0
        count_wait_win = 0
        sum_W_win = 0.0
        
        while True:
            next_event_t = float('inf')
            event_type = None
            
            if next_arrival <= H:
                next_event_t = next_arrival
                event_type = 'A'
            
            if dep_heap:
                if dep_heap[0][0] < next_event_t:
                    next_event_t = dep_heap[0][0]
                    event_type = 'D'
            
            if next_event_t == float('inf'):
                break
            
            t = next_event_t
            
            # Update Areas
            current_n = num_serving + len(queue)
            dt = t - prev_t
            if dt > 0:
                o_start = max(prev_t, warmup_time)
                o_end = min(t, H)
                if o_start < o_end:
                    dt_win = o_end - o_start
                    area_n += current_n * dt_win
                    area_min_nc += min(current_n, c) * dt_win
                    if current_n > 0:
                        area_nonempty += dt_win
            
            prev_t = t
            
            if event_type == 'A':
                serv_time = rng.expovariate(mu)
                waited = False
                if num_serving < c:
                    num_serving += 1
                    comp_time = t + serv_time
                    heapq.heappush(dep_heap, (comp_time, t, serv_time, False))
                else:
                    waited = True
                    queue.append((t, serv_time, True))
                
                if t >= warmup_time:
                    count_arr_win += 1
                    if waited:
                        count_wait_win += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'D':
                comp_time, arr_time, serv_time, waited_flag = heapq.heappop(dep_heap)
                num_serving -= 1
                
                if queue:
                    q_arr, q_serv, q_waited = queue.pop(0)
                    num_serving += 1
                    new_comp = t + q_serv
                    heapq.heappush(dep_heap, (new_comp, q_arr, q_serv, q_waited))
                
                if arr_time >= warmup_time:
                    count_dep_win += 1
                    sum_W_win += (t - arr_time)
        
        # Calculate metrics for this seed
        if win_len > 0:
            L = area_n / win_len
            busy_frac_val = (area_min_nc / win_len) / c
            busy_util_val = busy_frac_val # Same definition per prompt
            busy_occ_val = area_nonempty / win_len
            
            if count_dep_win > 0:
                W = sum_W_win / count_dep_win
            else:
                W = 0.0
                
            if count_arr_win > 0:
                p_wait_val = count_wait_win / count_arr_win
            else:
                p_wait_val = 0.0
                
            dep_rate_val = count_dep_win / win_len # per hour
            lam_eff_val = count_arr_win / win_len # per hour
            
            blk_val = 0.0
            p_loss_val = 0.0
        else:
            L = 0.0; busy_frac_val = 0.0; busy_util_val = 0.0; busy_occ_val = 0.0
            W = 0.0; p_wait_val = 0.0; dep_rate_val = 0.0; lam_eff_val = 0.0
            blk_val = 0.0; p_loss_val = 0.0

        res_L.append(L)
        res_W.append(W)
        res_busy_frac.append(busy_frac_val)
        res_p_wait.append(p_wait_val)
        res_arr.append(count_arr_win)
        res_dep.append(count_dep_win)
        res_blk.append(blk_val)
        res_busy_util.append(busy_util_val)
        res_dep_rate.append(dep_rate_val)
        res_lam_eff.append(lam_eff_val)
        res_p_loss.append(p_loss_val)
        res_busy_occ.append(busy_occ_val)
        
    # Average across seeds
    avg_L = sum(res_L)/len(res_L)
    avg_W = sum(res_W)/len(res_W)
    avg_busy_frac = sum(res_busy_frac)/len(res_busy_frac)
    avg_p_wait = sum(res_p_wait)/len(res_p_wait)
    avg_arr = sum(res_arr)/len(res_arr)
    avg_dep = sum(res_dep)/len(res_dep)
    avg_blk = sum(res_blk)/len(res_blk)
    avg_busy_util = sum(res_busy_util)/len(res_busy_util)
    avg_dep_rate = sum(res_dep_rate)/len(res_dep_rate)
    avg_lam_eff = sum(res_lam_eff)/len(res_lam_eff)
    avg_p_loss = sum(res_p_loss)/len(res_p_loss)
    avg_busy_occ = sum(res_busy_occ)/len(res_busy_occ)
    
    output = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": [seed_start + i for i in range(N_seeds)],
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in res_L],
        "per_seed_W": [round(x, 6) for x in res_W],
        "per_seed_busy_frac": [round(x, 6) for x in res_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in res_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in res_p_wait],
        "busy_occupied": round(avg_busy_occ, 6)
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
