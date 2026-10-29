import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 6.0 / 60.0  # per minute
    mu_base = 1.0 / 5.0    # per minute
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_min = args.horizon * 60.0 if args.time_unit == 'hour' else args.horizon
    # Determine time unit based on typical usage or force minute for internal calc simplicity? 
    # The prompt says time_unit is what the program uses internally. Let's use minutes internally.
    time_unit = "minute"
    
    # If horizon was passed as hours in CLI context usually, but here H is in same unit as time_unit.
    # Let's assume H is in minutes if we set time_unit to minute.
    # But standard M/M/1 problems often give horizon in hours. 
    # Let's stick to minutes internally. If user passes H=100, it means 100 minutes? 
    # Or should I interpret H based on a fixed assumption? 
    # Prompt: "H ... unit with self-reported time_unit".
    # I will report time_unit="minute". So H is minutes.
    
    total_horizon = args.horizon
    warmup_end = total_horizon * 0.75
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_p_loss = []
    all_busy_util = []
    all_busy_occupied = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_time = None
        queue = [] # stores (arrival_time, service_duration)
        server_free_at = 0.0
        
        # Statistics accumulators for this seed
        area_N = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0 # For M/M/1 infinite buffer, blk is 0 unless system full, but problem implies stable/infinite? 
                      # "System stable" usually implies infinite capacity or high enough. 
                      # However, p_loss and blk are requested. In standard M/M/1/K, loss occurs. 
                      # But prompt says "M/M/1", usually infinite queue. 
                      # Wait, "blk" and "p_loss" are requested. If infinite, they are 0.
                      # Let's assume infinite buffer as per standard M/M/1 description unless K is specified.
                      # If infinite, blk=0, p_loss=0.
        
        # To calculate W properly via Little's Law or direct sum of sojourn times?
        # Direct sum of sojourn times is better for accuracy in simulation.
        sum_sojourn = 0.0
        
        last_event_time = 0.0
        
        while t < total_horizon:
            # Determine next event time
            arr_t = next_arrival if next_arrival > t else float('inf')
            dep_t = server_free_at if server_free_at > t else float('inf')
            
            # If queue is empty and server idle, dep_t is inf effectively until new arrival
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= total_horizon:
                break
                
            dt = next_t - t
            
            # Integrate N(t) over [t, next_t]
            n_current = len(queue) + (1 if t < server_free_at else 0)
            if t >= warmup_end:
                area_N += n_current * dt
            
            t = next_t
            
            if abs(t - arr_t) < 1e-9:
                # Arrival
                count_arr += 1
                svc_dur = rng.expovariate(mu)
                
                if t >= warmup_end:
                    pass # We track sojourn later
                
                # Check if server busy
                if t < server_free_at:
                    # Join queue
                    queue.append((t, svc_dur))
                else:
                    # Start service immediately
                    server_free_at = t + svc_dur
                    # Record start of service for this customer? 
                    # Actually, we need to know when they leave to add to sum_sojourn.
                    # We can push to a "in_service" list or just handle departure logic carefully.
                    # Simpler: When a customer enters service, we know their arrival time.
                    # We need to link arrival time to departure time.
                    # Let's store (arrival_time, end_of_service_time) in a separate structure or manage queue differently.
                    
                    # Revised approach:
                    # Queue holds (arrival_time, service_duration).
                    # When server becomes free, pop from queue, set server_free_at = t + duration.
                    # When arrival happens and server free, set server_free_at = t + duration.
                    # We need to capture the departure time to compute sojourn.
                    
                    # Let's maintain a list of active customers with their arrival times.
                    # But simpler: Just record departure events.
                    # When a customer leaves, we know their arrival time if we stored it.
                    
                    # Let's change data structure:
                    # queue: list of (arrival_time, service_duration)
                    # current_customer: (arrival_time, service_duration, start_time) or None
                    
                    # If server was free:
                    start_time = t
                    end_time = t + svc_dur
                    server_free_at = end_time
                    # Store info to process at end_time
                    # We can't easily store "current" without complicating event loop.
                    # Alternative: Push departure event into a priority queue? 
                    # Since single server, we can just check queue at each step.
                    
                    # Let's restart the loop logic slightly cleaner.
                    pass

        # Re-implementing the loop cleanly inside the seed block
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        server_free_at = 0.0
        queue = [] # (arrival_time, service_duration)
        
        area_N = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_sojourn = 0.0
        count_sojourn_samples = 0
        
        # We need to track who is in service to get their arrival time upon departure.
        # Let's keep a variable `in_service` which is a tuple (arrival_time, service_duration, start_time) or None.
        in_service = None
        
        while t < total_horizon:
            # Calculate next event time
            arr_t = next_arrival
            dep_t = float('inf')
            if in_service is not None:
                dep_t = in_service[2] + in_service[1] # start + dur
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= total_horizon:
                # Advance to end
                dt = total_horizon - t
                n_curr = len(queue) + (1 if in_service is not None else 0)
                if t >= warmup_end:
                    area_N += n_curr * dt
                t = total_horizon
                break
            
            dt = next_t - t
            n_curr = len(queue) + (1 if in_service is not None else 0)
            
            if t >= warmup_end:
                area_N += n_curr * dt
                
            t = next_t
            
            if abs(t - arr_t) < 1e-9:
                # Arrival
                count_arr += 1
                svc_dur = rng.expovariate(mu)
                
                # Infinite buffer assumed, so no blocking
                if in_service is None:
                    # Server free
                    in_service = (t, svc_dur, t) # arrival, dur, start
                    # Note: start time is t
                else:
                    # Server busy, join queue
                    queue.append((t, svc_dur))
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - dep_t) < 1e-9:
                # Departure
                count_dep += 1
                arr_time, _, _ = in_service
                sojourn = t - arr_time
                if t >= warmup_end: # Only count sojourns that completed after warmup? 
                    # Standard practice: include all completions in window.
                    # Window is defined by time. If departure is in window, count it.
                    sum_sojourn += sojourn
                    count_sojourn_samples += 1
                
                in_service = None
                
                # Check if queue has waiting customers
                if queue:
                    next_cust = queue.pop(0)
                    # They start service immediately at t
                    in_service = (next_cust[0], next_cust[1], t)
        
        # End of simulation for this seed
        
        # Calculate stats for this seed
        win_len = total_horizon - warmup_end
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_wait_est = 0.0
            p_loss_est = 0.0
            busy_util_est = 0.0
            busy_occ_est = 0.0
        else:
            L_est = area_N / win_len
            W_est = sum_sojourn / count_sojourn_samples if count_sojourn_samples > 0 else 0.0
            
            # Busy fraction: E[min(N,1)] / 1. 
            # We integrated N(t). We need integral of min(N(t), 1).
            # This requires re-integrating or tracking separately.
            # Let's add another accumulator for busy time.
            pass 

        # Oops, I didn't track busy time area. Need to fix loop.
        # Restarting seed loop implementation with correct accumulators.
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        server_free_at = 0.0
        queue = []
        in_service = None
        
        area_N = 0.0
        area_busy = 0.0 # Integral of min(N, 1)
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_sojourn = 0.0
        count_sojourn_samples = 0
        count_waiters = 0 # Number of arrivals that found server busy
        
        while t < total_horizon:
            arr_t = next_arrival
            dep_t = float('inf')
            if in_service is not None:
                dep_t = in_service[2] + in_service[1]
            
            next_t = min(arr_t, dep_t)
            
            if next_t >= total_horizon:
                dt = total_horizon - t
                n_curr = len(queue) + (1 if in_service is not None else 0)
                b_curr = 1 if n_curr > 0 else 0
                if t >= warmup_end:
                    area_N += n_curr * dt
                    area_busy += b_curr * dt
                t = total_horizon
                break
            
            dt = next_t - t
            n_curr = len(queue) + (1 if in_service is not None else 0)
            b_curr = 1 if n_curr > 0 else 0
            
            if t >= warmup_end:
                area_N += n_curr * dt
                area_busy += b_curr * dt
                
            t = next_t
            
            if abs(t - arr_t) < 1e-9:
                count_arr += 1
                svc_dur = rng.expovariate(mu)
                
                if in_service is None:
                    in_service = (t, svc_dur, t)
                else:
                    queue.append((t, svc_dur))
                    count_waiters += 1 # Arrived to find server busy
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - dep_t) < 1e-9:
                count_dep += 1
                arr_time, _, _ = in_service
                sojourn = t - arr_time
                if t >= warmup_end:
                    sum_sojourn += sojourn
                    count_sojourn_samples += 1
                
                in_service = None
                if queue:
                    next_cust = queue.pop(0)
                    in_service = (next_cust[0], next_cust[1], t)

        win_len = total_horizon - warmup_end
        if win_len > 0:
            L_est = area_N / win_len
            W_est = sum_sojourn / count_sojourn_samples if count_sojourn_samples > 0 else 0.0
            busy_frac_est = area_busy / win_len
            p_wait_est = count_waiters / count_arr if count_arr > 0 else 0.0
            p_loss_est = 0.0 # Infinite buffer
            busy_util_est = busy_frac_est # c=1
            busy_occ_est = busy_frac_est # 1 - pi_0 approx by time avg
        else:
            L_est = W_est = busy_frac_est = p_wait_est = p_loss_est = busy_util_est = busy_occ_est = 0.0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr)
        all_dep.append(count_dep)
        all_blk.append(count_blk)
        all_p_loss.append(p_loss_est)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        
        seeds_used += 1
        seed_list.append(s)

    # Aggregate results
    avg_L = sum(all_L) / seeds_used if seeds_used else 0
    avg_W = sum(all_W) / seeds_used if seeds_used else 0
    avg_busy_frac = sum(all_busy_frac) / seeds_used if seeds_used else 0
    avg_p_wait = sum(all_p_wait) / seeds_used if seeds_used else 0
    avg_arr = sum(all_arr) / seeds_used if seeds_used else 0
    avg_dep = sum(all_dep) / seeds_used if seeds_used else 0
    avg_blk = sum(all_blk) / seeds_used if seeds_used else 0
    avg_p_loss = sum(all_p_loss) / seeds_used if seeds_used else 0
    avg_busy_util = sum(all_busy_util) / seeds_used if seeds_used else 0
    avg_busy_occ = sum(all_busy_occupied) / seeds_used if seeds_used else 0
    
    # dep_rate in per hour
    # avg_dep is count per seed in window win_len (minutes)
    # rate = (avg_dep / win_len) * 60
    dep_rate = (avg_dep / (total_horizon - total_horizon*0.75)) * 60 if (total_horizon*0.25) > 0 else 0

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(total_horizon * 0.25, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(avg_arr / (total_horizon * 0.25) * 60, 4) if (total_horizon*0.25)>0 else 0,
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
