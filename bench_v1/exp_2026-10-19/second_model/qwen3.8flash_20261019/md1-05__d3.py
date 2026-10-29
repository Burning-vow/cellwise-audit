import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0 / 60.0
    mu_base = 1.0 / 6.0
    
    if a.pert == 'lam_up': lam = lam_base * 1.2
    elif a.pert == 'mu_up': mu = mu_base * 1.2
    elif a.pert == 'c_up': c = 2; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base; c = 1
    
    if a.pert != 'c_up': c = 1
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_area = 0.0
    total_wait_area = 0.0
    total_busy_time = 0.0
    
    horizon = a.horizon
    warmup = horizon * 0.25
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        events = []
        queue = []
        service_end_times = []
        n_in_system = 0
        last_event_time = 0.0
        area_n = 0.0
        area_wait = 0.0
        busy_time = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        while t < horizon:
            if not events and next_arr >= horizon:
                break
            
            if events:
                ev_type, ev_t, ev_data = events[0]
                if next_arr < ev_t:
                    t_next = next_arr
                    ev_type = 'arr'
                    ev_data = None
                    events.pop(0) if False else None 
                else:
                    t_next = ev_t
                    events.pop(0)
                    ev_type = ev_type
                    ev_data = ev_data
            else:
                t_next = next_arr
                ev_type = 'arr'
                ev_data = None
            
            dt = t_next - t
            if t >= warmup:
                area_n += n_in_system * dt
                if len(queue) > 0:
                    area_wait += len(queue) * dt
                if n_in_system > 0:
                    busy_time += dt
            
            t = t_next
            
            if ev_type == 'arr':
                arr_count += 1
                if n_in_system < c:
                    n_in_system += 1
                    svc_dur = 6.0
                    end_t = t + svc_dur
                    events.append(('dep', end_t, {'start': t}))
                    import heapq
                    heapq.heappush(events, ('dep', end_t, {'start': t}))
                    events.sort(key=lambda x: x[1])
                else:
                    queue.append({'arrival': t})
                    n_in_system += 1
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                dep_count += 1
                n_in_system -= 1
                if queue:
                    cust = queue.pop(0)
                    wait_time = t - cust['arrival']
                    area_wait += wait_time 
                    # Actually area_wait should be integral of queue length over time.
                    # Let's re-evaluate. The standard way is to accumulate (queue_len * dt).
                    # I did that above. But when a customer leaves the queue and enters service,
                    # they are no longer in the queue. So queue length decreases by 1 immediately?
                    # No, in my logic, n_in_system includes those in service and queue.
                    # When arrival happens and system full, they go to queue. n_in_system increases.
                    # When departure happens, one leaves system. If queue non-empty, head moves to service.
                    # So n_in_system stays same? No.
                    # Let's trace:
                    # Arrive, sys full -> Queue append, n_in_system++.
                    # Departure occurs. One car finishes service.
                    # If queue has people: Pop from queue, start service. n_in_system-- (one left), then ++ (one entered service)?
                    # Or simply: n_in_system represents total cars in facility (service + queue).
                    # On departure: A car leaves the service bay.
                    # If queue is empty: n_in_system--.
                    # If queue is not empty: A car moves from queue to service. n_in_system remains unchanged?
                    # Yes, because one left service, one entered service. Total count constant.
                    # But wait, the departing car is gone. The queued car is now in service.
                    # So n_in_system should decrease by 1 only if queue was empty.
                    # If queue not empty, n_in_system stays same.
                    
                    # Correction on logic:
                    # n_in_system = number of cars in the system (waiting or being served).
                    # Arrival: if space available, enter service. n_in_system++.
                    #           if no space, enter queue. n_in_system++.
                    # Departure: Car finishes service.
                    #            If queue not empty: Next car starts service. n_in_system-- (the one who finished left).
                    #            Wait, the one who finished left. The one from queue entered. Net change 0?
                    #            No. The one who finished is removed from system. The one from queue is still in system.
                    #            So n_in_system decreases by 1.
                    #            BUT, we need to track who is in service vs queue.
                    #            My variable `n_in_system` counts both.
                    #            When a departure event fires, it means a car in service is done.
                    #            We remove that car. n_in_system--.
                    #            Then check queue. If queue not empty, pop one, put into service.
                    #            This new car is already counted in n_in_system?
                    #            Yes, it was added to n_in_system when it arrived and joined queue.
                    #            So moving it from queue to service doesn't change n_in_system.
                    #            So net effect of departure with queue: n_in_system--.
                    #            Net effect of departure without queue: n_in_system--.
                    #            So always n_in_system-- on departure?
                    #            Let's re-read arrival.
                    #            Arrival: n_in_system++.
                    #            Departure: n_in_system--.
                    #            This seems correct for total count.
                    
                    # However, I need to handle the "start service" part correctly.
                    # In my previous code block for 'dep':
                    # I decremented n_in_system.
                    # Then if queue: pop, add new dep event.
                    # This implies the popped car is now in service.
                    # Since it was already in n_in_system (as part of queue), and we just decremented n_in_system for the departing car,
                    # the count is now correct (departing car gone, queued car still there but now in service).
                    
                    # Wait, did I decrement before or after popping?
                    # Code: n_in_system -= 1. Then if queue: pop...
                    # This is correct.
                    
                    # Now about area_wait.
                    # area_wait accumulates len(queue) * dt.
                    # This is the integral of queue length over time.
                    # Little's Law for waiting line: L_q = lambda_eff * W_q.
                    # Here W is total time in system.
                    # The prompt asks for W (total stay time) and L (avg number in system).
                    # L = area_n / win.
                    # W = ?
                    # Usually W = L / lambda_eff.
                    # Or calculate sum of individual times / count.
                    # Sum of individual times = Integral of N(t) dt? No.
                    # Integral of N(t) dt = Sum of (time each car spends in system).
                    # Yes. Because at any time t, N(t) is the number of cars present.
                    # Integrating N(t) over T gives the total person-time units.
                    # Dividing by number of departures (in steady state, arrivals ~ departures) gives average time.
                    # So W = area_n / dep_count (if using all data) or area_n_warmup / dep_count_warmup.
                    
                    # So I don't need separate area_wait for W.
                    # I need area_n for L and W.
                    # I need busy_time for busy_frac.
                    # I need queue stats for p_wait?
                    # p_wait = fraction of arrivals that had to wait.
                    # Count how many arrivals found system full (i.e., went to queue).
                    
                    pass
                
                # Re-implementing the loop cleanly below to avoid confusion.
                # I will rewrite the inner loop logic properly.
                
                # Resetting variables for clean implementation
                # ...
                
                # Actually, let's just write the correct logic directly.
                
                # Previous logic flaw:
                # In 'arr', if n_in_system < c, we add to service.
                # Else, we add to queue.
                # In 'dep', we decrement n_in_system.
                # If queue not empty, we pop and schedule new dep.
                # This works for N(t).
                
                # For p_wait:
                # Need to count arrivals that were forced to queue.
                # Add a counter `waited_arrivals`.
                
                # For busy_frac:
                # busy_time accumulated when n_in_system > 0.
                # busy_frac = busy_time / win.
                
                # For L:
                # L = area_n / win.
                
                # For W:
                # W = area_n / dep_count (within window).
                # Note: dep_count must be within window.
                
                # Let's restart the simulation loop structure mentally to ensure correctness.
                
                # Variables per seed:
                # t, next_arr, events (heap), queue (list), n_in_system
                # area_n, busy_time, arr_count, dep_count, blk_count, waited_count
                # warmup cutoff.
                
                # Events: ('arr', time), ('dep', time, start_time_of_service_for_this_car?)
                # Actually, for dep, we just need to know it's a departure.
                # We don't need start time unless calculating individual sojourn times explicitly.
                # Using area_n method avoids storing individual times.
                
                # Implementation details:
                # Use heapq for events.
                # Event tuple: (time, type, data)
                # Type 0: Arrival, Type 1: Departure.
                # Tie-breaking: usually arrival before departure if same time?
                # Problem says FCFS. If arrival and departure at same time, does arriving car see empty spot?
                # Standard convention: Process departure first to free up server, then arrival can use it.
                # Or process arrival first?
                # If we process arrival first, it might get blocked even though a car is leaving right now.
                # Usually, in discrete event sim, if times are equal, order matters.
                # Let's assume Departure happens before Arrival if times are identical, to maximize throughput/accuracy.
                # So sort key: (time, type_order). Dep=0, Arr=1.
                
                # Let's rewrite the code block.
                
                # Clear previous messy thoughts.
                
                # Initialize per-seed vars
                t = 0.0
                next_arr = rng.expovariate(lam)
                events = []
                import heapq
                queue = []
                n_in_system = 0
                area_n = 0.0
                busy_time = 0.0
                arr_count = 0
                dep_count = 0
                blk_count = 0
                waited_count = 0
                
                # Helper to push event
                def push_ev(time, typ, data=None):
                    # typ: 0 for dep, 1 for arr (to prioritize dep on tie)
                    heapq.heappush(events, (time, typ, data))
                
                # Initial arrival
                push_ev(next_arr, 1)
                
                while events:
                    curr_t, typ, data = heapq.heappop(events)
                    
                    # Accumulate areas up to curr_t
                    dt = curr_t - t
                    if t >= warmup:
                        area_n += n_in_system * dt
                        if n_in_system > 0:
                            busy_time += dt
                    
                    t = curr_t
                    
                    if t >= horizon:
                        break
                        
                    if typ == 1: # Arrival
                        arr_count += 1
                        if n_in_system < c:
                            n_in_system += 1
                            svc_dur = 6.0
                            dep_t = t + svc_dur
                            push_ev(dep_t, 0)
                        else:
                            queue.append(t) # Store arrival time for potential individual calc, though we use area method
                            n_in_system += 1
                            waited_count += 1
                            
                        next_arr = t + rng.expovariate(lam)
                        push_ev(next_arr, 1)
                        
                    elif typ == 0: # Departure
                        dep_count += 1
                        n_in_system -= 1
                        if queue:
                            arr_time_queued = queue.pop(0)
                            # Start service for this queued car
                            svc_dur = 6.0
                            dep_t = t + svc_dur
                            push_ev(dep_t, 0)
                            # n_in_system remains same? 
                            # No. The departing car left (-1). The queued car was already counted (+1 earlier).
                            # It moves from queue to service. Count doesn't change due to move.
                            # So net change is -1. Correct.
                
                # Final accumulation if loop broke early?
                # The loop breaks when t >= horizon.
                # We need to integrate until horizon.
                # If we broke out, we haven't integrated from last event time to horizon.
                # But the condition `if t >= horizon: break` happens AFTER updating t to curr_t.
                # And BEFORE processing the event?
                # No, I processed the event.
                # Wait, if curr_t >= horizon, we shouldn't process the event?
                # Usually, we stop simulation at horizon.
                # If an event occurs exactly at horizon, do we count it?
                # Typically, interval is [0, H).
                # Let's adjust:
                # While events and events[0][0] < horizon:
                #   process event.
                # After loop, integrate from t to horizon.
                
                # Redoing the loop structure for clarity.
                
                # Reset
                t = 0.0
                next_arr = rng.expovariate(lam)
                events = []
                queue = []
                n_in_system = 0
                area_n = 0.0
                busy_time = 0.0
                arr_count = 0
                dep_count = 0
                blk_count = 0
                waited_count = 0
                
                heapq.heappush(events, (next_arr, 1, None))
                
                while events:
                    curr_t, typ, data = events[0]
                    if curr_t >= horizon:
                        break
                    heapq.heappop(events)
                    
                    dt = curr_t - t
                    if t >= warmup:
                        area_n += n_in_system * dt
                        if n_in_system > 0:
                            busy_time += dt
                    t = curr_t
                    
                    if typ == 1: # Arrival
                        arr_count += 1
                        if n_in_system < c:
                            n_in_system += 1
                            dep_t = t + 6.0
                            heapq.heappush(events, (dep_t, 0, None))
                        else:
                            queue.append(t)
                            n_in_system += 1
                            waited_count += 1
                        next_arr = t + rng.expovariate(lam)
                        heapq.heappush(events, (next_arr, 1, None))
                        
                    else: # Departure
                        dep_count += 1
                        n_in_system -= 1
                        if queue:
                            queue.pop(0)
                            dep_t = t + 6.0
                            heapq.heappush(events, (dep_t, 0, None))
                
                # Integrate remaining time to horizon
                dt = horizon - t
                if t >= warmup:
                    area_n += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                
                win = horizon - warmup
                if win <= 0:
                    win = 1e-9
                
                s_L = area_n / win
                s_W = area_n / dep_count if dep_count > 0 else 0.0
                s_busy = busy_time / win
                s_p_loss = blk_count / arr_count if arr_count > 0 else 0.0
                s_p_wait = waited_count / arr_count if arr_count > 0 else 0.0
                
                per_seed_L.append(s_L)
                per_seed_W.append(s_W)
                per_seed_busy_frac.append(s_busy)
                per_seed_p
