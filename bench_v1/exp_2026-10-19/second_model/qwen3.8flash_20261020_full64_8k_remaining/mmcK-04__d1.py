import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr = 10/hr
    c = 2
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
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
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_runtime_units = 0.0
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = [] 
        queue = [] 
        servers_free_at = [0.0] * c
        num_in_system = 0
        
        warmup_end = 0.25 * H
        stats_window_len = H - warmup_end
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0
        count_waited = 0
        
        last_event_time = 0.0
        
        while True:
            # Determine next event time
            arr_t = next_arrival if next_arrival < float('inf') else float('inf')
            dep_t = min(servers_free_at) if any(s < float('inf') for s in servers_free_at) else float('inf')
            
            if arr_t > H and dep_t > H:
                break
            
            if arr_t <= dep_t:
                # Arrival
                t = arr_t
                if t >= warmup_end:
                    dt = t - last_event_time
                    area_L += num_in_system * dt
                    busy_count = sum(1 for s in servers_free_at if s > last_event_time or (s >= t and s != float('inf')))
                    # Recalculate busy fraction correctly based on state during interval
                    # Actually, simpler to track integral of indicator{N>0}
                    pass
                
                # Update integrals before changing state
                dt = t - last_event_time
                if last_event_time < warmup_end:
                    overlap_start = max(last_event_time, warmup_end)
                    if overlap_start < t:
                        # Partially in window? No, we only integrate from warmup_end onwards
                        pass
                    # We need to handle the transition carefully.
                    # Let's restart integration logic properly.
                
                # Resetting approach for clarity:
                # We will simulate events. At each event, we add area since last event.
                # But we only care about area after warmup.
                
                # Let's restructure loop slightly for correctness.
                # Break out and rewrite inner loop structure mentally.
                
                # Correct Logic:
                # 1. Calculate dt = t - last_event_time
                # 2. If last_event_time < warmup_end and t > warmup_end:
                #    Split interval.
                # 3. Add area for portion inside window.
                
                # Since I cannot edit freely without breaking flow, let's assume standard DES pattern.
                
                # Arrival handling
                if num_in_system < K:
                    num_in_system += 1
                    count_arr += 1 if t >= warmup_end else 0
                    # Find free server
                    free_idx = -1
                    for j in range(c):
                        if servers_free_at[j] <= t:
                            free_idx = j
                            break
                    if free_idx != -1:
                        st = rng.expovariate(mu)
                        servers_free_at[free_idx] = t + st
                        service_times.append((t, t+st)) # Not strictly needed if we use servers_free_at
                    else:
                        queue.append(t)
                else:
                    count_blk += 1 if t >= warmup_end else 0
                
                next_arrival = t + rng.expovariate(lam)
                last_event_time = t
                
            else:
                # Departure
                t = dep_t
                # Which server finished?
                finished_servers = [j for j in range(c) if abs(servers_free_at[j] - t) < 1e-9]
                if not finished_servers:
                    # Floating point issue, pick min
                    min_val = min(servers_free_at)
                    finished_servers = [j for j in range(c) if servers_free_at[j] == min_val]
                
                j = finished_servers[0]
                
                # Area update before state change
                dt = t - last_event_time
                if last_event_time < warmup_end:
                    if t > warmup_end:
                        # Part of interval is in window
                        win_dt = t - warmup_end
                        # State was constant during [last_event_time, t)
                        # Was it busy?
                        # Check if any server was busy at start of this interval (which is same as end of prev)
                        # Actually, state changes AT events. So between last_event_time and t, state is fixed.
                        # We need to know if system was non-empty during this whole interval.
                        # num_in_system is current count BEFORE departure processing but AFTER arrival processing?
                        # No, num_in_system reflects state just before this event.
                        
                        # Wait, if we are at a departure event, num_in_system includes the departing car.
                        # The interval [last_event_time, t) had this num_in_system.
                        
                        if num_in_system > 0:
                            area_busy += win_dt
                        area_L += num_in_system * win_dt
                        
                        # Also add part before warmup? No, ignore.
                        # But what if last_event_time was way before warmup?
                        # We should have been accumulating only from warmup.
                        # This implies we need to reset accumulators or handle split intervals.
                        # Simpler: Only start counting when t >= warmup_end.
                        # But area needs integration from warmup_end.
                        # If an interval spans warmup_end, we split it.
                        
                        # Let's refine:
                        # If last_event_time < warmup_end and t >= warmup_end:
                        #   Interval [last_event_time, warmup_end] ignored.
                        #   Interval [warmup_end, t] counted.
                        #   State is num_in_system (before dep).
                        #   Busy status: num_in_system > 0.
                        
                        # If last_event_time >= warmup_end:
                        #   Interval [last_event_time, t] counted.
                        
                        # If t < warmup_end:
                        #   Ignore.
                        
                        pass 
                    else:
                        pass # Entirely before warmup
                else:
                    # Entirely in window
                    if num_in_system > 0:
                        area_busy += dt
                    area_L += num_in_system * dt
                
                # Process Departure
                num_in_system -= 1
                count_dep += 1 if t >= warmup_end else 0
                
                # W calculation: Need arrival time of this car.
                # We didn't store arrival times linked to specific server slots easily.
                # Better: Store (arrival_time, departure_time) pairs or manage queue explicitly.
                # Refactoring data structures for W:
                # Use a list of active services with their arrival times.
                
                # Since I am writing code directly, I must ensure W is calculated.
                # I will maintain a list `active_services` containing (arrival_time, end_time).
                # On departure, find which one ended.
                
                # Re-evaluating strategy: It's getting complex to patch.
                # I will write the clean version now.
                
                # Clean Version Plan:
                # Variables:
                # t: current time
                # next_arr: next arrival time
                # events: priority queue or just compare next_arr and next_dep
                # next_dep: min(end_time of active services)
                # active_services: list of (start_time, end_time)
                # queue: list of start_times waiting
                # n_sys: len(active_services) + len(queue)
                
                # Loop:
                # 1. Determine next event time te = min(next_arr, next_dep)
                # 2. If te > H: break
                # 3. Integrate areas from last_t to te (handling warmup split)
                # 4. Process event at te
                # 5. Update last_t = te
                
                # This requires rewriting the block above.
                # I will output the corrected full function below.
                break # Exit this messy attempt to provide clean code
            # End of messy attempt
            break
        
    # Placeholder return to satisfy syntax if break happened early
    # Actual implementation follows in final output block.
    pass

if __name__ == "__main__":
    main()
