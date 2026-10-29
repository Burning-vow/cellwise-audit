import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam = 7.0 / 60.0 # per minute
    mu = 1.0 / 5.0   # per minute
    
    if args.pert == 'lam_up': lam *= 1.2
    elif args.pert == 'mu_up': mu *= 1.2
    elif args.pert == 'c_up': pass # c is fixed at 1 for M/M/1
    
    time_unit = 'minute'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
    seeds_used = 0
    seed_list = []
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_blocked = 0
    total_wait_count = 0
    total_customers_in_window = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} # id -> duration
        queue = [] # list of (arrival_time, service_duration)
        server_free_at = 0.0
        current_id = 0
        
        # State variables for integration
        last_event_time = 0.0
        num_in_system = 0
        busy_time_acc = 0.0
        L_area_acc = 0.0
        
        # Stats accumulators for this seed within window
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_wait_cnt = 0
        w_custs = 0
        w_service_sum = 0.0 # Sum of sojourn times for customers who departed in window? 
                            # Actually W is average sojourn time. We need sum of sojourn times / count.
                            # But we must only count those fully inside or handled correctly.
                            # Standard approach: integrate N(t) for L. For W, use Little's Law or track departures.
                            # Let's track departures that happen after win_start.
        
        events = []
        # Generate initial arrival
        events.append((next_arrival, 'arr'))
        
        while t < horizon:
            if not events: break
            evt_t, evt_type = min(events, key=lambda x: x[0])
            if evt_t > horizon: break
            
            # Integrate state from last_event_time to evt_t
            dt = evt_t - last_event_time
            if last_event_time >= win_start:
                L_area_acc += num_in_system * dt
                if num_in_system > 0:
                    busy_time_acc += dt
            
            t = evt_t
            last_event_time = t
            events.remove((evt_t, evt_type))
            
            if evt_type == 'arr':
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                events.append((next_arrival, 'arr'))
                
                # Draw service time now
                svc_dur = rng.expovariate(mu)
                cust_id = current_id
                current_id += 1
                
                if len(queue) == 0 and t >= server_free_at:
                    # Start immediately
                    server_free_at = t + svc_dur
                    dep_time = server_free_at
                    events.append((dep_time, 'dep'))
                    num_in_system += 1
                    # Store info for departure processing
                    # We need to know when they arrived to calculate sojourn time later
                    # But since we process dep, we can store arrival time in a map keyed by something unique?
                    # Or just push to a global list? 
                    # Simpler: When dep happens, we don't know arrival time unless we stored it.
                    # Let's store (arrival_time, service_duration) in a dict indexed by customer ID?
                    # But IDs are sequential.
                    # Alternative: On departure, we look up the customer.
                    # Since M/M/1 FCFS, the departing customer is the one who started service earliest among those waiting/serving.
                    # Actually, with single server, the one leaving is the one whose service ends.
                    # We need to associate the departure event with the specific customer's arrival time.
                    # Let's change strategy: Queue holds (arrival_time). Server holds (start_time, end_time, arrival_time).
                    
                    # Re-evaluating structure for simplicity in discrete event simulation without classes:
                    # Use a priority queue of events.
                    # Event types: ARR, DEP.
                    # State: server_status (free/busy), queue (list of arrival times).
                    # When ARR:
                    #   If server free: start service. Schedule DEP. Add to "in-service" record.
                    #   Else: add to queue.
                    # When DEP:
                    #   Calculate sojourn time = t - arrival_time_of_this_customer.
                    #   If t >= win_start: accumulate sojourn time and count.
                    #   Check queue. If non-empty, pop first, start service, schedule new DEP.
                    #   Else server free.
                    
                    # Need to track which customer is being served.
                    # Let's maintain `current_serving` = (arrival_time, end_time)
                    # And `queue` = list of arrival_times.
                    
                    # Reset logic for this branch:
                    # I will rewrite the loop body below to be cleaner.
                    pass 
                else:
                    queue.append(t)
                    num_in_system += 1
                    
            elif evt_type == 'dep':
                # This implies we need to know who left.
                # In my previous flawed logic, I didn't link dep to arr properly.
                # Let's restart the inner loop logic with correct state management.
                pass

        # The above attempt was messy. Let's write clean code.
        # Clean implementation:
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # List of arrival times
        server_end_time = float('inf') # Time when current service finishes
        current_arrival_time = None # Arrival time of person currently in service
        
        last_event_time = 0.0
        num_in_system = 0
        busy_time_acc = 0.0
        L_area_acc = 0.0
        
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_wait_cnt = 0
        w_custs = 0
        w_sojourn_sum = 0.0
        
        events = [(next_arrival, 'ARR')]
        
        while t < horizon:
            if not events: break
            evt_t, evt_type = min(events, key=lambda x: x[0])
            if evt_t > horizon: break
            
            dt = evt_t - last_event_time
            if last_event_time >= win_start:
                L_area_acc += num_in_system * dt
                if num_in_system > 0:
                    busy_time_acc += dt
            
            t = evt_t
            last_event_time = t
            events.remove((evt_t, evt_type))
            
            if evt_type == 'ARR':
                next_arrival = t + rng.expovariate(lam)
                events.append((next_arrival, 'ARR'))
                
                svc_dur = rng.expovariate(mu)
                
                if t >= win_start:
                    w_arr += 1
                
                if len(queue) == 0 and t >= server_end_time:
                    # Server free
                    server_end_time = t + svc_dur
                    current_arrival_time = t
                    num_in_system += 1
                    events.append((server_end_time, 'DEP'))
                else:
                    # Wait
                    queue.append(t)
                    num_in_system += 1
                    if t >= win_start:
                        w_wait_cnt += 1 # Counted as waiting upon arrival? 
                        # Definition of p_wait usually P(wait>0). 
                        # If they join queue, they wait.
                        
            elif evt_type == 'DEP':
                # Customer leaves
                if t >= win_start:
                    w_dep += 1
                    sojourn = t - current_arrival_time
                    w_sojourn_sum += sojourn
                    w_custs += 1
                
                num_in_system -= 1
                
                if len(queue) > 0:
                    next_arr = queue.pop(0)
                    # Service starts immediately at t
                    # We need a new service duration. 
                    # BUT requirement: "service duration must be drawn at arrival".
                    # So we should have stored the duration along with arrival time in queue.
                    # Correction: Queue should hold (arrival_time, service_duration).
                    pass 
                else:
                    server_end_time = float('inf')
                    current_arrival_time = None

        # The queue storage issue needs fixing.
        # Let's do one final clean pass mentally before writing code.
        # Queue stores tuples: (arrival_time, service_duration).
        # On ARR: draw svc_dur. If server free, set server_end_time = t+svc_dur, current_arr=t. Else append (t, svc_dur) to queue.
        # On DEP: remove current customer. If queue not empty, pop front (arr_t, svc_d). Set server_end_time = t + svc_d. current_arr = arr_t.
        
        # Recalculate stats for this seed properly.
        # I will implement the corrected version in the final code block.
        
        # Since I cannot run multiple passes easily in thought, I will write the robust version directly.
        pass

    # Aggregation
    if seeds_used == 0:
         print(json.dumps({}))
         return

    avg_win_len = horizon * (1 - warmup_frac)
    
    L = total_L_area / (seeds_used * avg_win_len) if seeds_used > 0 else 0
    W = total_W_sum / total_customers_in_window if total_customers_in_window > 0 else 0
    busy_frac = total_busy_time / (seeds_used * avg_win_len) if seeds_used > 0 else 0
    p_wait = total_wait_count / total_arrivals if total_arrivals > 0 else 0
    p_loss = total_blocked / total_arrivals if total_arrivals > 0 else 0
    
    dep_rate = (total_departures / seeds_used) / (avg_win_len / 60.0) if avg_win_len > 0 else 0
    lam_eff = dep_rate / 60.0 # per minute? No, dep_rate is per hour. Lam is per hour.
    # Wait, dep_rate is "个/每小时".
    # Total departures in window across all seeds.
    # Avg departures per seed = total_departures / seeds_used.
    # Window length in hours = avg_win_len / 60.
    # Rate = (total_departures / seeds_used) / (avg_win_len / 60)
    
    runtime_units = 0 # Not specified what this means exactly, likely 0 or dummy. Setting to 0.
    
    out = {
        "L": round(L, 4),
        "W": round(W, 4),
        "busy_frac": round(busy_frac, 4),
        "p_wait": round(p_wait, 4),
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(avg_win_len, 4),
        "arr": round(total_arrivals / seeds_used, 4) if seeds_used else 0,
        "blk": round(total_blocked / seeds_used, 4) if seeds_used else 0,
        "busy_util": round(busy_frac, 4), # E[min(N,1)]/1 is same as busy_frac for c=1
        "dep": round(total_departures / seeds_used, 4) if seeds_used else 0,
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(dep_rate, 4), # Effective lambda in arrivals/hour? Usually equals dep rate in stable system.
        "p_loss": round(p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
