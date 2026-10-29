import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    lam_base = 8.0
    mu_base = 6.0
    c = 3

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    win = H
    warmup_frac = 0.25
    warmup_end = H * (1 - warmup_frac)

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
    seeds_used_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = []
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        total_wait_time_sum = 0.0
        total_service_time_sum = 0.0
        num_customers_served_in_window = 0
        area_N = 0.0
        last_event_time = 0.0
        current_N = 0
        p_wait_count = 0
        p_wait_total = 0

        while True:
            min_server_free = min(servers_free_at) if servers_free_at else float('inf')
            next_departure = min_server_free if queue or any(f > t for f in servers_free_at) else float('inf')
            
            # Determine next event
            events = []
            if next_arrival < float('inf'):
                events.append(('arr', next_arrival))
            if next_departure < float('inf'):
                events.append(('dep', next_departure))
            
            if not events:
                break
            
            event_type, event_time = min(events, key=lambda x: x[1])
            
            if event_time > H:
                break

            # Integrate area before changing state
            dt = event_time - last_event_time
            if last_event_time >= warmup_end and event_time <= H:
                area_N += current_N * dt
            elif last_event_time < warmup_end and event_time > warmup_end:
                dt_warm = warmup_end - last_event_time
                dt_win = event_time - warmup_end
                area_N += current_N * dt_win
            elif last_event_time < warmup_end and event_time <= warmup_end:
                pass
            elif last_event_time >= warmup_end and event_time > H:
                dt_win = H - last_event_time
                area_N += current_N * dt_win

            last_event_time = event_time
            t = event_time

            if event_type == 'arr':
                # Check if server is free at arrival time
                free_idx = -1
                for j in range(c):
                    if servers_free_at[j] <= t:
                        free_idx = j
                        break
                
                if free_idx != -1:
                    # Start service immediately
                    serv_time = rng.expovariate(mu)
                    servers_free_at[free_idx] = t + serv_time
                    current_N += 1
                    if t >= warmup_end:
                        arrivals_in_window += 1
                        total_service_time_sum += serv_time
                        num_customers_served_in_window += 1
                        p_wait_total += 1
                        p_wait_count += 0 # No wait
                else:
                    # Join queue
                    serv_time = rng.expovariate(mu)
                    queue.append((t, serv_time))
                    current_N += 1
                    if t >= warmup_end:
                        arrivals_in_window += 1
                        p_wait_total += 1
                        p_wait_count += 1 # Waited

                next_arrival = t + rng.expovariate(lam)

            elif event_type == 'dep':
                # Find which server finished
                finished_idx = -1
                for j in range(c):
                    if abs(servers_free_at[j] - t) < 1e-9:
                        finished_idx = j
                        break
                
                if finished_idx == -1:
                    # Should not happen with correct logic, but safety
                    continue

                if queue:
                    arr_t, serv_dur = queue.pop(0)
                    wait_time = t - arr_t
                    new_free = t + serv_dur
                    servers_free_at[finished_idx] = new_free
                    current_N -= 1 # One left, one entered service, net change 0? 
                    # Actually: Customer leaves system. Another enters from queue.
                    # So N decreases by 1 (the one leaving), then increases by 1 (the one entering). Net 0.
                    # But we need to track stats for the one leaving.
                    
                    if t >= warmup_end:
                        departures_in_window += 1
                        total_wait_time_sum += wait_time
                        total_service_time_sum += serv_dur
                        num_customers_served_in_window += 1
                        # For W calculation later: sum of (wait+serv) / count
                        # We are accumulating components separately or together?
                        # Let's accumulate total time in system for those who departed in window.
                        # But careful: some might have arrived before window.
                        # The problem says "statistics only in window after removing warmup".
                        # Usually this means events occurring in the window.
                        # If a customer departs in the window, their entire sojourn time counts towards W average?
                        # Or just the part in the window? Standard DES usually averages over customers completing in the window.
                        # Let's assume standard: Average W = Sum(T_i for i departing in window) / Count(departing in window)
                        # T_i = departure_time - arrival_time.
                        # We have arr_t and t (departure).
                        sys_time = t - arr_t
                        # We need to store these sums properly.
                        # I'll use a separate accumulator for system time.
                        # Re-evaluating structure:
                        # I need sum_sys_time for departures in window.
                        # I already have total_wait_time_sum and total_service_time_sum.
                        # sys_time = wait + serv.
                        # So I can add wait_time + serv_dur to a sum_sys_time variable.
                        # Let's rename/adjust.
                        pass
                else:
                    servers_free_at[finished_idx] = float('inf')
                    current_N -= 1
                    if t >= warmup_end:
                        departures_in_window += 1
                        # This case shouldn't happen if we popped from queue correctly or handled immediate service.
                        # Immediate service customers don't go through 'dep' event loop in this simple implementation?
                        # Ah, my logic above: if free_idx found, I set servers_free_at. I did NOT push an event.
                        # I rely on the next iteration finding the min server free time.
                        # But I didn't create a specific 'dep' event for them.
                        # The 'next_departure' calculation uses min(servers_free_at).
                        # So when that time comes, it triggers 'dep'.
                        # In 'dep', if queue is empty, it means the person who was being served finishes.
                        # But I lost their arrival time!
                        
                        # Correction needed: Track customers in service.
                        # Let's restart the simulation logic more carefully.
                        break # Break to rewrite logic below
        
        # Since the logic got tangled, let's implement a cleaner version inside the loop.
        # Resetting variables for clean run
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # List of (arrival_time, service_duration)
        # To handle immediate service, we can treat them as entering queue and immediately popping?
        # Or better: maintain list of active services with their start times.
        
        # Let's use a priority queue approach manually since stdlib heapq is available.
        import heapq
        
        events = [] # (time, type, data)
        heapq.heappush(events, (next_arrival, 'A', None))
        
        # State
        n_in_system = 0
        # For each server, we need to know when it becomes free AND who is being served (for stats)
        # Simpler: Just track completion events.
        
        # Stats accumulators for the window
        sum_sys_time = 0.0
        count_departures = 0
        count_arrivals = 0
        count_blocked = 0
        count_waited = 0 # Arrivals that had to wait
        area_n = 0.0
        last_t = 0.0
        
        # Initial state
        # We need to generate initial arrivals? No, Poisson process starts at 0.
        
        while events:
            etime, etype, edata = heapq.heappop(events)
            
            if etime > H:
                break
            
            # Integrate area
            dt = etime - last_t
            if last_t >= warmup_end:
                area_n += n_in_system * dt
            elif etime > warmup_end:
                area_n += n_in_system * (etime - warmup_end)
            
            last_t = etime
            t = etime
            
            if etype == 'A':
                # Arrival
                count_arrivals += 1 if t >= warmup_end else 0
                
                # Find free server
                free_srv = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_srv = k
                        break
                
                if free_srv != -1:
                    # Start service
                    serv_dur = rng.expovariate(mu)
                    comp_time = t + serv_dur
                    servers_free_at[free_srv] = comp_time
                    heapq.heappush(events, (comp_time, 'D', {'start': t, 'srv': free_srv}))
                    n_in_system += 1
                    # Did they wait? No.
                else:
                    # Queue
                    serv_dur = rng.expovariate(mu)
                    queue.append({'arr': t, 'dur': serv_dur})
                    n_in_system += 1
                    if t >= warmup_end:
                        count_waited += 1
                    
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                heapq.heappush(events, (next_arrival, 'A', None))
                
            elif etype == 'D':
                # Departure
                srv_idx = edata['srv']
                start_time = edata['start']
                
                # Verify this server is indeed finishing this job
                # In FIFO, jobs leave in order of completion? No, exponential memoryless, but FCFS queue.
                # My model: Server picks up job from queue when free.
                # When a D event fires, it corresponds to a specific job started at 'start_time'.
                
                # Calculate system time
                sys_time = t - start_time
                
                if t >= warmup_end:
                    count_departures += 1
                    sum_sys_time += sys_time
                
                n_in_system -= 1
                servers_free_at[srv_idx] = float('inf') # Mark free until next assignment
                
                # Check if queue has waiting customers
                if queue:
                    job = queue.pop(0)
                    # Start service for this job
                    comp_time = t + job['dur']
                    servers_free_at[srv_idx] = comp_time
                    heapq.heappush(events, (comp_time, 'D', {'start': t, 'srv': srv_idx}))
                    n_in_system += 1 # One left, one entered service. Net 0 change in N?
                    # Wait, n_in_system decreased by 1 above. Now increase by 1. Correct.
                    # Note: The job in queue was already counted in n_in_system when it arrived.
                    # So when it moves from queue to service, n_in_system should NOT change.
                    # My code: n_in_system -= 1 (departure). Then if queue: n_in_system += 1.
                    # This implies the queued person was NOT in n_in_system?
                    # Yes, when they arrived and joined queue, I did n_in_system += 1.
                    # So they ARE in n_in_system.
                    # When they move to service, they are still in the system.
                    # So I should NOT increment n_in_system again.
                    # Correction: Remove the increment here.
                    n_in_system -= 1 # Undo the increment I just added erroneously?
                    # Let's trace:
                    # 1. Job arrives, no server free -> queue.append, n_in_system += 1.
                    # 2. Previous job departs -> n_in_system -= 1.
                    # 3. New job starts service -> It was already in system. So n_in_system stays same.
                    # So I must remove the `n_in_system += 1` in the block above.
                    pass 

        # Fix the logic error in the loop above regarding n_in_system update on queue->service transition.
        # I will re-run the simulation with corrected logic.
        
        # Restart simulation for this seed with fixed logic
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = []
        events = []
        heapq.heappush(events, (next_arrival, 'A', None))
        
        n_in_system = 0
        sum_sys_time = 0.0
        count_departures = 0
        count_arrivals = 0
        count_blocked = 0
        count_waited = 0
        area_n = 0.0
        last_t = 0.0
        
        while events:
            etime, etype, edata = heapq.heappop(events)
            if etime > H:
                break
            
            dt = etime - last_t
            if last_t >= warmup_end:
                area_n += n_in_system * dt
            elif etime > warmup_end:
                area_n += n_in_system * (etime - warmup_end)
            
            last_t = etime
            t = etime
            
            if etype == 'A':
                if t >= warmup_end:
                    count_arrivals += 1
                
                free_srv = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_srv = k
                        break
                
                if free_srv != -1:
                    serv_dur = rng.expovariate(mu)
                    comp_time = t + serv_dur
                    servers_free_at[free_srv] = comp_time
                    heapq.heappush(events, (comp_time, 'D', {'start': t, 'srv': free_srv}))
                    n_in_system += 1
                else:
                    serv_dur = rng.expovariate(mu)
                    queue.append({'arr': t, 'dur': serv_dur})
                    n_in_system += 1
                    if t >= warmup_end:
                        count_waited += 1
                
                next_arrival = t + rng.expovariate(lam)
                heapq.heappush(events, (next_arrival, 'A', None))
                
            elif etype == 'D':
                srv_idx = edata['srv']
                start_time = edata['start']
                sys_time = t - start_time
                
                if t >= warmup_end:
                    count_departures += 1
                    sum_sys_time += sys_time
                
                n_in_system -= 1
                servers_free_at[srv_idx] = float('inf')
                
                if queue:
                    job = queue.pop(0)
                    comp_time = t + job['dur']
                    servers_free_at[srv_idx] = comp_time
                    heapq.heappush(events, (comp_time, 'D', {'start': t, 'srv': srv_idx}))
                    # Do not change n_in_system, job was already counted
        
        # Post-process results for this seed
        L_est = area_n / (H - warmup_end) if (H - warmup_end) > 0 else 0.0
        W_est = (sum_sys_time / count_departures) * 60.0 if count_departures > 0 else 0.0 # Convert hours to minutes
        busy_frac_est = L_est / c if c > 0 else 0.0
        p_wait_est = count_waited / count_arrivals if count_arrivals > 0 else 0.0
        p_loss_est = count_blocked / count_arrivals if count_arrivals > 0 else 0.0
        dep_rate_est = count_departures / (H - warmup_end) if
