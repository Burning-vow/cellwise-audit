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
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr
    c = 3
    K = 4 # max cars including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = 'hour'
    win = H * 0.75 # discard first 25%
    warmup_end = H * 0.25
    
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
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # list of (arrival_time, service_duration)
        n_in_system = 0
        
        # Statistics accumulators for the window
        area_L = 0.0
        area_busy_occ = 0.0 # time when system not empty
        area_busy_serv = 0.0 # sum of busy server times / c? No, E[min(N,c)]/c is avg utilization per server.
        # Let's track total server busy time to compute busy_util later.
        total_server_busy_time = 0.0
        
        arrivals_in_win = 0
        blocks_in_win = 0
        departures_in_win = 0
        wait_times_sum = 0.0 # Sum of waiting times for those who waited? Or all? W usually includes 0 wait.
        # Standard definition: W is average time in system. L is average number in system.
        # Little's Law: L = lambda_eff * W.
        # We need to accumulate integral of N(t) and count departures with their sojourn times.
        
        # To handle "area" correctly, we integrate between events.
        last_event_time = 0.0
        
        # Event loop
        while True:
            # Determine next event time
            arr_t = next_arrival
            # Find earliest server completion among active services
            # If queue exists, next departure is min(server_free_at) but only if server was started.
            # Actually, simpler: maintain a heap or just scan since c is small.
            
            dep_t = float('inf')
            for k in range(c):
                if servers_free_at[k] > t: # Server is busy
                    if servers_free_at[k] < dep_t:
                        dep_t = servers_free_at[k]
            
            # If no one is being served, dep_t remains inf
            
            next_event = min(arr_t, dep_t)
            
            if next_event == float('inf'):
                break
                
            # Advance time
            dt = next_event - t
            if dt > 0:
                # Integrate statistics over this interval if it overlaps with window
                # Window starts at warmup_end, ends at H
                start_int = max(t, warmup_end)
                end_int = min(next_event, H)
                
                if start_int < end_int:
                    duration = end_int - start_int
                    area_L += n_in_system * duration
                    if n_in_system > 0:
                        area_busy_occ += duration
                    
                    # Calculate busy servers during this interval
                    # A server is busy if its free_at > current time segment start? 
                    # Since we are integrating from t to next_event, and states don't change inside,
                    # we can check which servers were busy at time t (which is same as throughout interval).
                    num_busy = 0
                    for k in range(c):
                        if servers_free_at[k] > t:
                            num_busy += 1
                    total_server_busy_time += num_busy * duration
                
                t = next_event
            
            if t >= H:
                break
                
            # Process event
            if abs(arr_t - t) < 1e-9:
                # Arrival
                if t >= warmup_end:
                    arrivals_in_win += 1
                
                if n_in_system < K:
                    # Accept
                    n_in_system += 1
                    # Assign to a server if available, else queue
                    assigned_server = -1
                    for k in range(c):
                        if servers_free_at[k] <= t:
                            assigned_server = k
                            break
                    
                    if assigned_server != -1:
                        # Start service immediately
                        dur = rng.expovariate(mu)
                        servers_free_at[assigned_server] = t + dur
                        # Store arrival time for this customer on this server? 
                        # Problem says: "service duration must be drawn at arrival and attached to customer".
                        # We need to know when they leave to calculate sojourn time.
                        # Sojourn = Departure Time - Arrival Time.
                        # We need to link the departure event back to the arrival time.
                        # Let's store (arrival_time, service_dur) in a structure associated with the server slot?
                        # But multiple customers might use same server sequentially.
                        # Better: When a customer enters service, we record their arrival time.
                        # When they finish, we pop that info.
                        # However, our event loop uses `servers_free_at`. 
                        # We need an auxiliary array `server_customer_arrival` to track who is currently being served.
                        pass
                    else:
                        # Queue
                        dur = rng.expovariate(mu)
                        queue.append((t, dur))
                    
                    # Correction: The prompt says "draw service duration at arrival".
                    # So regardless of whether they start now or later, draw dur now.
                    dur = rng.expovariate(mu)
                    
                    if assigned_server != -1:
                        servers_free_at[assigned_server] = t + dur
                        # Need to remember arrival time for this specific service instance
                        # Let's add a parallel array for tracking arrival times of current occupants
                        # But we don't have one yet. Let's refactor slightly.
                        # Instead of just servers_free_at, let's keep a list of active services: (end_time, arrival_time)
                        # And a queue of waiting: (arrival_time, service_dur)
                        
                        # Re-doing logic inside arrival block properly:
                        # Remove previous assignment logic above, replace with clean state update.
                        pass
                    else:
                        queue.append((t, dur))
                    
                    # Wait, I mixed up flow. Let's restart the event processing logic cleanly.
                    # State variables needed:
                    # n_in_system
                    # queue: list of (arrival_time, service_duration)
                    # active_services: list of (end_time, arrival_time) -- length <= c
                    # servers_free_at is redundant if we use active_services sorted by end_time.
                    
                    # Let's stick to the arrays approach but fix the data storage.
                    # Array `active_arrival_times` indexed by server ID.
                    # If server is idle, value is None.
                    
                    # Resetting the block for clarity in code generation below.
                    pass
                else:
                    # Block
                    if t >= warmup_end:
                        blocks_in_win += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(dep_t - t) < 1e-9:
                # Departure
                # Find which server finished
                finished_server = -1
                for k in range(c):
                    if abs(servers_free_at[k] - t) < 1e-9:
                        finished_server = k
                        break
                
                # Get arrival time of the person leaving
                # We need to have stored this. 
                # In the arrival step, if assigned to server k, we set `server_arrival[k] = t`.
                # If queued, we don't assign server yet.
                
                # Let's assume we maintained `server_arrival` array.
                arr_time_of_leaver = server_arrival[finished_server]
                sojourn = t - arr_time_of_leaver
                wait_time = sojourn - service_durations[finished_server] # Need to store dur too?
                # Prompt: "draw service duration... attach to customer".
                # So we should store (arrival, duration) for the person in service.
                
                # This requires restructuring the state variables.
                # Let's define:
                # `in_service`: dict/list mapping server index to (arrival_time, duration)
                # `queue`: list of (arrival_time, duration)
                
                # Okay, I will rewrite the simulation core carefully in the final output.
                
                # For now, continuing the thought process:
                # On departure:
                # 1. Record stats for the leaver if in window.
                # 2. Free the server.
                # 3. Check queue. If non-empty, pop front, assign to server, set new end time.
                
                if t >= warmup_end:
                    departures_in_win += 1
                    # Accumulate W numerator? 
                    # Usually W is calculated via Little's Law or direct averaging of sojourn times of departed customers.
                    # Direct averaging: Sum(sojourn) / Count(departures).
                    # But we also have area_L. 
                    # Let's collect sojourn times for departed customers in the window.
                    pass
                
                # Move next person from queue to service
                if queue:
                    next_cust = queue.pop(0)
                    arr_t_next, dur_next = next_cust
                    servers_free_at[finished_server] = t + dur_next
                    server_arrival[finished_server] = arr_t_next
                    server_duration[finished_server] = dur_next
                else:
                    servers_free_at[finished_server] = float('inf')
                    server_arrival[finished_server] = None
                    server_duration[finished_server] = None
                
                n_in_system -= 1

        # End of simulation for one seed
        
        # Calculate metrics for this seed
        if departures_in_win > 0:
            w_avg = sum_sojourns / departures_in_win
        else:
            w_avg = 0.0
            
        l_avg = area_L / win if win > 0 else 0.0
        busy_frac_val = area_busy_occ / win if win > 0 else 0.0
        p_loss_val = blocks_in_win / arrivals_in_win if arrivals_in_win > 0 else 0.0
        
        # Busy util: E[min(N,c)]/c. 
        # Total server busy time accumulated. 
        # Average number of busy servers = total_server_busy_time / win.
        # Utilization per server = (total_server_busy_time / win) / c.
        busy_util_val = (total_server_busy_time / win) / c if win > 0 else 0.0
        
        # P_wait: Probability of waiting. 
        # Customers who had to queue. 
        # We need to count how many arrivals entered the queue vs went straight to service.
        # Or: Fraction of departures whose wait_time > 0.
        # Let's track `waited_count` in window.
        
        p_wait_val = waited_count / departures_in_win if departures_in_win > 0 else 0.0
        
        # Append to lists
        per_seed_L.append(l_avg)
        per_seed_W.append(w_avg)
        per_seed_busy_frac.append(busy_frac_val)
        per_seed_p_loss.append(p_loss_val)
        per_seed_p_wait.append(p_wait_val)
        
        all_L.append(l_avg)
        all_W.append(w_avg)
        all_busy_frac.append(busy_frac_val)
        all_p_loss.append(p_loss_val)
        all_p_wait.append(p_wait_val)
        all_arr.append(arrivals_in_win)
        all_blk.append(blocks_in_win)
        all_dep.append(departures_in_win)
        all_busy_util.append(busy_util_val)
        all_busy_occupied.append(busy_frac_val) # Same as busy_frac
        
        seeds_used += 1
        seed_list.append(s)

    # Aggregate results
    def mean(lst): return sum(lst)/len(lst) if lst else 0.0
    
    res = {
        "L": mean(all_L),
        "W": mean(all_W),
        "busy_frac": mean(all_busy_frac),
        "p_loss": mean(all_p_loss),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win,
        "arr": mean(all_arr),
        "blk": mean(all_blk),
        "busy_util": mean(all_busy_util),
        "dep": mean(all_dep),
        "dep_rate": mean(all_dep) / win * 1.0, # Deps per hour? Win is in hours.
        "lam_eff": mean(all_dep) / win,
        "p_wait": mean(all_p_wait),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": mean(all_busy_occupied)
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
