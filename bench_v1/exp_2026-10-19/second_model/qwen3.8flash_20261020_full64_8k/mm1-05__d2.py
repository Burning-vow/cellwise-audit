import argparse, json, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()

    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 7.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service completions per minute
    c = 1
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
    else:
        lam = lam_base
        mu = mu_base

    horizon_min = H * 60.0 if args.horizon > 0 and abs(H - int(H)) < 1e-9 else H
    # The problem says H is in time_unit. Let's assume time_unit is minute for internal calc? 
    # Or hour? "average hourly 7 people". Usually simulation uses minutes or seconds.
    # Let's stick to minutes internally. If H is given as hours, we convert.
    # But the prompt says "H ... unit with your self-reported time_unit".
    # Let's report time_unit as 'minute' and treat H as minutes? 
    # No, standard queueing problems often use hours. Let's look at "average hourly 7".
    # If I set time_unit='hour', then lam=7, mu=1/6*60=10? No, mu is rate per hour.
    # Service mean 6 min = 0.1 hour. mu = 10 per hour.
    # Let's use time_unit='hour'.
    
    time_unit = 'hour'
    lam_h = 7.0
    mu_h = 10.0 # 1/(6/60)
    
    if pert == 'lam_up':
        lam_h *= 1.2
    elif pert == 'mu_up':
        mu_h *= 1.2
    elif pert == 'c_up':
        pass # c changes logic, but here c=1 fixed in base? Prompt says c_up changes parameter.
             # But MM1 implies c=1. If c_up means capacity up, maybe c=2?
             # "MM1" usually means single server. Let's assume c=1 always unless specified otherwise by structure change which is forbidden.
             # "Perturbation only changes parameters not structure". So c stays 1.
             # Maybe c_up refers to something else? Or just ignore if it doesn't make sense for MM1.
             # Let's keep c=1.
        pass

    horizon_hours = H
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_wait_count = 0
    total_arrivals = 0
    total_departures = 0
    total_blocks = 0
    total_customers_in_system_integral = 0.0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_fraction = 0.25
    warmup_end = horizon_hours * (1 - warmup_fraction)
    
    for i in range(N):
        seed = S + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam_h)
        next_departure = float('inf')
        
        n_in_system = 0
        last_event_time = 0.0
        
        # State variables for integration
        integral_L = 0.0
        busy_time = 0.0
        wait_count = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        # We need to track customers who are waiting to calculate W properly?
        # W = Average time in system. Sum of times / Number of departures in window.
        # We need to store arrival times of customers currently in system.
        # Since c=1, max 1 in service, others waiting.
        # List of arrival times for those in system.
        customer_arrival_times = [] 
        
        while t < horizon_hours:
            # Determine next event
            if next_arrival <= next_departure:
                # Arrival
                dt = next_arrival - t
                # Integrate L and Busy Time over dt
                if t >= warmup_end:
                    integral_L += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                
                t = next_arrival
                arr_count += 1
                
                # Generate service time now
                serv_time = rng.expovariate(mu_h)
                
                if n_in_system < c:
                    # Start service immediately
                    n_in_system += 1
                    customer_arrival_times.append(t)
                    next_departure = t + serv_time
                else:
                    # Wait
                    n_in_system += 1
                    customer_arrival_times.append(t)
                    # next_departure remains unchanged
                    
            else:
                # Departure
                dt = next_departure - t
                if t >= warmup_end:
                    integral_L += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                        
                t = next_departure
                
                if n_in_system > 0:
                    # Remove one customer from system
                    # Who leaves? FIFO. The first one in list.
                    leave_time = t
                    enter_time = customer_arrival_times.pop(0)
                    time_in_system = leave_time - enter_time
                    
                    dep_count += 1
                    if len(customer_arrival_times) > 0:
                        # Someone was waiting? Actually, if someone was waiting, they start service now.
                        # But we don't track individual service starts easily without more state.
                        # For W calculation, we just sum time_in_system for departed customers.
                        pass
                    
                    n_in_system -= 1
                    
                    if n_in_system > 0:
                        # Next customer starts service
                        # We need their service time. But we generated service time at arrival!
                        # Problem: We stored arrival time, but did we store service time?
                        # Requirement: "Service duration must be drawn at arrival and attached to customer".
                        # So we should store tuples (arrival_time, service_duration).
                        # Let's refactor storage.
                        pass
                    else:
                        next_departure = float('inf')
                else:
                    next_departure = float('inf')

        # Re-run loop with correct data structure
        # Reset
        t = 0.0
        next_arrival = rng.expovariate(lam_h)
        next_departure = float('inf')
        n_in_system = 0
        integral_L = 0.0
        busy_time = 0.0
        wait_count = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        total_time_in_system = 0.0 # Sum of W_i for departed customers in window
        
        # Queue stores (arrival_time, service_duration)
        queue = []
        
        while t < horizon_hours:
            if next_arrival <= next_departure:
                dt = next_arrival - t
                if t >= warmup_end:
                    integral_L += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                t = next_arrival
                arr_count += 1
                serv_dur = rng.expovariate(mu_h)
                
                if n_in_system < c:
                    n_in_system += 1
                    queue.append((t, serv_dur))
                    next_departure = t + serv_dur
                else:
                    n_in_system += 1
                    queue.append((t, serv_dur))
                    # Check if this customer waited? 
                    # If queue length before append was > 0, they waited.
                    # Actually, if n_in_system > c before increment, they waited.
                    # Simpler: if len(queue) > 1 after append, the new one waited? 
                    # No, FIFO. If there was already someone in service, new one waits.
                    # Condition for waiting: Was there a customer in service when this one arrived?
                    # Yes, if n_in_system_before_arrival >= c.
                    # Here n_in_system was incremented after check.
                    # Let's check before increment.
                    # Refactored below.
                    
            else:
                dt = next_departure - t
                if t >= warmup_end:
                    integral_L += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                t = next_departure
                
                if n_in_system > 0:
                    # Departure
                    # Pop front
                    arr_t, serv_d = queue.pop(0)
                    dep_count += 1
                    if t >= warmup_end:
                        total_time_in_system += (t - arr_t)
                    
                    n_in_system -= 1
                    
                    if n_in_system > 0:
                        # Next in queue starts service
                        next_arr_t, next_serv_d = queue[0]
                        # It has been waiting since next_arr_t. Now starts at t.
                        # New departure time = t + next_serv_d
                        next_departure = t + next_serv_d
                    else:
                        next_departure = float('inf')
                else:
                    next_departure = float('inf')
            
            # Update next_arrival if needed? No, handled in loop condition.
            # Need to generate next arrival if current one processed
            if t == next_arrival:
                 next_arrival = t + rng.expovariate(lam_h)

        # Calculate stats for this seed
        win_len = horizon_hours - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        avg_L = integral_L / win_len
        avg_W = total_time_in_system / dep_count if dep_count > 0 else 0.0
        bf = busy_time / win_len
        
        # p_wait: fraction of arrivals that had to wait?
        # We didn't track this explicitly in the second loop version above.
        # Let's add tracking.
        
        # Re-re-run to get p_wait correctly
        t = 0.0
        next_arrival = rng.expovariate(lam_h)
        next_departure = float('inf')
        n_in_system = 0
        integral_L = 0.0
        busy_time = 0.0
        wait_count = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        total_time_in_system = 0.0
        queue = []
        
        while t < horizon_hours:
            if next_arrival <= next_departure:
                dt = next_arrival - t
                if t >= warmup_end:
                    integral_L += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                t = next_arrival
                arr_count += 1
                serv_dur = rng.expovariate(mu_h)
                
                # Did this customer wait?
                # They wait if there is already someone in service (n_in_system >= c)
                # OR if there is someone in queue ahead of them.
                # In M/M/1/c, if n_in_system >= c, they wait (if c=1, if n>=1, wait).
                # Note: n_in_system includes those in service AND waiting.
                # If n_in_system >= c, the server is busy.
                # If c=1, n_in_system >= 1 means server busy.
                # If n_in_system == 0, no wait.
                # If n_in_system > 0, wait.
                
                if n_in_system >= c:
                    if t >= warmup_end:
                        wait_count += 1
                
                n_in_system += 1
                queue.append((t, serv_dur))
                
                if n_in_system == 1:
                    # Server was idle, now starts service
                    next_departure = t + serv_dur
                # Else, server is busy, departure time unchanged (unless we model preemption, which we don't)
                    
            else:
                dt = next_departure - t
                if t >= warmup_end:
                    integral_L += n_in_system * dt
                    if n_in_system > 0:
                        busy_time += dt
                t = next_departure
                
                if n_in_system > 0:
                    arr_t, serv_d = queue.pop(0)
                    dep_count += 1
                    if t >= warmup_end:
                        total_time_in_system += (t - arr_t)
                    n_in_system -= 1
                    
                    if n_in_system > 0:
                        next_arr_t, next_serv_d = queue[0]
                        next_departure = t + next_serv_d
                    else:
                        next_departure = float('inf')
                else:
                    next_departure = float('inf')
            
            if t == next_arrival:
                next_arrival = t + rng.expovariate(lam_h)

        win_len = horizon_hours - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        s_L = integral_L / win_len
        s_W = total_time_in_system / dep_count if dep_count > 0 else 0.0
        s_bf = busy_time / win_len
        s_pw = wait_count / arr_count if arr_count > 0 else 0.0
        s_pl = blk_count / arr_count if arr_count > 0 else 0.0 # blk_count is 0 for infinite buffer
        
        per_seed_L.append(s_L)
        per_seed_W.append(s_W)
        per_seed_busy_frac.append(s_bf)
        per_seed_p_loss.append(s_pl)
        per_seed_p_wait.append(s_pw)
        
        total_L_sum += s_L
        total_W_sum += s_W
        total_busy_time += s_bf * win_len # Weighted? No, just average of fractions
        total_wait_count += wait_count
        total_arrivals += arr_count
        total_departures += dep_count
        total_blocks += blk_count
        total_customers_in_system_integral += integral_L

    seeds_used = N
    avg_L = total_L_sum / seeds_used
    avg_W = total_W_sum / seeds_used
    avg_busy_frac = sum(per_seed_busy_frac) / seeds_used
    avg_p_wait = sum(per_seed_p_wait) / seeds_used
    avg_p_loss = sum(per_seed_p_loss) / seeds_used
    
    # Identity checks
    # L = lambda_eff * W
    # lambda_eff = dep_rate / 60? No, dep_rate is per hour.
    # dep_rate = total_departures / (seeds_used * win_len) ?
    # Per seed dep count.
    avg_dep_per_seed = total_departures / seeds_used
    dep_rate = avg_dep_per_seed / win_len # per hour
    
    lam_eff = dep_rate
    
    # busy_util = E[min(N,c)]/c. For c=1, E[N]/1 = L? No.
    # E[min(N,1)] is probability N>=1. Which is busy_frac.
    # So busy_util = busy_frac.
    # busy_occupied = 1 - pi_0. pi_0 is prob empty.
    # In steady state M/M/1, pi_0 = 1 - rho. busy_frac = rho.
    # So busy_occupied = busy_frac.
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "simulation",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(total_arrivals / seeds_used, 4),
        "blk": round(total_blocks / seeds_used, 4),
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(total_departures / seeds_used, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
