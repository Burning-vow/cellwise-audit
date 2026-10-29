import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 6.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean service time 6 min)
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # c is number of servers, but problem says 1 server. 
        # If c_up implies changing capacity? The prompt says "perturbation only changes parameters not structure".
        # For MM/1, c is fixed at 1. Maybe it means something else or just no-op for this specific model if c isn't a param.
        # Let's assume standard MM/1 params are lambda and mu. c=1 is structural.
        # If the prompt implies c can be changed, we'd need M/M/c. But task is mm1-03.
        # I will treat c_up as no-op or perhaps increasing lambda/mu ratio? 
        # Given strict constraints, I'll stick to base params unless specified otherwise.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'minute'
    horizon_min = H
    
    total_L = 0.0
    total_W = 0.0
    total_busy_frac = 0.0
    total_p_wait = 0.0
    total_arr = 0.0
    total_blk = 0.0
    total_dep = 0.0
    total_busy_util = 0.0
    total_busy_occupied = 0.0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_ratio = 0.25
    win_len = horizon_min * (1 - warmup_ratio)
    
    for i in range(N):
        current_seed = S + i
        seed_list.append(current_seed)
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = [] # List of tuples (arrival_time, service_duration)
        num_in_system = 0
        busy_until = 0.0
        
        # Statistics accumulators for this seed
        area_L = 0.0
        last_t = 0.0
        last_num = 0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        wait_times_sum = 0.0
        stay_times_sum = 0.0
        
        # We need to track when customers start waiting vs being served immediately
        # To calculate p_wait: fraction of arrivals that had to wait (queue length > 0 upon arrival)
        # Or fraction of time system has queue? Usually p_wait is probability an arriving customer waits.
        # In discrete event sim, we count arrivals that see queue > 0.
        
        arrivals_that_waited = 0
        
        while t < horizon_min:
            # Determine next event time
            # Events: Arrival, Departure
            
            # Check if there is a pending departure
            if num_in_system > 0:
                # If someone is currently being served, their end time is busy_until
                # If queue exists, next departure is busy_until (if server busy) 
                # Actually, simpler approach: maintain a priority queue of events?
                # Standard MM/1 simulation:
                
                # Next arrival time
                t_arr = next_arrival
                
                # Next departure time
                # If server is idle (num_in_system == 0), no departure.
                # If server is busy, next departure is busy_until.
                # Note: busy_until is updated when service starts.
                
                if num_in_system == 0:
                    t_dep = float('inf')
                else:
                    t_dep = busy_until
                
                t_next = min(t_arr, t_dep)
                
                if t_next >= horizon_min:
                    break
                    
                # Integrate L up to t_next
                dt = t_next - t
                area_L += last_num * dt
                t = t_next
                
                if t_arr <= t_dep:
                    # Arrival
                    arr_count += 1
                    # Service duration drawn now
                    svc_dur = rng.expovariate(mu)
                    
                    # Check if waiting
                    if num_in_system > 0:
                        arrivals_that_waited += 1
                        # Add to queue
                        queue.append((t, svc_dur))
                        num_in_system += 1
                    else:
                        # Start service immediately
                        num_in_system += 1
                        busy_until = t + svc_dur
                        # This customer doesn't wait, so stays in system until busy_until
                        # We need to track individual stay times for W calculation later?
                        # W = Average Stay Time. 
                        # Easier: Sum of stay times of all departed customers / Number of departures.
                        # But we need to know when they depart.
                        # Let's store (arrival_time, service_duration) in a list of active services?
                        # No, standard way:
                        # When a customer arrives and finds server free, they enter service.
                        # Their departure time is known.
                        # When a customer arrives and finds server busy, they join queue.
                        # They don't have a departure time yet.
                        
                        # To compute W accurately via Little's Law or direct sum:
                        # Direct sum requires tracking each customer's exit time.
                        # Let's use a list `active_customers` storing (arrival_time, scheduled_departure_time).
                        # But scheduled_departure_time depends on previous services.
                        
                        # Alternative: Use Little's Law L = lam_eff * W => W = L / lam_eff.
                        # The prompt asks for W. It also asks for L.
                        # Usually in DES, we measure W by averaging (departure_time - arrival_time) for all completed customers in window.
                        # And L by time-average.
                        # Let's implement explicit tracking.
                        
                        # Refactor state:
                        # `server_free_at`: time when server becomes free.
                        # `queue`: list of (arrival_time, service_duration)
                        # `departures_log`: list of (arrival_time, departure_time) for completed customers
                        
                        pass # Logic handled below in restructured loop

                else:
                    # Departure
                    dep_count += 1
                    # Remove one from system
                    num_in_system -= 1
                    
                    # Who departed? The one who started service earliest.
                    # We need to track the specific customer.
                    # Let's restart the logic with a cleaner state machine.
                    break 

        # RESTARTING SIMULATION LOGIC FOR CLARITY AND CORRECTNESS
        
        # Reset variables for this seed
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # State
        # Server status: idle or busy until T
        server_busy_until = 0.0
        # Queue: list of (arrival_time, service_duration)
        q = []
        # Completed customers in window: list of (arrival_time, departure_time)
        # We only care about those whose departure is within [warmup, horizon]
        # But for W, we usually average over all customers who departed in the steady-state window.
        # A customer might arrive before warmup but depart after. Should they be counted?
        # Standard practice: Count customers who DEPART in the measurement window.
        # Their stay time includes time spent before warmup. This is valid for W.
        
        completed_stays = [] # List of stay durations (minutes)
        
        # Metrics accumulation
        area_L = 0.0
        last_t = 0.0
        last_N = 0
        
        arr_total = 0
        dep_total = 0
        blk_total = 0 # Losses (not applicable in infinite buffer MM/1, but keep var)
        wait_total = 0 # Arrivals that waited
        
        warmup_t = horizon_min * warmup_ratio
        
        while True:
            # Determine next event
            t_arr = next_arrival
            t_dep = server_busy_until if len(q) > 0 or server_busy_until > t else float('inf')
            
            # Correction: If server is idle (busy_until <= t) and queue empty, no dep.
            # If server is busy, t_dep is server_busy_until.
            # If queue is not empty, the next departure is still server_busy_until (the current service ending).
            
            if server_busy_until <= t and len(q) == 0:
                t_dep = float('inf')
            else:
                t_dep = server_busy_until
                
            t_next = min(t_arr, t_dep)
            
            if t_next >= horizon_min:
                # Final integration step
                dt = horizon_min - t
                area_L += last_N * dt
                t = horizon_min
                break
            
            # Integrate L
            dt = t_next - t
            area_L += last_N * dt
            t = t_next
            
            if t_arr <= t_dep:
                # Arrival
                arr_total += 1
                svc_dur = rng.expovariate(mu)
                
                # Check if waiting
                # Waiting if server is busy OR queue is non-empty
                # Effectively, if t < server_busy_until (and server was busy) or len(q)>0
                # Simpler: if len(q) > 0 or t < server_busy_until (meaning server occupied)
                # Actually, if server is free (t >= server_busy_until) and q is empty, no wait.
                
                is_waiting = False
                if len(q) > 0:
                    is_waiting = True
                elif t < server_busy_until:
                    is_waiting = True
                
                if is_waiting:
                    wait_total += 1
                    q.append((t, svc_dur))
                    last_N += 1
                else:
                    # Start service immediately
                    server_busy_until = t + svc_dur
                    last_N += 1
                    # Record potential completion? No, record when it actually completes.
                    # We need to associate this arrival with its departure.
                    # Since it starts immediately, its departure is server_busy_until.
                    # We can push a "pending" item to a list of active services?
                    # Or just handle it in the departure branch.
                    # Problem: How do we know which arrival corresponds to the departure?
                    # FIFO.
                    # If we start service immediately, this customer is at head of "service".
                    # If we add to queue, they are behind.
                    
                    # Let's maintain a list `in_service_or_queue`?
                    # Better: Maintain `q` including the one in service?
                    # Common pattern:
                    # `q` holds all customers in system.
                    # First element is in service. Rest are waiting.
                    # `server_busy_until` is derived from first element's remaining time?
                    # No, easier to keep separate.
                    
                    # Let's use a unified list `customers` where index 0 is in service.
                    # But service time is fixed at arrival.
                    
                    # Revised State:
                    # `q`: list of (arrival_time, service_duration)
                    # If `q` is not empty, `q[0]` is in service.
                    # `server_busy_until` should be consistent with `q[0]`.
                    
                    # Let's switch to this model:
                    # On arrival:
                    #   Draw svc_dur.
                    #   Append (t, svc_dur) to `q`.
                    #   If len(q) == 1 (was empty):
                    #       server_busy_until = t + svc_dur
                    #       last_N increases.
                    #   Else:
                    #       last_N increases.
                    #       Wait flag set.
                    
                    # On departure:
                    #   Pop q[0].
                    #   Calculate stay time: t - arrival_time_of_popped.
                    #   If t >= warmup_t: append stay_time to completed_stays.
                    #   If q is not empty:
                    #       new_head = q[0]
                    #       server_busy_until = t + new_head.svc_dur
                    #   Else:
                    #       server_busy_until = inf (idle)
                    #   last_N decreases.
                    
                    # This handles everything uniformly.
                    
                    # Re-implementing loop with this logic...
                    pass 
                
                # Update next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                # Pop from q
                if len(q) > 0:
                    arr_t, svc_d = q.pop(0)
                    stay = t - arr_t
                    if t >= warmup_t:
                        completed_stays.append(stay)
                    dep_total += 1
                    last_N -= 1
                    
                    if len(q) > 0:
                        # Next customer starts service
                        next_arr_t, next_svc_d = q[0]
                        server_busy_until = t + next_svc_d
                    else:
                        server_busy_until = float('inf')
                else:
                    # Should not happen if logic correct
                    pass

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        # Window length for L is win_len
        # L_avg = area_L / horizon_min ? 
        # Prompt: "Statistics accumulated only in window after removing first 25% warmup".
        # So area_L should only accumulate during [warmup_t, horizon_min].
        # My code above accumulates area_L for the whole run.
        # Need to fix integration to only count steady state.
        
        # Recalculating area_L properly:
        # I will re-run the loop logic mentally or adjust code.
        # Adjustment: Only add to area_L if the interval overlaps with [warmup_t, horizon_min].
        # Or simpler: Run full sim, but integrate only when t >= warmup_t.
        
        # Let's rewrite the inner loop part specifically for the final code generation.
        
        # Per-seed results
        # L: Time-average number in system in steady state.
        # W: Average stay time of customers departing in steady state.
        # busy_frac: Fraction of time server is busy in steady state.
        # p_wait: Fraction of arrivals in steady state that waited.
        
        # I need to track:
        # area_L_ss
        # time_busy_ss
        # arr_ss
        # wait_ss
        # dep_ss (for W denominator? No, W uses completed_stays)
        
        # Let's refine the loop implementation in the final code block.
        
        # Placeholder calculations based on the flawed loop above (will fix in final string)
        # For now, assuming the loop structure is corrected in the final output.
        
        # Corrected Loop Structure Plan:
        # 1. Initialize t=0, q=[], server_busy_until=inf, next_arr=rng.expovariate(lam)
        # 2. Variables: area_L_ss=0, time_busy_ss=0, arr_ss=0, wait_ss=0, dep_ss=0, stays_ss=[]
        # 3. While t < H:
        #    a. Find t_next = min(next_arr, server_busy_until)
        #    b. If t_next > H, t_next = H
        #    c. dt = t_next - t
        #    d. If t >= warmup_t:
        #         area_L_ss += len(q) * dt
        #         if server_busy_until > t: time_busy_ss += dt (Careful: if server busy throughout interval)
        #           Actually, check if server is busy during [t, t_next].
        #           Server is busy if t < server_busy_until.
        #           Overlap with [warmup_t, H]:
        #           start_int = max(t, warmup_t)
        #           end_int = min(t_next, H)
        #           if start_int < end_int:
        #               area_L_ss += len(q) * (end_int - start_int)
        #               if server_busy_until > start_int:
        #                   busy_end = min(server_busy_until, end_int)
        #                   time_busy_ss += busy_end - start_int
        #    e. t = t_next
        #    f. Process Event:
        #       If t == next_arr (Arrival):
        #          Draw svc.
        #          Append to q.
        #          If t >= warmup_t:
        #             arr_ss += 1
        #             if len(q) > 1 or (len(q)==1 and t < server_busy_until_before_update?):
        #                Wait condition: Did they wait?
        #                They wait if server was busy when they arrived.
        #                Server busy if t < old_server_busy_until.
        #                If wait: wait_ss += 1
        #          Update server_busy_until if q was empty before adding?
        #             If len(q) == 1 (just added, was empty): server_busy_until = t + svc
