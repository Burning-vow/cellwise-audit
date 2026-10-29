import sys, json, random, math
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            val = sys.argv[i+1] if i+1 < len(sys.argv) else None
            args[key] = val
            i += 2
        else:
            i += 1
    
    N = int(args.get('seeds', 10))
    H = float(args.get('horizon', 100.0))
    S_start = int(args.get('seed-start', 1))
    pert = args.get('pert', 'none')
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 5.0 # 1/12 min = 5 per hour
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
    horizon_hours = H
    
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
    
    for s_idx in range(N):
        seed_val = S_start + s_idx
        rng = random.Random(seed_val)
        
        # State variables
        t = 0.0
        n_in_system = 0
        service_end_times = [] # List of end times for currently served cars
        queue = deque() # Cars waiting to be served (arrival time stored)
        
        # Statistics accumulators (for area integration and counts)
        # We need to track the state over time to compute L (average number in system)
        # and W (average waiting time).
        # Since it's a discrete event simulation, we can integrate L by tracking 
        # the duration each state was held.
        
        # To handle warm-up (first 25%), we record events or use a simpler approach:
        # Run until 0.75*H, then start collecting stats until H.
        # However, standard DES usually collects from start. The prompt says:
        # "统计量只在去掉前 25% 预热后的窗口内累计"
        # This implies we should discard data from [0, 0.25*H].
        # But "面积型量必须在改变状态之前积分".
        
        # Let's implement a loop that processes events.
        # Events: Arrival, Departure.
        
        # Generate initial arrival
        next_arrival_time = rng.expovariate(lam)
        
        # We need to store history to calculate averages correctly after warmup?
        # Or just reset counters at warmup point?
        # Resetting counters is tricky because ongoing services started before warmup.
        # Better approach: Simulate full horizon, but only accumulate stats when t >= warmup_threshold.
        # For L (time-average), we integrate n_in_system * dt only if the interval overlaps with [warmup, H].
        # For W (customer average), we only count customers who completed service after warmup? 
        # Or customers who arrived after warmup? Usually, steady-state estimates exclude transient effects.
        # Common practice: Discard first 25% of observations.
        # For time-weighted metrics (L, busy_frac), integrate over [0.25H, H].
        # For customer-weighted metrics (W, p_loss, p_wait), consider customers whose service completion 
        # falls within [0.25H, H]? Or arrivals? 
        # Let's assume: 
        # - L, busy_frac: Time integral over [T_warm, T_end].
        # - W: Average sojourn time of customers who DEPARTED during [T_warm, T_end].
        # - p_loss: Proportion of ARRIVALS during [T_warm, T_end] that were blocked.
        # - p_wait: Proportion of ARRIVALS during [T_warm, T_end] that had to wait (queue > 0 upon arrival).
        
        T_warm = 0.25 * horizon_hours
        T_end = horizon_hours
        
        # Accumulators for the window [T_warm, T_end]
        sum_L_area = 0.0
        sum_busy_area = 0.0 # Time where n_in_system > 0
        sum_occupied_area = 0.0 # Time where n_in_system > 0 (same as busy for station not empty?)
        # Prompt: busy_frac = 1 - pi_0 = P(N>0). So yes, same as above.
        # busy_util = E[min(N,c)]/c. Need to integrate min(n,c).
        sum_min_nc_area = 0.0
        
        count_arrivals_window = 0
        count_blocked_window = 0
        count_waited_window = 0
        count_departures_window = 0
        sum_sojourn_time_window = 0.0
        
        # Event loop
        # We need to know the last event time to calculate durations.
        last_event_time = 0.0
        
        # Helper to add area contribution
        def add_areas(t_start, t_end, n_current):
            nonlocal sum_L_area, sum_busy_area, sum_min_nc_area
            
            # Clip to window
            w_start = max(t_start, T_warm)
            w_end = min(t_end, T_end)
            
            if w_start < w_end:
                dt = w_end - w_start
                sum_L_area += n_current * dt
                if n_current > 0:
                    sum_busy_area += dt
                sum_min_nc_area += min(n_current, c) * dt

        while True:
            # Determine next event time
            next_dep_time = float('inf')
            if service_end_times:
                # Find earliest departure
                # Note: service_end_times might have multiple entries. 
                # In this model, servers are identical. 
                # We can just keep a list of end times.
                next_dep_time = min(service_end_times)
            
            next_evt_time = min(next_arrival_time, next_dep_time)
            
            if next_evt_time > T_end:
                # Process remaining time up to T_end
                add_areas(last_event_time, T_end, n_in_system)
                break
            
            # Advance time and update areas for the previous state
            add_areas(last_event_time, next_evt_time, n_in_system)
            last_event_time = next_evt_time
            
            if next_evt_time == next_arrival_time:
                # Arrival
                if n_in_system < K:
                    # Accept
                    n_in_system += 1
                    
                    # Check if waited
                    if len(queue) > 0 or len(service_end_times) >= c:
                        # If there are people waiting OR all servers busy, this car waits?
                        # Actually, if servers are free, it goes straight to service.
                        # If servers are busy, it joins queue.
                        # Condition for waiting: Upon arrival, if no server is immediately available.
                        # Number of busy servers = len(service_end_times) (assuming we remove finished ones properly)
                        # Wait, service_end_times contains active services.
                        # If len(service_end_times) < c, a server is free.
                        
                        if len(service_end_times) < c:
                            # Server free, start service immediately
                            dur = rng.expovariate(mu)
                            end_t = next_evt_time + dur
                            service_end_times.append(end_t)
                            # Store arrival time for this specific service? 
                            # We need to link arrival to departure to calculate sojourn time.
                            # Let's change structure: service_end_times stores tuples (end_time, arrival_time)
                            # But we used min(). Let's refactor slightly.
                            pass
                        else:
                            # All servers busy, join queue
                            queue.append(next_evt_time) # Store arrival time
                            
                    else:
                         # No servers busy? Impossible if n_in_system increased and n_in_system <= K.
                         # If n_in_system was 0, now 1. Servers busy 0. Free.
                         if len(service_end_times) < c:
                             dur = rng.expovariate(mu)
                             end_t = next_evt_time + dur
                             service_end_times.append((end_t, next_evt_time))
                         else:
                             queue.append(next_evt_time)
                             
                    # Correction on logic above: I mixed up tuple vs float.
                    # Let's restart the arrival logic cleanly.
                    
                    # Re-evaluate:
                    # n_in_system includes those in service AND in queue.
                    # service_end_times holds (end_time, arrival_time) for those IN SERVICE.
                    # queue holds arrival_time for those WAITING.
                    
                    # If we accepted the car:
                    # Is there a free server?
                    num_in_service = len(service_end_times)
                    if num_in_service < c:
                        # Start service
                        dur = rng.expovariate(mu)
                        end_t = next_evt_time + dur
                        service_end_times.append((end_t, next_evt_time))
                        # Did it wait? No, immediate service.
                        waited = False
                    else:
                        # Join queue
                        queue.append(next_evt_time)
                        waited = True
                    
                    # Update stats if in window
                    if next_evt_time >= T_warm:
                        count_arrivals_window += 1
                        if waited:
                            count_waited_window += 1
                            
                    # Schedule next arrival
                    next_arrival_time = next_evt_time + rng.expovariate(lam)
                    
                else:
                    # Blocked
                    if next_evt_time >= T_warm:
                        count_arrivals_window += 1
                        count_blocked_window += 1
                    next_arrival_time = next_evt_time + rng.expovariate(lam)
                    
            elif next_evt_time == next_dep_time:
                # Departure
                # Find which one departed
                # Remove the one with end_time == next_evt_time
                # There might be ties, pick any.
                idx_to_remove = -1
                for i, (et, at) in enumerate(service_end_times):
                    if abs(et - next_evt_time) < 1e-9:
                        idx_to_remove = i
                        break
                
                if idx_to_remove != -1:
                    et, at = service_end_times.pop(idx_to_remove)
                    n_in_system -= 1
                    
                    # Calculate sojourn time
                    sojourn = et - at
                    
                    # If someone is waiting, start their service
                    if queue:
                        arr_time_waiting = queue.popleft()
                        dur = rng.expovariate(mu)
                        new_end_t = next_evt_time + dur
                        service_end_times.append((new_end_t, arr_time_waiting))
                        # Note: The departing car's sojourn is recorded.
                        # The waiting car starts service now.
                    
                    # Update stats if departure happened in window
                    if next_evt_time >= T_warm:
                        count_departures_window += 1
                        sum_sojourn_time_window += sojourn
                        
                else:
                    # Should not happen if logic is correct
                    pass

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        window_len = T_end - T_warm
        
        if window_len > 0:
            avg_L = sum_L_area / window_len
            avg_busy_frac = sum_busy_area / window_len
            avg_busy_util = sum_min_nc_area / (window_len * c)
            
            if count_arrivals_window > 0:
                p_loss = count_blocked_window / count_arrivals_window
                p_wait = count_waited_window / count_arrivals_window
            else:
                p_loss = 0.0
                p_wait = 0.0
                
            if count_departures_window > 0:
                avg_W = sum_sojourn_time_window / count_departures_window
            else:
                avg_W = 0.0
                
            dep_rate = count_departures_window / window_len # per hour
            lam_eff = count_arrivals_window / window_len # per hour (accepted + blocked? No, effective arrival rate into system is accepted ones)
            # Prompt: lam_eff. Usually means rate of customers entering the system.
            # Accepted arrivals = Total Arrivals - Blocked.
            accepted_count = count_arrivals_window - count_blocked_window
            lam_eff = accepted_count / window_len
            
        else:
            avg_L = 0.0
            avg_busy_frac = 0.0
            avg_busy_util = 0.0
            p_loss = 0.0
            p_wait = 0.0
            avg_W = 0.0
            dep_rate = 0.0
            lam_eff = 0.0

        all_L.append(avg_L)
        all_W.append(avg_W)
        all_busy_frac.append(avg_busy_frac)
        all_p_loss.append(p_loss)
        all_p_wait.append(p_wait)
        all_arr.append(count_arrivals_window)
        all_blk.append(count_blocked_window)
        all_dep.append(count_departures_window)
        all_busy_util.append(avg_busy_util)
        all_lam_eff.append(lam_eff)
        all_dep_rate.append(dep_rate)
        
        seeds_used += 1
        seed_list.append(seed_val)

    # Aggregate results
    if seeds_used == 0:
        res = {
            "L": 0.0, "W": 0.0, "busy_frac": 0.0, "p_loss": 0.0,
            "runtime_units": 0.0, "seed_list": [], "seeds_used": 0,
            "time_unit": time_unit, "win": 0.0,
            "arr": 0.0, "blk": 0.0, "busy_util": 0.0, "dep": 0.0,
            "dep_rate": 0.0, "lam_eff": 0.0, "p_wait": 0.0,
            "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [],
            "per_seed_p_loss": [], "per_seed_p_wait": []
        }
    else:
        mean_L = sum(all_L) / seeds_used
        mean_W = sum(all_W) / seeds_used
        mean_busy_frac = sum(all_busy_frac) / seeds_used
        mean_p_loss = sum(all_p_loss) / seeds_used
        mean_p_wait = sum(all_p_wait) / seeds_used
        mean_arr = sum(all_arr) / seeds_used
        mean_blk = sum(all_blk) / seeds_used
        mean_dep = sum(all_dep) / seeds_used
        mean_busy_util = sum(all_busy_util) / seeds_used
        mean_lam_eff = sum(all_lam_eff) / seeds_used
        mean_dep_rate = sum(all_dep_rate) / seeds_used
        
        # Convert W to minutes
        W_minutes = mean_W * 60.0
        
        res = {
            "L": round(mean_L, 6),
            "W": round(W_minutes, 6),
            "busy_frac": round(mean_busy_frac, 6),
            "p_loss": round(mean_p_loss, 6),
            "runtime_units": round(H, 6),
            "seed_list": seed_list,
            "seeds_used": seeds_used,
            "time_unit": time_unit,
            "win": round(T_end - T_warm, 6),
            "arr": round(mean_arr, 6),
            "blk": round(mean_blk, 6),
            "busy_util": round(mean_busy_util, 6),
            "dep": round(mean_dep, 6),
            "dep_rate": round(mean_dep_rate, 6),
            "lam_eff": round(mean_lam_eff, 6),
            "p_wait": round(mean_p_wait, 6),
            "per_seed_L": [round(x, 6) for x in all_L],
            "per_seed_W": [round(x * 60.0, 6) for x in all_W],
            "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
            "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
            "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
        }
        
    print(json.dumps(res))

if __name__ == "__main__":
    main()
