import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in hours and minutes
    lam_base = 8.0  # per hour
    mu_base = 60.0 / 12.0  # per hour (mean service time 12 min)
    c = 2
    K = 4  # max capacity including service
    
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

    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    results_busy_util = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Queue holds tuples: (arrival_time, service_duration)
        queue = [] 
        # Servers hold completion times or None
        servers = [None] * c
        
        # Statistics accumulators (for area integrals and counts)
        warmup_end = H * 0.25
        total_area_N = 0.0
        total_area_busy = 0.0 # Time where at least one server is busy? No, busy_frac defined as station not empty (N>0).
        # Re-reading requirement: "busy_frac ... = 站不空的时间比例 1−π₀". So integral of indicator(N(t)>0).
        # busy_util = E[min(N,c)]/c. Integral of min(N(t), c)/c.
        
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0 # Sum of waiting times (time in system? Usually W is time in system. Let's assume W = sojourn time.)
        # Wait, standard notation: W often means waiting time in queue, but in simple M/M/c/K contexts without explicit distinction, and given "throughput time" is mentioned, usually W refers to system time unless specified as Wq. However, the prompt asks for W (minutes). In many textbook examples for toll booths, W is time spent in the system. Let's calculate System Time. If it meant queue wait, it would likely say Wq. Given "passing through time", let's stick to System Time.
        # Actually, let's look at L and W relationship. Little's Law L = lambda_eff * W. If W is system time, L is avg number in system. This matches.
        
        prev_t = 0.0
        
        while t < H:
            # Determine next event time
            events = []
            if next_arrival <= H:
                events.append(('arr', next_arrival))
            
            for j in range(c):
                if servers[j] is not None and servers[j] <= H:
                    events.append(('dep', servers[j], j))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            event_type, event_time = events[0][0], events[0][1]
            idx_server = events[0][2] if len(events[0]) > 2 else -1
            
            dt = event_time - prev_t
            
            # Integrate statistics over dt if we are past warmup
            if prev_t >= warmup_end:
                n_curr = len(queue) + sum(1 for s in servers if s is not None)
                total_area_N += n_curr * dt
                if n_curr > 0:
                    total_area_busy += dt
                
                # For busy_util: integral of min(n, c)/c
                util_val = min(n_curr, c) / c
                # We need to accumulate this separately or compute from total_area_N? 
                # No, total_area_N is integral of N. We need integral of min(N,c).
                # Let's add another accumulator.
                
            # Update global accumulators for utilization specifically
            if prev_t >= warmup_end:
                n_curr = len(queue) + sum(1 for s in servers if s is not None)
                # Accumulate for busy_util
                # We'll store this in a separate variable later or just compute here.
                pass 

            # Process Event
            t = event_time
            prev_t = t
            
            if event_type == 'arr':
                count_arr += 1
                n_curr = len(queue) + sum(1 for s in servers if s is not None)
                
                if n_curr < K:
                    # Accept vehicle
                    svc_dur = rng.expovariate(mu)
                    # Find free server
                    free_idx = -1
                    for j in range(c):
                        if servers[j] is None:
                            free_idx = j
                            break
                    
                    if free_idx != -1:
                        servers[free_idx] = t + svc_dur
                        # Store arrival time for W calculation upon departure
                        # We need to track which customer is on which server.
                        # Since we don't have IDs, we can push (arrival_time, svc_dur) to a list associated with server?
                        # Better: When departing, we know the start time was when it entered service.
                        # But we need the original arrival time.
                        # Let's maintain a list of customers in system: (arrival_time, status, start_service_time, end_service_time)
                        # Simpler approach for discrete event:
                        # On arrival: create record. If goes to server, mark server with record. If queue, append to queue.
                        # On departure: retrieve record from server, calculate W = t - arrival_time.
                        
                        # Refactor state:
                        # servers[j] stores (completion_time, arrival_time) or None
                        # queue stores (arrival_time, service_duration)
                        
                        # Correction: Service duration is drawn at arrival.
                        # If going to server:
                        servers[free_idx] = (t + svc_dur, t) # (end_time, arrival_time)
                    else:
                        # Must be queued since n_curr < K implies space exists but maybe all servers busy?
                        # If n_curr < K, there is space. If no free server, it must go to queue.
                        queue.append((t, svc_dur))
                else:
                    count_blk += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'dep':
                j = idx_server
                comp_time, arr_time = servers[j]
                servers[j] = None
                count_dep += 1
                
                w_sys = t - arr_time
                if t >= warmup_end:
                    sum_W += w_sys
                
                # Check if queue has someone to move to this server
                if queue:
                    q_arr, q_svc = queue.pop(0)
                    servers[j] = (t + q_svc, q_arr)
                    
        # End of simulation loop for this seed
        
        # Calculate final stats for this seed based on window [warmup_end, H]
        win_len = H - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        # Recalculate areas properly because I skipped some logic in the loop above for brevity/clarity
        # The loop above had placeholders. Let's re-run the integration logic correctly inside the loop structure.
        # Since I cannot easily refactor the loop now without rewriting the whole block, I will implement the integration correctly in the code below.
        
        # Resetting for correct implementation in the final code block:
        # I will rewrite the inner loop logic in the final output to ensure correctness.
        
        # Placeholder values to avoid syntax error in thought process, actual logic follows in code.
        L_est = total_area_N / win_len
        busy_frac_est = total_area_busy / win_len
        p_loss_est = count_blk / count_arr if count_arr > 0 else 0
        p_wait_est = 0 # Need to track those who waited vs total accepted? Or queue wait?
        # Prompt asks for p_wait. Usually probability that an arriving customer has to wait.
        # I didn't track that. I need to add a counter for arrivals that went to queue.
        
        # Busy Util: E[min(N,c)]/c. Need integral of min(N,c).
        
        # Let's restart the seed loop logic mentally to ensure all counters are present.
        
        # Counters needed:
        # count_arr_total (in window)
        # count_blk_total (in window)
        # count_dep_total (in window)
        # count_wait_total (arrivals in window that joined queue)
        # sum_W_total (system time for departures in window)
        # area_N (integral of N)
        # area_busy (integral of 1_{N>0})
        # area_min_N_c (integral of min(N,c))
        
        # Note: Events crossing the boundary. Standard practice: only count events fully within window or use time-weighted.
        # Simplest: Only integrate during intervals where t >= warmup_end.
        # Counts: Only increment if event_time >= warmup_end.
        
        # Finalizing calculations for this seed:
        # L = area_N / win_len
        # W = sum_W / count_dep (if count_dep > 0)
        # busy_frac = area_busy / win_len
        # p_loss = count_blk / count_arr
        # p_wait = count_wait / count_arr
        # busy_util = area_min_N_c / (win_len * c)
        
        # Append to lists...
        
        # Since I am generating the code directly, I will write the robust version now.
        
        # Clear previous partial thoughts and write clean code.
        pass

    # Aggregation
    seeds_used = N_seeds
    avg_L = sum(results_L) / seeds_used
    avg_W = sum(results_W) / seeds_used
    avg_busy_frac = sum(results_busy_frac) / seeds_used
    avg_p_loss = sum(results_p_loss) / seeds_used
    avg_p_wait = sum(results_p_wait) / seeds_used
    avg_arr = sum(results_arr) / seeds_used
    avg_blk = sum(results_blk) / seeds_used
    avg_dep = sum(results_dep) / seeds_used
    avg_busy_util = sum(results_busy_util) / seeds_used
    
    dep_rate = avg_dep / (H - H*0.25) * 60.0 # Per hour? H is in hours. Window is in hours. Rate = Deps / Hours.
    # Wait, H is horizon in time_unit. If time_unit is hour, then rate is per hour.
    # Prompt says "dep_rate is '个/每小时'".
    # If my internal time is hours, then dep_rate = avg_dep / win_hours.
    
    lam_eff = avg_arr / (H - H*0.25) # Arrivals per hour in window
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_loss": round(avg_p_loss, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(H - H*0.25, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in results_L],
        "per_seed_W": [round(x, 4) for x in results_W],
        "per_seed_busy_frac": [round(x, 4) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in results_p_wait]
    }
    print(json.dumps(out))

# The above thought process identified missing counters. I will now generate the complete, corrected Python code.
