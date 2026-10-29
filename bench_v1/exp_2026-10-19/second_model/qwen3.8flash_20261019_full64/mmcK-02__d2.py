import random, json, argparse, sys

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

    # Parameters in hours
    lam_base = 6.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr
    c = 2
    K = 4 # capacity including service

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
    
    if pert != 'mu_up' and pert != 'lam_up':
        mu = mu_base
    if pert == 'mu_up':
        pass # already set
        
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
    all_busy_occupied = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # list of (arrival_time, service_duration)
        n_in_system = 0
        
        # Statistics accumulators (for area integration)
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0 # time when at least one server is busy? No, busy_frac defined as station not empty (1-pi0). 
                        # Wait, prompt says: busy_frac definition: station not empty time proportion 1-pi0.
                        # And busy_util = E[min(N,c)]/c.
                        # So I need to track:
                        # 1. Time integral of N(t) for L
                        # 2. Time integral of (N(t)>0 ? 1 : 0) for busy_frac (1-pi0)
                        # 3. Time integral of min(N(t), c) for busy_util numerator
                        
        area_min_N_c = 0.0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_W = 0.0
        count_waited = 0 # Customers who waited (arrival < start_service)
        
        # Warmup removal: discard first 25% of horizon
        warmup_end = 0.25 * H
        stats_start_time = warmup_end
        
        # We need to handle events properly.
        # Events: Arrival, Departure
        
        while t < H:
            # Determine next event time
            next_dep = min(servers_free_at) if any(f > t for f in servers_free_at) else float('inf')
            # Actually, servers_free_at contains times when they become free.
            # If a server is idle, its free time is <= t.
            # Let's find the earliest future departure among active services.
            # Active services are those where server_free_at > t.
            active_deps = [f for f in servers_free_at if f > t]
            if active_deps:
                next_dep = min(active_deps)
            else:
                next_dep = float('inf')
                
            next_evt = min(next_arrival, next_dep)
            
            if next_evt > H:
                break
                
            # Integrate areas from last_event_time to next_evt
            dt = next_evt - last_event_time
            if dt > 0:
                # Current N is n_in_system
                area_L += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
                area_min_N_c += min(n_in_system, c) * dt
            
            last_event_time = next_evt
            t = next_evt
            
            if t >= stats_start_time:
                # Only record stats after warmup? 
                # The prompt says: "statistics only accumulated in window after removing first 25% warmup".
                # This usually means we run the sim for full H, but ignore data before 0.25H.
                # However, area integrals must be handled carefully.
                # Simpler approach: Run full sim, but reset accumulators at warmup_end?
                # Or just integrate everything and subtract the pre-warmup part?
                # Given the complexity of discrete events, it's easier to just start collecting stats once t >= warmup_end.
                # But we must ensure the system state is correct.
                pass

            # Process Event
            if next_evt == next_arrival:
                count_arrivals += 1
                # Check capacity
                if n_in_system < K:
                    # Accept
                    n_in_system += 1
                    # Find free server
                    free_idx = -1
                    for j in range(c):
                        if servers_free_at[j] <= t:
                            free_idx = j
                            break
                    
                    svc_dur = rng.expovariate(mu)
                    
                    if free_idx != -1:
                        # Start immediately
                        servers_free_at[free_idx] = t + svc_dur
                        # Did not wait
                        if t >= stats_start_time:
                            sum_W += svc_dur # W is total time in system? Usually W is waiting+service or just waiting?
                            # Prompt asks for W (minutes). In queueing theory, W often denotes sojourn time (waiting + service).
                            # Let's assume Sojourn Time.
                            # If started immediately, sojourn = svc_dur.
                            pass
                    else:
                        # Queue
                        queue.append((t, svc_dur))
                        # Will calculate W upon departure
                else:
                    # Block
                    count_blocks += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif next_evt == next_dep:
                # A server becomes free
                # Find which server(s) became free at this exact time
                freed_servers = []
                for j in range(c):
                    if abs(servers_free_at[j] - t) < 1e-9:
                        freed_servers.append(j)
                
                # Handle departures from queue
                # One departure per freed server slot effectively reduces N by 1
                # But we need to know how many people left.
                # Since we have multiple servers freeing up, we process them.
                
                # Actually, standard M/M/c/K logic:
                # When a service completes, that customer leaves.
                # If there is someone in queue, they enter service.
                
                # How many customers leave? Exactly len(freed_servers)?
                # No, each freed server corresponds to one completed service.
                # So number of departures = len(freed_servers)
                
                num_leaving = len(freed_servers)
                count_departures += num_leaving
                n_in_system -= num_leaving
                
                # For each leaving customer, we need their arrival time to compute W.
                # Problem: We don't store arrival time on the server object directly in simple arrays.
                # We need to track who is being served.
                
                # Refactor: Use a list of active services: (start_time, end_time, arrival_time)
                # This is cleaner.
                
                # Let's restart the simulation loop with a better structure.
                # It's too late to refactor inside the loop easily without breaking flow.
                # I will rewrite the inner loop logic completely below.
                break # Exit this attempt to rewrite

        # --- REWRITTEN SIMULATION LOGIC ---
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Active services: list of dicts {end_time, arrival_time}
        active_services = []
        # Queue: list of dicts {arrival_time, service_duration}
        queue = []
        n_in_system = 0
        
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        area_min_N_c = 0.0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        sum_W = 0.0
        count_waited = 0
        
        warmup_end = 0.25 * H
        
        while t < H:
            # Next departure time
            if active_services:
                next_dep = min(s['end_time'] for s in active_services)
            else:
                next_dep = float('inf')
            
            next_evt = min(next_arrival, next_dep)
            
            if next_evt > H:
                # Integrate remaining time
                dt = H - last_event_time
                if dt > 0:
                    if last_event_time < warmup_end:
                        # Split integration
                        split_t = min(warmup_end, H)
                        dt_pre = split_t - last_event_time
                        dt_post = H - split_t
                        # Pre-warmup ignored for stats, but we need to maintain state?
                        # State is maintained regardless. Stats accumulation starts at warmup_end.
                        # So we only add to area_* if interval overlaps with [warmup_end, H]
                        overlap_start = max(last_event_time, warmup_end)
                        overlap_end = H
                        if overlap_start < overlap_end:
                            dt_overlap = overlap_end - overlap_start
                            area_L += n_in_system * dt_overlap
                            if n_in_system > 0:
                                area_busy += dt_overlap
                            area_min_N_c += min(n_in_system, c) * dt_overlap
                    else:
                        area_L += n_in_system * dt
                        if n_in_system > 0:
                            area_busy += dt
                        area_min_N_c += min(n_in_system, c) * dt
                break
            
            # Integrate area from last_event_time to next_evt
            dt = next_evt - last_event_time
            if dt > 0:
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = next_evt
                if overlap_start < overlap_end:
                    dt_overlap = overlap_end - overlap_start
                    area_L += n_in_system * dt_overlap
                    if n_in_system > 0:
                        area_busy += dt_overlap
                    area_min_N_c += min(n_in_system, c) * dt_overlap
            
            last_event_time = next_evt
            t = next_evt
            
            if t >= warmup_end:
                # Record counts/stats for this event if it happens in window
                # Note: Area is already integrated. Counts like arrivals/departures/blocks 
                # should also be restricted to the window?
                # "Statistics ... accumulated in window". Yes.
                pass

            if next_evt == next_arrival:
                if t >= warmup_end:
                    count_arrivals += 1
                
                if n_in_system < K:
                    n_in_system += 1
                    svc_dur = rng.expovariate(mu)
                    
                    # Find free server
                    # Count available slots
                    num_active = len(active_services)
                    if num_active < c:
                        # Start service immediately
                        end_time = t + svc_dur
                        active_services.append({'end_time': end_time, 'arrival_time': t})
                        if t >= warmup_end:
                            sum_W += svc_dur # Sojourn time
                            # Did not wait
                    else:
                        # Join queue
                        queue.append({'arrival_time': t, 'svc_dur': svc_dur})
                        if t >= warmup_end:
                            count_waited += 1 # Marked as waited, W added later
                else:
                    if t >= warmup_end:
                        count_blocks += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif next_evt == next_dep:
                # All services ending at t
                finished = [s for s in active_services if abs(s['end_time'] - t) < 1e-9]
                active_services = [s for s in active_services if abs(s['end_time'] - t) >= 1e-9]
                
                num_finished = len(finished)
                n_in_system -= num_finished
                
                if t >= warmup_end:
                    count_departures += num_finished
                    for s in finished:
                        w = s['end_time'] - s['arrival_time']
                        sum_W += w
                
                # Move from queue to service
                # Number of new services starting = min(num_finished, len(queue))
                # But actually, each finished slot allows one queued car to start.
                slots_freed = num_finished
                while slots_freed > 0 and queue:
                    q_item = queue.pop(0)
                    start_time = t
                    end_time = start_time + q_item['svc_dur']
                    active_services.append({'end_time': end_time, 'arrival_time': q_item['arrival_time']})
                    n_in_system += 1 # Still in system, just moved from queue to service
                    slots_freed -= 1
                    
                    if t >= warmup_end:
                        # This customer was waiting, now enters service.
                        # Their W will be calculated when they finish.
                        pass

        # End of simulation for seed s
        
        # Calculate metrics for this seed
        # Window length for stats
        win_len = H - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        L_est = area_L / win_len
        busy_frac_est = area_busy / win_len
        busy_util_est = area_min_N_c / (win_len * c)
        busy_occupied_est = busy_frac_est # Same as 1-pi0
        
        # p_loss = blocks / arrivals_in_window? Or blocks / potential_arrivals?
        # Usually loss probability is fraction of arriving customers lost.
        # Denominator should be total arrivals attempted in window.
        # But note: some arrivals might be blocked because system full.
        # p_loss = count_blocks / (count_arrivals + count_blocks)? 
        # No, count_arrivals here counts ONLY accepted ones? 
        # In my code: `if t >= warmup_end: count_arrivals += 1` happens BEFORE check capacity?
        # No, look at code:
        # if next_evt == next_arrival:
        #   if t >= warmup_end: count_arrivals += 1
        #   if n_in_system < K: ... else: if t>=warmup: count_blocks+=1
        # So count_arrivals includes both accepted and blocked?
        # Yes, count_arrivals increments for every arrival event in window.
        # count_blocks increments for blocked ones.
        # So p_loss = count_blocks / count_arrivals.
        
        p_loss_est = count_blocks / count_arrivals if count_arrivals > 0 else 0.0
        
        # p_wait: Probability an arriving customer waits.
        # Numerator: count_waited (accepted ones who went to queue)
        # Denominator: count_arrivals (all attempts) OR count_accepted?
        # Standard P_wait is prob that an ARRIVING customer has to wait.
        # So denominator is total arrivals.
        p_wait_est = count_waited / count_arrivals if count_arrivals > 0 else 0.0
        
        # W average
        # sum_W accumulated for:
        # 1. Immediate service completions (added at arrival time? No, added at arrival time in my code?
        #    Look: `if num_active < c: ... if t>=warmup: sum_W += svc_dur`.
        #    This adds the SERVICE duration, not the SOJOURN duration yet?
        #    Wait, if they start immediately, Sojourn = Service Duration. Correct.
        # 2. Queued service completions (added at departure time).
        #    Look: `for s in finished: w = ...; sum_W += w`.
        #    This covers everyone who finished in the window.
        #    BUT: What about people who arrived in window but haven't finished by H?
        #    They are excluded from sum_W.
        #    Also, what about people who arrived BEFORE window but finished IN window?
        #    My code adds their W to sum_W.
        #    This creates a bias.
        #    Better approach for W: Average over customers COMPLETED in the window.
        #    Denominator for W should be count_departures.
        #    Let's check: sum_W is sum of sojourn times for all customers who DEPARTED in the window.
        #    So W_avg = sum_W / count_departures.
        
        W_est = sum_W / count_departures if count_departures > 0 else 0.0
        
        # Convert W to minutes
        W_min = W_est * 60.0
        
        all_L.append(L_est)
        all_W.append(W_min)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arrivals)
        all_blk.append(count_blocks)
        all_dep.append(count_departures)
        all_busy_util.append(bus
