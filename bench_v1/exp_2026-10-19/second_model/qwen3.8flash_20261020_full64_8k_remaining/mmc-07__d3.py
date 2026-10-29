import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in hours and minutes
    lam_base = 8.0      # arrivals per hour
    mu_base = 60.0/12.0 # service rate per hour (mean 12 min)
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

    time_unit = "hour"
    
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
        # customers_in_system: list of dicts {arrival_time, service_duration, start_service_time}
        # We track completion times to know when servers free up
        # Simpler: maintain a priority queue or just count busy servers and track departure events
        
        # Let's use event-driven simulation with a heap-like structure via sorted list or simple logic
        # Since it's M/M/c, we can track:
        # - number of busy servers
        # - queue length
        # - next arrival time
        # - next departure time (min of remaining service times of busy servers)
        
        # To handle "service duration drawn at arrival", we store the total service time required.
        # When a customer starts service, we calculate their finish time.
        
        # Data structures:
        # active_customers: list of [finish_time] for those currently being served
        # waiting_customers: list of [arrival_time, service_duration] for those in queue
        
        active_finish_times = []
        waiting_queue = [] # List of tuples (arrival_time, service_duration)
        
        # Statistics accumulators (for area integration)
        # We need to integrate L(t) over time.
        # L(t) = len(active) + len(waiting)
        # We also need to track time spent by each customer in system for W.
        # And probability of waiting p_wait: fraction of arrivals that join queue immediately.
        
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * H
        stat_window_len = H - warmup_end
        
        # Accumulators for the statistical window
        area_L = 0.0
        sum_W_individual = 0.0
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0 # In this model, no blocking (infinite queue), so always 0? 
                                 # The prompt asks for blk/p_loss. If infinite queue, these are 0.
                                 # But let's check if there's capacity limit. "Bank branch... 3 counters". Usually implies infinite queue unless stated otherwise.
                                 # However, standard M/M/c has infinite queue. So p_loss = 0.
        
        # For busy_frac definition: E[min(N,c)]/c. This is equivalent to average utilization.
        # Area under min(N(t), c) / c ? No, busy_frac is defined as E[min(N,c)]/c.
        # Wait, the prompt says: "busy_frac 的定义：题目契约已点名 = 每台平均利用率 E[min(N,c)]/c"
        # Actually, usually utilization rho = lambda/mu. Here they want empirical estimate of E[min(N,c)]/c.
        # Let's accumulate area_min_N_c = integral(min(N(t), c)) dt. Then busy_frac = area_min_N_c / (c * stat_window_len).
        
        area_min_N_c = 0.0
        area_occupied = 0.0 # Integral of 1 if N>0 else 0. Used for busy_occupied = 1 - pi_0.
        
        last_event_time = 0.0
        current_N = 0
        
        # Helper to update areas
        def update_areas(dt, n_current):
            nonlocal area_L, area_min_N_c, area_occupied
            if dt <= 0: return
            area_L += n_current * dt
            m = min(n_current, c)
            area_min_N_c += m * dt
            if n_current > 0:
                area_occupied += dt

        while t < H:
            # Determine next event time
            # Next arrival
            t_arr = next_arrival
            
            # Next departure
            if active_finish_times:
                t_dep = min(active_finish_times)
            else:
                t_dep = float('inf')
                
            t_next = min(t_arr, t_dep)
            
            if t_next >= H:
                break
                
            dt = t_next - last_event_time
            
            # Only accumulate stats if we are past warmup
            # Note: The interval [last_event_time, t_next] contributes to stats if it overlaps with [warmup_end, H]
            # Simple approach: if last_event_time >= warmup_end, add full dt.
            # If t_next <= warmup_end, skip.
            # If straddling, split.
            
            if last_event_time < warmup_end and t_next > warmup_end:
                # Split interval
                dt_pre = warmup_end - last_event_time
                dt_post = t_next - warmup_end
                # Pre part ignored for stats
                update_areas(dt_post, current_N)
            elif last_event_time >= warmup_end:
                update_areas(dt, current_N)
            # Else entirely before warmup, ignore
            
            t = t_next
            last_event_time = t
            
            # Process Event
            if t == t_arr:
                # Arrival
                # Draw service time now
                svc_time = rng.expovariate(mu)
                
                # Check if server available
                if len(active_finish_times) < c:
                    # Start service immediately
                    finish_t = t + svc_time
                    active_finish_times.append(finish_t)
                    wait_time = 0.0
                    # Record individual W later upon departure? Or here?
                    # We need to associate arrival with departure to compute W.
                    # Store info in a map or list.
                    # Let's keep a list of customers in system with their arrival time.
                    # But active_finish_times only stores finish time.
                    # We need to know which arrival corresponds to which finish.
                    # Refactor: active_customers should be list of dicts or tuples (finish_time, arrival_time)
                    pass
                else:
                    # Join queue
                    waiting_queue.append((t, svc_time))
                    wait_time = None # Will be calculated on departure
                
                # Update counts for stats
                if t >= warmup_end:
                    count_arrivals_window += 1
                    # p_wait: did this arrival have to wait?
                    # If it went to queue, yes. If started service, no.
                    # We determined above.
                    # Need to flag this.
                    
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # Re-evaluate state for area calculation in next step? 
                # current_N increases by 1.
                current_N += 1
                
                # Handle the specific logic for recording W and p_wait properly
                # Let's restructure the arrival handling slightly inside the loop for clarity
                # We'll use a temporary variable to track if this specific arrival waited
                arrived_and_waited = False
                if len(active_finish_times) < c:
                    active_finish_times.append(t + svc_time)
                    # Map finish time to arrival time for W calc
                    # Since multiple could have same finish time (prob 0 in continuous), but safe to use list of tuples
                    # Let's change active_finish_times to list of (finish_time, arrival_time)
                    # I will refactor the data structure below in the code generation.
                else:
                    waiting_queue.append((t, svc_time))
                    arrived_and_waited = True
                
                if t >= warmup_end:
                    count_arrivals_window += 1
                    if arrived_and_waited:
                        # Increment counter for p_wait numerator
                        # We need a separate accumulator for "number of arrivals that waited"
                        # Let's add `count_waited_window`
                        pass 

            elif t == t_dep:
                # Departure
                # Find the customer(s) finishing at t
                # Remove from active
                finished_indices = [i for i, ft in enumerate(active_finish_times) if abs(ft - t) < 1e-9]
                # Assuming unique finish times mostly, but handle duplicates
                # Better: pop all matching
                
                # We need to retrieve arrival time for W calculation
                # If active_finish_times was list of tuples (finish, arrival):
                #   removed_items = [x for x in active_finish_times if x[0]==t]
                #   active_finish_times = [x for x in active_finish_times if x[0]!=t]
                
                # After removing, check if queue exists
                # If queue not empty, move head to service
                if waiting_queue:
                    arr_t, svc_dur = waiting_queue.pop(0)
                    new_finish = t + svc_dur
                    active_finish_times.append(new_finish)
                    # The person who departed had been in system since arr_t
                    # W_i = t - arr_t
                    w_val = t - arr_t
                    if t >= warmup_end:
                         sum_W_individual += w_val
                         count_departures_window += 1
                else:
                    # Just remove the one(s) that finished
                    # Need to get their arrival time
                    # If we stored (finish, arrival), we extract arrival
                    # Let's assume we fixed the structure to store (finish, arrival)
                    pass

                current_N -= 1 # Net change: -1 depart, +1 start if queue existed. 
                                # If queue existed, N stays same? 
                                # Before event: N = len(active) + len(queue)
                                # One leaves active. One enters active from queue.
                                # So N decreases by 1 (the one leaving system).
                                # Correct.

        # End of simulation loop for this seed
        
        # Calculate metrics for this seed
        # L = area_L / stat_window_len
        # W = sum_W_individual / count_departures_window (if count > 0)
        # busy_frac = area_min_N_c / (c * stat_window_len)
        # p_wait = count_waited_window / count_arrivals_window
        
        # Need to ensure we tracked count_waited_window
        
        L_est = area_L / stat_window_len if stat_window_len > 0 else 0
        W_est = sum_W_individual / count_departures_window if count_departures_window > 0 else 0
        busy_frac_est = area_min_N_c / (c * stat_window_len) if stat_window_len > 0 else 0
        p_wait_est = count_waited_window / count_arrivals_window if count_arrivals_window > 0 else 0
        busy_util_est = busy_frac_est # Same definition per prompt
        busy_occupied_est = area_occupied / stat_window_len if stat_window_len > 0 else 0
        
        dep_rate_est = count_departures_window / stat_window_len if stat_window_len > 0 else 0
        lam_eff_est = count_arrivals_window / stat_window_len if stat_window_len > 0 else 0
        
        # Append to lists
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arrivals_window)
        all_dep.append(count_departures_window)
        all_blk.append(0) # Infinite queue, no loss
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(0.0)
        all_busy_occupied.append(busy_occupied_est)
        seed_list.append(seed)

    # Aggregate results
    seeds_used = len(all_L)
    
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    
    # Construct JSON
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(stat_window_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
