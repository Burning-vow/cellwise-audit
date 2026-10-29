import random, json, math, argparse

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

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
    c = 2                  # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    horizon_min = H  # assume H is in minutes based on typical usage, but problem says time_unit self-reported. Let's stick to minutes internally.
    
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
    
    seeds_used_list = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        # Event simulation
        # State: t, n_in_system, next_arrival_time, list of departure times (sorted or heap)
        # We use a simple event loop with priority queue via sorted list or heapq
        
        import heapq
        
        t = 0.0
        n = 0
        # Pre-generate arrival and service times? 
        # Requirement: service duration drawn at arrival.
        
        events = [] # (time, type, data) type: 0=arrival, 1=departure
        
        # Initial arrival
        inter_arr = rng.expovariate(lam)
        heapq.heappush(events, (inter_arr, 0, None))
        
        # Warmup: discard first 25% of horizon
        warmup_end = 0.75 * horizon_min
        stats_start = warmup_end
        
        # Accumulators for area integration (L) and counts (W, p_wait, etc.) within window [stats_start, horizon_min]
        last_t = 0.0
        area_L = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0 # Sum of sojourn times for customers who departed in window? Or arrived in window?
        # Usually W is average sojourn time of customers served in the window.
        # p_wait is fraction of arrivals in window that had to wait.
        count_arr_window = 0
        count_wait_window = 0
        
        # To calculate W correctly as average over customers, we need to track individual sojourns.
        # But standard discrete event sim often accumulates total time in system for completed services.
        
        # Let's refine:
        # L = Time-average number in system. Integrate n(t) over [stats_start, horizon].
        # W = Average sojourn time. Sum(sojourn_i) / Count_departures_in_window? 
        # Or Little's Law check? The prompt asks for specific metrics.
        # "统计量只在去掉前 25% 预热后的窗口内累计"
        
        # We need to handle events crossing the boundary carefully.
        # Simpler approach: Run full sim, record events, then filter? No, memory.
        # Online accumulation:
        
        # Variables for current state
        # n: number in system
        # busy_servers: number of servers currently occupied (min(n, c))
        
        # For p_wait: At arrival, if n >= c, they wait.
        
        # For W: Need to know when each customer arrives and departs.
        # Since we draw service time at arrival, we can store arrival time in the departure event.
        
        # Reset accumulators for this seed
        area_L_acc = 0.0
        last_t_acc = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_count_win = 0
        sum_sojourn_win = 0.0
        
        # Helper to update area
        def update_area(current_t, current_n):
            nonlocal area_L_acc, last_t_acc
            dt = current_t - last_t_acc
            if last_t_acc < stats_start:
                # Partial overlap
                if current_t > stats_start:
                    dt_overlap = current_t - max(last_t_acc, stats_start)
                    area_L_acc += current_n * dt_overlap
            else:
                area_L_acc += current_n * dt
            
            last_t_acc = current_t

        while events:
            t_curr, ev_type, data = heapq.heappop(events)
            
            if t_curr > horizon_min:
                break
                
            # Update area up to this event time
            update_area(t_curr, n)
            
            if ev_type == 0: # Arrival
                # Check if blocked (infinite queue? Problem doesn't specify capacity limit, usually infinite for bank unless stated. "需要排队的概率" implies waiting allowed. So no blocking/loss due to capacity. blk should be 0?)
                # Wait, "blk" key exists. If infinite queue, blk=0.
                # However, if the system is saturated, maybe loss? Standard M/M/c has no loss.
                # I will assume infinite queue, so blk=0.
                
                # Draw service time now
                svc_time = rng.expovariate(mu)
                
                # Determine if waits
                if n >= c:
                    is_wait = True
                else:
                    is_wait = False
                
                # Record arrival stats if in window
                if t_curr >= stats_start:
                    arr_count_win += 1
                    if is_wait:
                        wait_count_win += 1
                
                n += 1
                
                # Schedule departure
                # Departure time = t_curr + svc_time
                # But if server is free, it starts immediately. If not, it queues.
                # In FCFS, the departure time depends on queue position.
                # Simplest way: Maintain a list of scheduled departures?
                # Actually, since we just increment n, and schedule a departure at t+svc, 
                # this assumes the service starts immediately? NO.
                # If n > c, the new customer joins queue. Their service hasn't started.
                # This model requires tracking when service actually starts.
                
                # Alternative standard approach:
                # Keep track of when servers become free.
                # Or, simpler: Just push departure event at t + svc_time ONLY IF server was free.
                # If server was busy, we don't know start time yet.
                
                # Correct Logic:
                # We need to know how many servers are busy.
                # If n_before < c, server is free. Service starts at t_curr. Dep at t_curr + svc.
                # If n_before >= c, server is busy. Customer waits.
                # When does their service start? When a previous customer departs.
                
                # This makes the "draw at arrival" requirement tricky for scheduling.
                # We must store the service time with the customer.
                # We can maintain a queue of customers waiting for service.
                # And a set of active services with end times.
                
                # Let's refactor state:
                # n_total: total in system
                # active_services: list of end_times (heap)
                # waiting_queue: list of (arrival_time, service_duration)
                
                # On Arrival:
                # Add to waiting_queue or start immediately.
                # If len(active_services) < c:
                #   Start service: end_time = t_curr + svc_time. Push to active_services.
                #   Remove from waiting_queue logic (it wasn't added).
                # Else:
                #   Add to waiting_queue.
                
                # On Departure:
                # Pop one from active_services.
                # n_total -= 1.
                # If waiting_queue not empty:
                #   Pop front customer.
                #   Start service: end_time = t_curr + cust_svc_time. Push to active_services.
                #   n_total remains same (one left, one entered service).
                # Else:
                #   n_total decreases by 1 effectively? No, n_total tracks total people.
                #   If someone leaves, n_total drops. If someone enters service from queue, n_total stays.
                
                # Let's implement this properly.
                
                # Re-initialize structures for this seed before loop?
                # I'll move the detailed logic inside the loop using external variables.
                
                # Wait, I already popped the event. I need to restructure the whole loop.
                pass

            elif ev_type == 1: # Departure
                pass

        # The above structure is getting messy because I tried to mix two approaches.
        # Let's restart the inner loop logic cleanly.
        
        # Reset for clean implementation
        rng = random.Random(seed)
        t = 0.0
        n_total = 0
        active_end_times = [] # Heap of end times
        waiting_customers = [] # Queue of (arrival_time, svc_time)
        
        # Generate first arrival
        next_arr_time = rng.expovariate(lam)
        
        # Stats accumulators
        area_L_acc = 0.0
        last_t_acc = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_count_win = 0
        sum_sojourn_win = 0.0
        
        # We need to process events until horizon
        # Events are implicit: Next Arrival vs Next Departure
        
        while True:
            # Determine next event time
            next_dep_time = active_end_times[0] if active_end_times else float('inf')
            next_arr_event_time = next_arr_time
            
            if next_dep_time <= next_arr_event_time:
                t_next = next_dep_time
                ev_type = 'dep'
            else:
                t_next = next_arr_event_time
                ev_type = 'arr'
                
            if t_next > horizon_min:
                # Final area update up to horizon
                dt = horizon_min - last_t_acc
                if last_t_acc < stats_start:
                    if horizon_min > stats_start:
                        dt_overlap = horizon_min - max(last_t_acc, stats_start)
                        area_L_acc += n_total * dt_overlap
                else:
                    area_L_acc += n_total * dt
                break
            
            # Update area up to t_next
            dt = t_next - last_t_acc
            if last_t_acc < stats_start:
                if t_next > stats_start:
                    dt_overlap = t_next - max(last_t_acc, stats_start)
                    area_L_acc += n_total * dt_overlap
            else:
                area_L_acc += n_total * dt
            last_t_acc = t_next
            
            if ev_type == 'arr':
                # Draw service time
                svc = rng.expovariate(mu)
                
                # Check wait condition BEFORE adding to system?
                # "到达时需要排队" -> if all servers busy.
                # Servers busy count = len(active_end_times)
                if len(active_end_times) >= c:
                    is_wait = True
                else:
                    is_wait = False
                    
                if t_next >= stats_start:
                    arr_count_win += 1
                    if is_wait:
                        wait_count_win += 1
                
                n_total += 1
                
                if len(active_end_times) < c:
                    # Start service immediately
                    heapq.heappush(active_end_times, t_next + svc)
                else:
                    # Join queue
                    waiting_customers.append((t_next, svc))
                    
                # Schedule next arrival
                next_arr_time = t_next + rng.expovariate(lam)
                
            else: # dep
                # A customer finishes service
                heapq.heappop(active_end_times)
                n_total -= 1
                
                # Who departed? We need to know their arrival time to calc sojourn.
                # Problem: We lost the link between the departure event and the specific customer's arrival time.
                # Solution: Store (end_time, arrival_time) in the heap.
                
                # REFACTOR: active_end_times stores (end_time, arrival_time)
                # Let's fix the heap content definition.
                
                # I need to rewrite the block slightly to include arrival_time in heap.
                # Since I am generating code, I will adjust the logic above mentally and write correct code.
                
                # Correction for 'dep' branch:
                # The heap contains tuples (end_time, arrival_time).
                # When popping, we get the arrival_time.
                # Sojourn = t_next - arrival_time.
                # If t_next >= stats_start, add to sum_sojourn_win and dep_count_win.
                
                # Also, after departure, check if queue has people.
                if waiting_customers:
                    arr_t, svc_t = waiting_customers.pop(0)
                    # Start service for this person
                    new_end = t_next + svc_t
                    heapq.heappush(active_end_times, (new_end, arr_t))
                    # n_total stays same (one left, one entered service)
                    # Wait, n_total was decremented above. Now we add back?
                    # Yes, person moves from queue to service. Total in system unchanged.
                    n_total += 1 
                else:
                    # No one waiting, n_total decreased by 1 (the one who left)
                    pass

        # Calculate metrics for this seed
        win_len = horizon_min - stats_start
        if win_len <= 0:
             L_est = 0.0
             W_est = 0.0
             p_wait_est = 0.0
             busy_frac_est = 0.0
        else:
            L_est = area_L_acc / win_len
            if dep_count_win > 0:
                W_est = sum_sojourn_win / dep_count_win
            else:
                W_est = 0.0
            
            if arr_count_win > 0:
                p_wait_est = wait_count_win / arr_count_win
            else:
                p_wait_est = 0.0
                
            # Busy frac: E[min(N,c)]/c
            # We didn't integrate min(N,c). We integrated N.
            # Need to integrate min(N,c) separately or derive?
            # Deriving from N is hard without knowing distribution.
            # Must integrate min(N,c) during loop.
            
            # I missed integrating busy servers.
            # Let's add `area_busy_acc` in the real code.
            
            busy_frac_est = 0.0 # Placeholder, will fix in final code generation.
            
        # Fixing the missing busy integration in the thought process:
        # I will ensure the final code integrates min(n_total, c).
        
        # Recalculating placeholders for output structure
        # I will generate the final code string directly now, incorporating the fixes.
        
        # For the purpose of this scratchpad, I acknowledge the bug in my mental draft regarding busy_frac integration and heap tuple structure.
        # The final code below will be corrected.
        
        # Metrics for aggregation
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(0.0) # Will be calculated in final code
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count_win)
        all_dep.append(dep_count_win)
        all_blk.append(blk_count_win)
        all_busy_util.append(0.0)
        all_dep_rate.append(0.0)
        all_lam_eff.append(0.0)
        all_p_loss.append(0.0)
        seeds_used_list.append(seed)

    # Aggregation
    avg_L = sum(all_L)/N_seeds if N_seeds>0 else 0
    avg_W = sum(all_W)/N_seeds if N_seeds>0 else 0
    avg_busy_frac = sum(all_busy_frac)/N_seeds if N_seeds>0 else 0
    avg_p_wait = sum(all_p_wait)/N_seeds if N_seeds>0 else 0
    avg_arr = sum(all_arr)/N_seeds if N_seeds>0 else 0
    avg_dep = sum(all_dep)/N_seeds if N_seeds>0 else 0
    avg_blk = sum(all_blk)/N_seeds if N_seeds>0 else 0
    avg_busy_util = sum(all_busy_util)/N_seeds if N_seeds>0 else 0
    avg_dep_rate = sum(all_dep_rate)/N_seeds if N_seeds>0 else 0
    avg_lam_eff = sum(all_lam_eff)/N_seeds if N_seeds>0 else 0
    avg_p_loss = sum(all_p_loss)/N_seeds if N_seeds>0 else 0
    
    # Note: The above loop logic was flawed in the scratchpad. 
    # I will now produce the CORRECTED Python code.
    
    # Key corrections needed in final code:
    # 1. Heap stores (end_time, arrival_time).
    # 2. Integrate both n_total and min(n_total, c) for area_L and area_busy.
    #
