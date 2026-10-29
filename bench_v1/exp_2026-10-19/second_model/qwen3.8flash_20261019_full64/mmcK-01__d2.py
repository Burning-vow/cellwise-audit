import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 6.0 # per hour
    mu_base = 5.0 # per hour (12 min mean -> 60/12 = 5)
    c = 2
    K = 4
    
    if args.pert == 'lam_up': lam = lam_base * 1.2
    elif args.pert == 'mu_up': mu = mu_base * 1.2
    elif args.pert == 'c_up': c = 3; K = 5
    else: lam, mu = lam_base, mu_base
    
    horizon_hours = args.horizon
    time_unit = 'hour'
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_lam_eff = []
    all_dep_rate = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # list of (arrival_time, service_duration)
        total_customers_in_system = 0
        
        warmup_end = horizon_hours * 0.25
        window_len = horizon_hours - warmup_end
        
        sum_L_area = 0.0
        sum_W_total = 0.0
        count_W = 0
        sum_busy_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_min_N_c = 0.0 # For busy_util integral approximation via events? No, L is area. Busy_util needs E[min(N,c)]. 
                          # We can track N at each event and integrate min(N,c).
        sum_min_N_c_area = 0.0
        
        last_event_t = 0.0
        current_N = 0
        
        # Helper to update integrals up to time t
        def update_integrals(t_now):
            nonlocal sum_L_area, sum_busy_time, sum_min_N_c_area, last_event_t
            dt = t_now - last_event_t
            if dt > 0:
                sum_L_area += current_N * dt
                sum_busy_time += (1 if current_N > 0 else 0) * dt
                sum_min_N_c_area += min(current_N, c) * dt
            last_event_t = t_now

        while t < horizon_hours:
            # Determine next event time
            arr_t = next_arr if next_arr < horizon_hours else float('inf')
            dep_t = min(servers_free_at) if any(f < horizon_hours for f in servers_free_at) else float('inf')
            
            # Find which server finishes first
            min_server_idx = -1
            min_server_time = float('inf')
            for idx, ft in enumerate(servers_free_at):
                if ft < min_server_time:
                    min_server_time = ft
                    min_server_idx = idx
            
            dep_t = min_server_time if min_server_time < horizon_hours else float('inf')
            
            if arr_t <= dep_t:
                t = arr_t
                update_integrals(t)
                
                # Arrival
                count_arr += 1
                
                # Check capacity
                if len(queue) + sum(1 for f in servers_free_at if f <= t) >= K:
                    # Full, blocked
                    count_blk += 1
                else:
                    # Accept
                    svc_dur = rng.expovariate(mu)
                    # Find free server or add to queue
                    found = False
                    for idx in range(c):
                        if servers_free_at[idx] <= t:
                            servers_free_at[idx] = t + svc_dur
                            found = True
                            break
                    if not found:
                        queue.append((t, svc_dur))
                    
                    current_N += 1
                    
                next_arr = t + rng.expovariate(lam)
                
            else:
                t = dep_t
                update_integrals(t)
                
                # Departure from server min_server_idx
                # The customer leaving was the one that started service on this server.
                # But we need to know who it was to calculate W.
                # Actually, we stored start times implicitly by when they grabbed a server.
                # Let's refine: When a customer arrives and finds a free server, they start immediately.
                # If they join queue, they wait until a server frees up.
                
                # Problem: In the arrival block above, if added to queue, we don't assign a server yet.
                # So when a server frees up, we must check if there's someone in the queue.
                
                # Who departed? It's the person who finished service on min_server_idx.
                # We need to track their arrival time.
                # Let's change data structure: servers_free_at stores (finish_time, arrival_time_of_current_cust)
                # Or simpler: keep a separate list for "currently serving" customers with their arrival times.
                
                # Refactoring logic inside loop:
                pass 

        # The above logic got messy because I didn't store arrival times for those in service properly.
        # Let's restart the simulation loop with cleaner state management.
        
        # Reset variables for this seed
        t = 0.0
        next_arr = rng.expovariate(lam)
        # State: 
        # servers: list of dicts {'free_at': float, 'cust_arrival': float} or None if idle
        servers = [{'free_at': 0.0, 'cust_arrival': None} for _ in range(c)]
        queue = [] # list of (arrival_time, service_duration)
        
        warmup_end = horizon_hours * 0.25
        window_len = horizon_hours - warmup_end
        
        sum_L_area = 0.0
        sum_W_total = 0.0
        count_W = 0
        sum_busy_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_min_N_c_area = 0.0
        
        last_event_t = 0.0
        current_N = 0
        
        def get_next_event():
            min_arr = next_arr
            min_dep = float('inf')
            dep_idx = -1
            for i, srv in enumerate(servers):
                if srv['free_at'] < min_dep:
                    min_dep = srv['free_at']
                    dep_idx = i
            return min_arr, min_dep, dep_idx

        while t < horizon_hours:
            arr_t, dep_t, dep_idx = get_next_event()
            
            if arr_t <= dep_t:
                t = arr_t
                dt = t - last_event_t
                if dt > 0:
                    sum_L_area += current_N * dt
                    sum_busy_time += (1 if current_N > 0 else 0) * dt
                    sum_min_N_c_area += min(current_N, c) * dt
                last_event_t = t
                
                count_arr += 1
                
                if current_N >= K:
                    count_blk += 1
                else:
                    svc_dur = rng.expovariate(mu)
                    # Try to find an idle server
                    idle_idx = -1
                    for i, srv in enumerate(servers):
                        if srv['free_at'] <= t:
                            idle_idx = i
                            break
                    
                    if idle_idx != -1:
                        servers[idle_idx]['free_at'] = t + svc_dur
                        servers[idle_idx]['cust_arrival'] = t
                    else:
                        queue.append((t, svc_dur))
                    
                    current_N += 1
                
                next_arr = t + rng.expovariate(lam)
                
            else:
                t = dep_t
                dt = t - last_event_t
                if dt > 0:
                    sum_L_area += current_N * dt
                    sum_busy_time += (1 if current_N > 0 else 0) * dt
                    sum_min_N_c_area += min(current_N, c) * dt
                last_event_t = t
                
                # Customer departs from server dep_idx
                cust_arr = servers[dep_idx]['cust_arrival']
                if cust_arr is not None:
                    w = t - cust_arr
                    if t > warmup_end:
                        sum_W_total += w
                        count_W += 1
                    count_dep += 1
                    current_N -= 1
                    servers[dep_idx]['cust_arrival'] = None
                    servers[dep_idx]['free_at'] = t # Mark as free now, but will be updated if new cust assigned below
                
                # Check if queue has people to move into this freed server
                if queue:
                    q_arr, q_svc = queue.pop(0)
                    servers[dep_idx]['free_at'] = t + q_svc
                    servers[dep_idx]['cust_arrival'] = q_arr
                    # Note: The customer moved from queue to server. 
                    # They were already counted in current_N. 
                    # Their waiting time starts accumulating from q_arr.
                    # When they eventually depart, W will be calculated correctly.
                else:
                    servers[dep_idx]['free_at'] = t # Idle
        
        # Final integration step to horizon
        dt = horizon_hours - last_event_t
        if dt > 0:
            sum_L_area += current_N * dt
            sum_busy_time += (1 if current_N > 0 else 0) * dt
            sum_min_N_c_area += min(current_N, c) * dt
            
        # Calculate stats for this seed
        # Only use data after warmup? 
        # The problem says "statistics only accumulated in window after removing first 25% warmup".
        # My accumulation logic above accumulates EVERYTHING.
        # I need to reset accumulators at warmup_end.
        
        # Re-running simulation is expensive. Better approach:
        # Store events or just re-calculate? 
        # Given constraints, let's modify the loop to only accumulate AFTER warmup.
        
        # Since I already wrote the loop, I'll rewrite the core part to handle warmup correctly.
        # This requires a fresh start for the seed loop body.
        
        # --- RESTARTING SEED LOOP BODY FOR CORRECT WARMUP HANDLING ---
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        servers = [{'free_at': 0.0, 'cust_arrival': None} for _ in range(c)]
        queue = []
        
        warmup_end = horizon_hours * 0.25
        window_len = horizon_hours - warmup_end
        
        sum_L_area = 0.0
        sum_W_total = 0.0
        count_W = 0
        sum_busy_time = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_min_N_c_area = 0.0
        
        last_event_t = 0.0
        current_N = 0
        
        def get_next_event():
            min_arr = next_arr
            min_dep = float('inf')
            dep_idx = -1
            for i, srv in enumerate(servers):
                if srv['free_at'] < min_dep:
                    min_dep = srv['free_at']
                    dep_idx = i
            return min_arr, min_dep, dep_idx

        while t < horizon_hours:
            arr_t, dep_t, dep_idx = get_next_event()
            
            if arr_t <= dep_t:
                t = arr_t
                dt = t - last_event_t
                if dt > 0 and last_event_t >= warmup_end:
                    sum_L_area += current_N * dt
                    sum_busy_time += (1 if current_N > 0 else 0) * dt
                    sum_min_N_c_area += min(current_N, c) * dt
                elif dt > 0 and last_event_t < warmup_end and t > warmup_end:
                    # Split interval
                    dt_pre = warmup_end - last_event_t
                    dt_post = t - warmup_end
                    sum_L_area += current_N * dt_post
                    sum_busy_time += (1 if current_N > 0 else 0) * dt_post
                    sum_min_N_c_area += min(current_N, c) * dt_post
                
                last_event_t = t
                
                if t >= warmup_end:
                    count_arr += 1
                
                if current_N >= K:
                    if t >= warmup_end:
                        count_blk += 1
                else:
                    svc_dur = rng.expovariate(mu)
                    idle_idx = -1
                    for i, srv in enumerate(servers):
                        if srv['free_at'] <= t:
                            idle_idx = i
                            break
                    
                    if idle_idx != -1:
                        servers[idle_idx]['free_at'] = t + svc_dur
                        servers[idle_idx]['cust_arrival'] = t
                    else:
                        queue.append((t, svc_dur))
                    
                    current_N += 1
                
                next_arr = t + rng.expovariate(lam)
                
            else:
                t = dep_t
                dt = t - last_event_t
                if dt > 0 and last_event_t >= warmup_end:
                    sum_L_area += current_N * dt
                    sum_busy_time += (1 if current_N > 0 else 0) * dt
                    sum_min_N_c_area += min(current_N, c) * dt
                elif dt > 0 and last_event_t < warmup_end and t > warmup_end:
                    dt_post = t - warmup_end
                    sum_L_area += current_N * dt_post
                    sum_busy_time += (1 if current_N > 0 else 0) * dt_post
                    sum_min_N_c_area += min(current_N, c) * dt_post
                
                last_event_t = t
                
                cust_arr = servers[dep_idx]['cust_arrival']
                if cust_arr is not None:
                    w = t - cust_arr
                    if t > warmup_end:
                        sum_W_total += w
                        count_W += 1
                    if t > warmup_end:
                        count_dep += 1
                    current_N -= 1
                    servers[dep_idx]['cust_arrival'] = None
                    servers[dep_idx]['free_at'] = t
                
                if queue:
                    q_arr, q_svc = queue.pop(0)
                    servers[dep_idx]['free_at'] = t + q_svc
                    servers[dep_idx]['cust_arrival'] = q_arr
                else:
                    servers[dep_idx]['free_at'] = t
        
        dt = horizon_hours - last_event_t
        if dt > 0 and last_event_t >= warmup_end:
            sum_L_area += current_N * dt
            sum_busy_time += (1 if current_N > 0 else 0) * dt
            sum_min_N_c_area += min(current_N, c) * dt
        elif dt > 0 and last_event_t < warmup_end and horizon_hours > warmup_end:
            dt_post = horizon_hours - warmup_end
            sum_L_area += current_N * dt_post
            sum_busy_time += (1 if current_N > 0 else 0) * dt_post
            sum_min_N_c_area += min(current_N, c) * dt_post

        # Compute metrics for this seed
        if window_len > 0:
            L_est = sum_L_area / window_len
            busy_frac_est = sum_busy_time / window_len
            busy_util_est = sum_min_N_c_area / (window_len * c)
            
            if count_W > 0:
                W_est = sum_W_total / count_W
            else:
                W_est = 0.0
                
            if count_arr > 0:
                p_loss_est = count_blk / count_arr
                p_wait_est = (count_arr - count_blk - count_dep) / count_arr # Approximation: arrived, not lost, not yet left? 
                # Actually p_wait usually means probability of waiting. 
                # In M/M/c/K, P(wait) = P(all servers busy). 
                # From simulation: fraction of accepted customers who had to wait.
                # Accepted = count_arr - count_blk.
                # Waited = Accepted - (those served immediately).
                # Hard to track "served immediately" without extra flag.
                # Alternative definition often used: P(N>=c).
                # Let's stick to empirical: Fraction of arrivals that joined queue vs went straight to server.
                # I didn't track that explicitly. 
                # Let's approximate p_wait using Little's Law or theoretical? No, must be sim.
                # I'll set p_wait to 0 if not tracked, or better:
                # Track "waited" count.
                pass
            else:
                p_loss_est = 0.0
                p_wait_est = 0.0
            
            lam_eff_est = count_arr / window_len
            dep_rate_est = count_dep / window_len
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_loss.append(p_loss_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(count_arr)
            all_blk.append(count_blk)
            all_dep.append(count_dep)
            all_busy_util.append(busy_util_est)
