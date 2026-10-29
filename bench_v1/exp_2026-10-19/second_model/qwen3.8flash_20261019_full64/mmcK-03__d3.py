import sys, json, random, math
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            k = sys.argv[i][2:]
            v = sys.argv[i+1] if i+1 < len(sys.argv) else None
            args[k] = v
            i += 2
        else:
            i += 1
    
    N = int(args.get('seeds', 5))
    H = float(args.get('horizon', 100.0))
    S = int(args.get('seed-start', 1))
    pert = args.get('pert', 'none')
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 12.0 # 5 per hour
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
    all_dep_rate = []
    all_lam_eff = []
    
    seeds_used = 0
    seed_list = []
    
    for s_idx in range(N):
        seed = S + s_idx
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_sys = 0
        servers_free_time = [0.0, 0.0] # For c=2, extend if needed
        if c > 2:
             servers_free_time = [0.0] * c
        
        # Event queue: (time, type, data)
        # type: 0=arrival, 1=departure
        events = []
        
        # Generate first arrival
        next_arrival_t = rng.expovariate(lam)
        events.append((next_arrival_t, 0, None))
        
        # Statistics accumulators (for the whole run initially, then we filter or just use warmup logic)
        # Warmup is 25% of horizon
        warmup_end = 0.25 * H
        
        # We need to track state changes to integrate area.
        # Since it's a discrete event sim, we can accumulate area between events.
        
        total_area_n = 0.0
        total_time_window = 0.0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        
        # For W calculation: sum of waiting times (queueing time only? or system time?)
        # Standard Little's Law L = lambda * W usually refers to System Time (W_s).
        # However, often "W" in these contexts might mean Waiting Time in Queue (W_q).
        # The prompt asks for W (minutes). Usually W includes service unless specified Wq.
        # Let's assume W is System Time (Time in system).
        # But wait, "busy_frac" is defined as station not empty. 
        # Let's look at standard M/M/c/K.
        # If W is system time, L = lambda_eff * W.
        # If W is queue time, Lq = lambda_eff * Wq.
        # The prompt says "L, W". Usually L is number in system, W is time in system.
        # I will calculate System Time.
        
        sum_system_times = 0.0
        count_completed_customers = 0
        
        # To handle warmup properly with area integration:
        # We simulate until H.
        # We record state transitions.
        # After simulation, we re-calculate stats based on the timeline segments that fall after warmup_end.
        
        timeline = [] # List of (start_t, end_t, n_val)
        
        current_state_start = 0.0
        current_n = 0
        
        # Helper to add segment
        def add_segment(start, end, val):
            if end > start:
                timeline.append((start, end, val))
                
        # Simulation Loop
        while events:
            # Pop earliest event
            events.sort(key=lambda x: x[0])
            t_event, e_type, e_data = events.pop(0)
            
            if t_event > H:
                break
                
            # Add segment from last change to now
            add_segment(current_state_start, t_event, current_n)
            current_state_start = t_event
            
            if e_type == 0: # Arrival
                count_arrivals += 1
                if n_in_sys < K:
                    # Accept
                    n_in_sys += 1
                    current_n = n_in_sys
                    
                    # Find free server
                    min_server_idx = -1
                    min_free_time = float('inf')
                    for i in range(c):
                        if servers_free_time[i] <= t_event:
                            min_server_idx = i
                            break
                        if servers_free_time[i] < min_free_time:
                            min_free_time = servers_free_time[i]
                            min_server_idx = i
                            
                    if min_server_idx != -1 and servers_free_time[min_server_idx] <= t_event:
                        # Start immediately
                        service_dur = rng.expovariate(mu)
                        dep_t = t_event + service_dur
                        servers_free_time[min_server_idx] = dep_t
                        events.append((dep_t, 1, {'arr_t': t_event, 'server': min_server_idx}))
                    else:
                        # Wait in queue
                        # Store arrival time for this customer
                        # We need to associate this customer with a specific slot in queue?
                        # In M/M/c, FCFS.
                        # We push arrival time to a queue structure associated with the system?
                        # Actually, simpler: when a server becomes free, it picks the oldest waiting customer.
                        # We need a list of waiting customers' arrival times.
                        pass 
                    
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    events.append((t_event + inter_arr, 0, None))
                else:
                    # Block
                    count_blocks += 1
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    events.append((t_event + inter_arr, 0, None))
                    
            elif e_type == 1: # Departure
                arr_t = e_data['arr_t']
                server_idx = e_data['server']
                
                # Customer leaves
                n_in_sys -= 1
                current_n = n_in_sys
                count_departures += 1
                
                # Calculate system time for this customer
                sys_time = t_event - arr_t
                sum_system_times += sys_time
                count_completed_customers += 1
                
                # Check if there are waiting customers
                # We need to know who is waiting. 
                # Problem: My previous logic didn't store waiting customers explicitly.
                # Refactor: Maintain a queue of arrival times for waiting customers.
                # When a departure happens, if queue is not empty, pop front, assign to this server.
                
                # Wait, I didn't implement the waiting queue storage in the arrival branch correctly above.
                # Let's restart the logic inside the loop with proper state management.
                
                # This approach is getting messy because I'm mixing event generation and state tracking.
                # Let's rewrite the core simulation loop cleanly.
                break 

        # RESTARTING SIMULATION LOGIC FOR CLARITY AND CORRECTNESS
        
        # Reset for this seed
        rng = random.Random(seed)
        t = 0.0
        n_in_sys = 0
        servers_free_time = [0.0] * c
        waiting_queue = deque() # Stores arrival times of customers waiting
        
        events = []
        next_arrival_t = rng.expovariate(lam)
        events.append((next_arrival_t, 0, None))
        
        timeline = []
        current_state_start = 0.0
        current_n = 0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_system_times = 0.0
        count_completed_customers = 0
        
        # We also need to track busy time for busy_frac (station not empty)
        # Station not empty means n_in_sys > 0.
        # So we just integrate indicator(n>0).
        
        while events:
            events.sort(key=lambda x: x[0])
            t_event, e_type, e_data = events.pop(0)
            
            if t_event > H:
                # Final segment up to H
                if current_state_start < H:
                    timeline.append((current_state_start, H, current_n))
                break
            
            # Record segment before state change
            if current_state_start < t_event:
                timeline.append((current_state_start, t_event, current_n))
            current_state_start = t_event
            
            if e_type == 0: # Arrival
                count_arrivals += 1
                if n_in_sys < K:
                    n_in_sys += 1
                    current_n = n_in_sys
                    
                    # Try to assign to server
                    assigned = False
                    for i in range(c):
                        if servers_free_time[i] <= t_event:
                            # Server is free
                            service_dur = rng.expovariate(mu)
                            dep_t = t_event + service_dur
                            servers_free_time[i] = dep_t
                            events.append((dep_t, 1, {'arr_t': t_event, 'server': i}))
                            assigned = True
                            break
                    
                    if not assigned:
                        # Must wait
                        waiting_queue.append(t_event)
                        
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    events.append((t_event + inter_arr, 0, None))
                else:
                    count_blocks += 1
                    inter_arr = rng.expovariate(lam)
                    events.append((t_event + inter_arr, 0, None))
                    
            elif e_type == 1: # Departure
                arr_t = e_data['arr_t']
                server_idx = e_data['server']
                
                n_in_sys -= 1
                current_n = n_in_sys
                count_departures += 1
                
                sys_time = t_event - arr_t
                sum_system_times += sys_time
                count_completed_customers += 1
                
                # If someone is waiting, start service
                if waiting_queue:
                    next_arr_t = waiting_queue.popleft()
                    # This customer moves from queue to service
                    # Note: n_in_sys remains same effectively? No, one left, one enters service.
                    # But they were already counted in n_in_sys.
                    # So n_in_sys doesn't change here regarding count, but status changes.
                    # However, our `n_in_sys` tracks total people in system (waiting + serving).
                    # So no change to n_in_sys value.
                    
                    service_dur = rng.expovariate(mu)
                    dep_t = t_event + service_dur
                    servers_free_time[server_idx] = dep_t
                    events.append((dep_t, 1, {'arr_t': next_arr_t, 'server': server_idx}))
                else:
                    servers_free_time[server_idx] = t_event # Mark free immediately? 
                    # Actually, if no one waits, server is idle. 
                    # Setting to t_event is fine, next arrival will see it <= t_event.
        
        # Post-process timeline for statistics within window [warmup_end, H]
        win_start = warmup_end
        win_len = H - win_start
        
        if win_len <= 0:
            continue
            
        area_n = 0.0
        area_busy = 0.0 # Area where n > 0
        
        for seg_start, seg_end, val in timeline:
            # Clip segment to window
            s = max(seg_start, win_start)
            e = min(seg_end, H)
            if s < e:
                dt = e - s
                area_n += val * dt
                if val > 0:
                    area_busy += dt
        
        L_avg = area_n / win_len
        busy_frac_avg = area_busy / win_len
        
        # W: Average system time for customers who departed during the window?
        # Or all customers? 
        # Standard steady-state estimation: Use customers whose entire sojourn is in the window?
        # Or simply average over all completed customers in the window?
        # Given the complexity, let's use the average system time of customers who DEPARTED in the window.
        # We need to filter sum_system_times by departure time.
        # I didn't store departure times in a list. 
        # Let's approximate using Little's Law consistency check or recalculate.
        # Better: Store (dep_time, sys_time) pairs.
        
        # Re-run logic to collect dep times? No, too slow.
        # Let's modify the loop to collect dep info.
        
        # Since I already ran the loop, I'll just use the global averages for W if window is large enough,
        # but strictly speaking, we should filter.
        # For this task, let's assume the provided counts are sufficient for approximation or 
        # I will re-implement quickly to capture dep times.
        
        # Actually, let's just use the overall stats for this seed if the window is significant,
        # but the prompt requires strict windowing.
        # I will modify the simulation to store departures.
        
        # Due to length constraints, I will assume the user accepts the approximation 
        # or I will do a quick second pass logic mentally... 
        # No, I must be precise.
        
        # Let's refactor the inner loop to store dep_events.
        # I will rewrite the block below.
        
        # ... (Rewriting simulation part for precision) ...
        
        # Reset
        rng = random.Random(seed)
        t = 0.0
        n_in_sys = 0
        servers_free_time = [0.0] * c
        waiting_queue = deque()
        events = []
        next_arrival_t = rng.expovariate(lam)
        events.append((next_arrival_t, 0, None))
        
        timeline = []
        current_state_start = 0.0
        current_n = 0
        
        count_arrivals = 0
        count_blocks = 0
        dep_records = [] # (dep_time, sys_time)
        
        while events:
            events.sort(key=lambda x: x[0])
            t_event, e_type, e_data = events.pop(0)
            
            if t_event > H:
                if current_state_start < H:
                    timeline.append((current_state_start, H, current_n))
                break
            
            if current_state_start < t_event:
                timeline.append((current_state_start, t_event, current_n))
            current_state_start = t_event
            
            if e_type == 0:
                count_arrivals += 1
                if n_in_sys < K:
                    n_in_sys += 1
                    current_n = n_in_sys
                    assigned = False
                    for i in range(c):
                        if servers_free_time[i] <= t_event:
                            service_dur = rng.expovariate(mu)
                            dep_t = t_event + service_dur
                            servers_free_time[i] = dep_t
                            events.append((dep_t, 1, {'arr_t': t_event, 'server': i}))
                            assigned = True
                            break
                    if not assigned:
                        waiting_queue.append(t_event)
                    inter_arr = rng.expovariate(lam)
                    events.append((t_event + inter_arr, 0, None))
                else:
                    count_blocks += 1
                    inter_arr = rng.expovariate(lam)
                    events.append((t_event + inter_arr, 0, None))
            else:
                arr_t = e_data['arr_t']
                server_idx = e_data['server']
                n_in_sys -= 1
                current_n = n_in_sys
                sys_time = t_event - arr_t
                dep_records.append((t_event, sys_time))
                
                if waiting_queue:
                    next_arr_t = waiting_queue.popleft()
                    service_dur = rng.expovariate(mu)
                    dep_t = t_event + service_dur
                    servers_free_time[server_idx] = dep_t
                    events.append((dep_t, 1, {'arr_t': next_arr_t, 'server': server_idx}))
                else:
                    servers_free_time[server_idx] = t_event

        # Calculate Stats for Window
        win_start = warmup_end
        win_len = H - win_start
        
        area_n = 0.0
        area_busy = 0.0
        for s, e, val in timeline:
            cs = max(s, win_start)
            ce = min(e, H)
            if cs < ce:
                dt = ce - cs
                area_n += val * dt
                if val > 0:
                    area_busy += dt
        
        L_val = area_n / win_len if win_len > 0 else 0
        busy_frac_val = area_busy / win_len if win_len > 0 else 0
        
        # Filter deps in window
        deps_in_win = [st for dt, st in dep_records if win_start <= dt <= H]
        num_deps_win = len(deps_in_win)
        sum_st_win = sum(deps_in_win)
        
        W_val = (sum_st_win / num_deps_win) * 60.0 if num_deps_win >
