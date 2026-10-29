import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed-start
    pert = args.pert
    
    # Parameters in hours and minutes
    lam_base = 8.0      # arrivals per hour
    mu_base = 6.0       # services per hour (mean service time 10 min = 1/6 hr)
    c = 3               # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 4
    else:
        lam = lam_base
        mu = mu_base
        
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    
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
    all_busy_occupied = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # State variables
        n_in_system = 0
        n_busy = 0
        queue = [] # list of arrival times or just count? Need to track individual service times drawn at arrival.
                   # Actually, we need to know when each customer finishes.
                   # Let's maintain a list of completion times for busy servers.
                   # And a FIFO queue of customers waiting. Each customer has a service time drawn at arrival.
                   
        # To implement FCFS with pre-drawn service times:
        # We can simulate events. But simple loop over time steps is not efficient for DES.
        # Standard M/M/c simulation:
        # Events: Arrival, Departure.
        # We need to handle the queue properly.
        
        # Let's use an event-driven approach manually.
        # Priority queue of events: (time, type, data)
        # Type 0: Arrival, Type 1: Departure
        
        import heapq
        events = []
        heapq.heappush(events, (next_arrival, 0, None))
        
        # Statistics accumulators for the window [warmup_end, H]
        warmup_end = H * warmup_frac
        
        area_L = 0.0
        area_busy_servers = 0.0 # sum of min(n, c) over time
        area_idle_time = 0.0     # integral of (c - n_busy) ? No, busy_util is E[min(N,c)]/c.
                                 # So we need integral of min(N(t), c).
                                 # busy_occupied = 1 - pi_0. Integral of indicator(N>0).
        
        last_event_time = 0.0
        current_n = 0
        current_min_n_c = 0
        
        # For W calculation: sum of sojourn times of customers who depart within window?
        # Or average over all customers? Usually Little's Law uses steady state.
        # W = L / lambda_eff. But we are asked for direct estimates too.
        # "Average wait+service time W". 
        # If we compute L via area, and lambda_eff via arrivals/departures in window, W = L/lambda_eff.
        # However, the prompt asks for W as a separate stat. It might be better to accumulate sojourn times.
        # But careful with truncation bias.
        # Let's stick to L and lambda_eff to derive W, or accumulate sojourns of completed customers in window.
        # Given "area-type quantities must be integrated before changing state", this hints at using integrals for L.
        # For W, it's often defined as average sojourn time.
        # Let's accumulate sojourn times of customers that DEPART in the window.
        
        total_sojourn_time = 0.0
        count_departures_window = 0
        
        # Tracking for p_wait: probability that an arriving customer finds all servers busy.
        # Count arrivals in window where n >= c.
        count_arrivals_window = 0
        count_wait_arrivals = 0
        
        # Losses: In standard M/M/c/K, K=c means blocked if full. Here infinite queue?
        # "Bank branch... 3 counters". Usually implies infinite queue capacity unless specified.
        # But output requires blk and p_loss. If infinite queue, blk=0, p_loss=0.
        # Let's assume infinite queue capacity (M/M/c). Then blk=0.
        
        # Server completion times
        # We need to know which server becomes free. Since exponential, memoryless, 
        # we can just pick one of the busy servers randomly? 
        # Or simpler: maintain a heap of departure times.
        # When a customer arrives:
        #   Draw service time s ~ Exp(mu).
        #   If n < c: Start service immediately. Push (t+s, id) to dep_heap.
        #   Else: Add to queue. Store s with customer.
        # When a departure occurs:
        #   Pop from dep_heap.
        #   If queue not empty: Dequeue customer, start service. Push new dep time.
        #   Else: n_busy decreases.
        
        # This requires tracking queue elements.
        
        dep_heap = [] # (time, unique_id)
        queue_customers = [] # list of service_times remaining? No, service time is fixed. Just store s.
                             # Wait, if we store s, when they start service, their finish time is t_current + s.
        
        cust_id_counter = 0
        
        while events:
            t_curr, ev_type, _ = heapq.heappop(events)
            
            if t_curr > H:
                break
                
            # Update areas based on time elapsed since last event
            dt = t_curr - last_event_time
            if dt > 0:
                # Only integrate if we are in the window? 
                # The prompt says "statistics only accumulated after removing first 25% warmup".
                # So we check if the interval overlaps with [warmup_end, H].
                
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = min(t_curr, H)
                
                if overlap_start < overlap_end:
                    valid_dt = overlap_end - overlap_start
                    area_L += current_n * valid_dt
                    area_busy_servers += current_min_n_c * valid_dt
                    # For busy_occupied: integral of 1 if current_n > 0 else 0
                    if current_n > 0:
                        area_idle_time += 0 # Not needed directly, but let's track occupied time
                        # Actually let's track area_occupied separately
                        pass 
                    
                    # Let's add another accumulator for occupied time
                    # I'll rename area_idle_time to area_occupied_time logic later.
                    # For now, let's just add a variable.
                    # Re-initializing vars outside loop is better.
                    # Let's move these accumulators out.
            
            # Process Event
            if ev_type == 0: # Arrival
                # Generate next arrival
                inter_arr = rng.expovariate(lam)
                heapq.heappush(events, (t_curr + inter_arr, 0, None))
                
                # Check if in window for stats
                if t_curr >= warmup_end:
                    count_arrivals_window += 1
                    if current_n >= c:
                        count_wait_arrivals += 1
                        
                # Draw service time
                s = rng.expovariate(mu)
                
                if current_n < c:
                    # Start service
                    current_n += 1
                    current_min_n_c = min(current_n, c)
                    heapq.heappush(dep_heap, (t_curr + s, cust_id_counter))
                    cust_id_counter += 1
                else:
                    # Join queue
                    current_n += 1
                    current_min_n_c = min(current_n, c)
                    queue_customers.append((cust_id_counter, s))
                    cust_id_counter += 1
                    
            else: # Departure
                # Find the departing customer
                # Note: dep_heap contains (time, id). 
                # We popped an event from `events` which was a departure? 
                # No, my event structure is mixed. 
                # Let's refine: 
                # Events heap contains both arrivals and departures.
                # When popping a departure event, we need to match it to a specific customer/server.
                # Since we push (t+s, id) to dep_heap, and also push (t+s, 1, id) to events?
                # Simpler: Just use dep_heap for scheduling departures.
                # But we need to process them in chronological order along with arrivals.
                # So, when a service starts, we push (finish_time, 1, id) to `events`.
                # When an arrival happens, we push (arrival_time, 0, None) to `events`.
                
                # So here, ev_type==1 means a customer with ID `data` finished.
                # But I didn't pass data in the tuple above. Let's fix the event pushing.
                
                # Correction in logic flow below.
                pass
            
            # Update last_event_time
            last_event_time = t_curr
            
        # End of simulation for this seed
        
        # Calculate stats for this seed
        if win_len > 0:
            L_est = area_L / win_len
            busy_util_est = area_busy_servers / win_len / c
            # busy_occupied = 1 - pi_0. pi_0 is fraction of time system is empty.
            # area_occupied = integral of 1_{N>0}.
            # I missed accumulating area_occupied. Let's redo the accumulation part mentally.
            # I will rewrite the loop carefully in the final code.
            
            # W estimation:
            # Method 1: Little's Law W = L / lambda_eff.
            # lambda_eff = count_departures_window / win_len? 
            # Or count_arrivals_window / win_len? In steady state they are equal.
            # Using departures is safer for finite horizon if no loss.
            # But if there is loss, effective arrival rate != departure rate.
            # Here no loss.
            # Let's use L / (count_departures_window / win_len).
            
            # Direct W: Sum of sojourn times of those who departed in window / count.
            # This is biased if long jobs cross boundary.
            # Prompt doesn't specify method. "Average wait+service time".
            # Usually in DES, we accumulate sojourn times of completed customers.
            
            # p_wait: count_wait_arrivals / count_arrivals_window
            
            # blk: 0
            # p_loss: 0
            
            # dep_rate: count_departures_window / win_len * 60? No, units.
            # Time unit is Hour. Rate is per Hour.
            # dep_rate = count_departures_window / win_len
            
            # lam_eff = same as dep_rate
            
            # Save per-seed values
            all_L.append(L_est)
            all_busy_util.append(busy_util_est)
            # ... etc
        else:
            # Handle edge case
            pass

    # Aggregate results
    # Mean of per-seed estimates
    
    print(json.dumps({
        "L": sum(all_L)/len(all_L),
        "W": sum(all_W)/len(all_W),
        "busy_frac": sum(all_busy_frac)/len(all_busy_frac),
        "p_wait": sum(all_p_wait)/len(all_p_wait),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "win": win_len,
        "arr": sum(all_arr)/len(all_arr),
        "blk": sum(all_blk)/len(all_blk),
        "busy_util": sum(all_busy_util)/len(all_busy_util),
        "dep": sum(all_dep)/len(all_dep),
        "dep_rate": sum(all_dep_rate)/len(all_dep_rate),
        "lam_eff": sum(all_lam_eff)/len(all_lam_eff),
        "p_loss": sum(all_p_loss)/len(all_p_loss),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }))

if __name__ == "__main__":
    main()
