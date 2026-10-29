import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 10.0 # 6 min mean -> 10 per hour
    c = 1
    K = 6 # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # Capacity is fixed by problem statement "only 1 doctor", but perturbation might imply changing effective capacity or just ignoring? 
        # The prompt says "perturbation only changes parameters not structure". c is number of servers. If c_up means increase servers, it breaks MM1. 
        # However, usually c_up in these contexts might mean increasing the queue limit or something else, but here c is explicitly 1.
        # Let's assume c_up doesn't change c (since structure is fixed to 1 doctor) or maybe it increases K? 
        # Given "MM1K", K is capacity. Let's assume c_up is a distractor or implies no change for this specific single-server case unless we interpret c as capacity K.
        # But standard notation: c=servers, K=capacity. Prompt says "1 doctor". So c=1.
        # If pert=c_up, maybe it increases K? Or maybe it's invalid. I will treat c_up as no change to lam/mu, and keep K=6.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
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
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn at arrival. We need a list of customers waiting/being served.
        # Each customer: (arrival_time, service_duration)
        # System state: n_in_system (including service)
        # Events: Arrival, Departure
        
        # To handle "draw service time at arrival", we generate it when the arrival event occurs.
        
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * H
        stats_window_len = H - warmup_end
        
        # Accumulators for area integration (time-weighted)
        # L_area: integral of N(t) dt over [warmup_end, H]
        # Busy_area: integral of I(N(t)>0) dt over [warmup_end, H]
        # Wait_area: integral of I(N(t)>1) dt over [warmup_end, H] -- actually p_wait is prob of waiting, which is P(N>=2)? 
        # In MM1-K, if you arrive and N < K, you enter. If N >= 1, you wait? No, if N=1, server busy, you wait. If N=0, no wait.
        # So p_wait = fraction of time N(t) >= 1? No, that's busy_frac.
        # p_wait usually means probability an arriving customer has to wait.
        # But the output asks for p_wait as a statistic. Often defined as P(Wait > 0).
        # Let's stick to time-average definitions for L and busy_frac.
        # For p_wait, let's calculate it as the fraction of accepted arrivals who had to wait (i.e., found system non-empty).
        
        L_area = 0.0
        Busy_area = 0.0
        Wait_count_accepted = 0
        Total_accepted = 0
        Total_arrivals = 0
        Total_blocked = 0
        Total_departures = 0
        
        # Current state
        n = 0
        last_event_time = 0.0
        # Queue of customers currently in system (waiting or being served)
        # We need to know when the next departure happens.
        # Since service times are exponential, memoryless property allows us to just track the remaining time of the current service?
        # BUT: "Service duration must be drawn at arrival and attached to the customer".
        # This implies we cannot use the memoryless property to reset the clock arbitrarily if we want strict adherence to "attached" logic, 
        # although for exponential distribution, drawing at arrival vs start is statistically identical IF we don't condition on past.
        # However, to simulate correctly with pre-drawn times:
        # We maintain a list of active customers.
        # When a customer arrives, we draw their service time `s`.
        # They join the queue.
        # The server works on the head of the queue.
        # We need to schedule departures.
        
        # Simpler approach for discrete event simulation with pre-drawn times:
        # Maintain a priority queue of events? Or just step through events.
        # Events: Arrival, Departure.
        # State: List of customers in system. Each has (arrival_time, service_time).
        # The one being served is the first one. Its completion time is max(last_departure_or_0, arrival_time_of_current_service_start) + service_time?
        # Actually, since it's FCFS and single server:
        # If server is idle, next departure is current_time + service_time_of_new_customer.
        # If server is busy, new customer waits.
        
        # Let's manage the timeline.
        # We need to know the finish time of the current service.
        # Let `current_service_finish` be infinity if idle.
        # When a customer arrives at `t`:
        #   Draw `s`.
        #   If `n < K`:
        #       Add customer to system.
        #       If `n == 0` (was idle):
        #           `current_service_finish` = `t` + `s`
        #           Schedule departure at `t+s`.
        #       Else:
        #           Customer joins queue. Departure time depends on previous ones.
        #           We can store the cumulative service times.
        #   Else:
        #       Block.
        
        # To handle multiple queued customers efficiently without complex bookkeeping of each person's exact start time:
        # Keep a list of service times for people in the system.
        # The total work in system is sum(service_times).
        # The time until next departure is determined by the head of the line.
        
        # Let's use an event-driven loop.
        # Event types: 0=Arrival, 1=Departure.
        # We need to generate arrivals dynamically.
        
        # Initialize
        t = 0.0
        n = 0
        # List of service times for customers currently in system (index 0 is being served)
        services = [] 
        # Time when the current service (if any) finishes
        next_dep_time = float('inf')
        
        # Generate first arrival
        next_arr_time = rng.expovariate(lam)
        
        # We need to integrate areas.
        # Area calculation: between events, state is constant.
        # L_area += n * (t_next - t_current)
        # Busy_area += (1 if n>0 else 0) * (t_next - t_current)
        
        while True:
            # Determine next event time
            t_arr = next_arr_time
            t_dep = next_dep_time
            
            if t_arr <= t_dep:
                # Arrival
                t_event = t_arr
                
                # Integrate up to t_event
                dt = t_event - last_event_time
                if last_event_time >= warmup_end:
                    L_area += n * dt
                    Busy_area += (1 if n > 0 else 0) * dt
                elif t_event > warmup_end:
                    # Partial overlap
                    dt_warm = warmup_end - last_event_time
                    dt_stat = t_event - warmup_end
                    L_area += n * dt_stat
                    Busy_area += (1 if n > 0 else 0) * dt_stat
                
                last_event_time = t_event
                
                # Process Arrival
                Total_arrivals += 1
                s = rng.expovariate(mu) # Draw service time now
                
                if n < K:
                    # Accept
                    Total_accepted += 1
                    if n > 0:
                        Wait_count_accepted += 1
                    
                    services.append(s)
                    n += 1
                    
                    # If server was idle, set next departure
                    if n == 1:
                        next_dep_time = t_event + s
                    else:
                        # Server busy, departure time remains same (head of queue unchanged)
                        pass
                        
                else:
                    # Block
                    Total_blocked += 1
                
                # Schedule next arrival
                next_arr_time = t_event + rng.expovariate(lam)
                
            else:
                # Departure
                t_event = t_dep
                
                # Integrate up to t_event
                dt = t_event - last_event_time
                if last_event_time >= warmup_end:
                    L_area += n * dt
                    Busy_area += (1 if n > 0 else 0) * dt
                elif t_event > warmup_end:
                    dt_stat = t_event - warmup_end
                    L_area += n * dt_stat
                    Busy_area += (1 if n > 0 else 0) * dt_stat
                
                last_event_time = t_event
                
                # Process Departure
                Total_departures += 1
                # Remove head of queue
                services.pop(0)
                n -= 1
                
                if n > 0:
                    # Next customer starts service immediately
                    next_s = services[0]
                    next_dep_time = t_event + next_s
                else:
                    next_dep_time = float('inf')
            
            # Check termination
            if t_event >= H:
                break
                
        # Final integration check? The loop breaks after processing event at t_event >= H.
        # But we integrated up to t_event. If t_event > H, we overshot slightly in integration?
        # The condition `if t_event >= H: break` happens AFTER integration.
        # Integration used `dt = t_event - last_event_time`.
        # If t_event > H, we integrated beyond H.
        # We should clip the integration to H.
        
        # Correction: The loop structure above integrates fully to t_event.
        # If t_event > H, we have added extra area.
        # Let's refine the loop to stop exactly at H.
        
        # Re-running logic mentally:
        # It's easier to just ensure we don't integrate past H.
        # But given the complexity of rewriting, let's assume H is large enough that boundary effects are negligible or fix the final step.
        # Actually, the prompt requires precise statistics.
        
        # Let's restart the inner loop logic with proper clipping.
        # ... (Self-correction: The code below implements the corrected loop)
        
        # Reset accumulators for this seed to implement correct clipping
        L_area = 0.0
        Busy_area = 0.0
        Wait_count_accepted = 0
        Total_accepted = 0
        Total_arrivals = 0
        Total_blocked = 0
        Total_departures = 0
        
        t = 0.0
        n = 0
        services = []
        next_dep_time = float('inf')
        next_arr_time = rng.expovariate(lam)
        last_event_time = 0.0
        
        while True:
            t_arr = next_arr_time
            t_dep = next_dep_time
            
            # Find next event time, capped at H
            t_next = min(t_arr, t_dep, H)
            
            # Integrate from last_event_time to t_next
            dt = t_next - last_event_time
            if dt > 0:
                if last_event_time >= warmup_end:
                    L_area += n * dt
                    Busy_area += (1 if n > 0 else 0) * dt
                elif t_next > warmup_end:
                    dt_stat = t_next - warmup_end
                    L_area += n * dt_stat
                    Busy_area += (1 if n > 0 else 0) * dt_stat
            
            last_event_time = t_next
            
            if t_next >= H:
                break
            
            # Process event
            if t_arr <= t_dep:
                # Arrival
                Total_arrivals += 1
                s = rng.expovariate(mu)
                
                if n < K:
                    Total_accepted += 1
                    if n > 0:
                        Wait_count_accepted += 1
                    services.append(s)
                    n += 1
                    if n == 1:
                        next_dep_time = t_arr + s
                else:
                    Total_blocked += 1
                
                next_arr_time = t_arr + rng.expovariate(lam)
            else:
                # Departure
                Total_departures += 1
                services.pop(0)
                n -= 1
                if n > 0:
                    next_dep_time = t_dep + services[0]
                else:
                    next_dep_time = float('inf')
                    
        # Calculate stats for this seed
        win_len = H - warmup_end
        if win_len <= 0:
            continue
            
        L_est = L_area / win_len
        Busy_frac_est = Busy_area / win_len
        p_loss_est = Total_blocked / Total_arrivals if Total_arrivals > 0 else 0.0
        p_wait_est = Wait_count_accepted / Total_accepted if Total_accepted > 0 else 0.0
        
        # W estimation: Little's Law L = lambda_eff * W => W = L / lambda_eff
        # lambda_eff = Total_accepted / win_len (per hour)
        lam_eff = Total_accepted / win_len
        if lam_eff > 0:
            W_est = L_est / lam_eff
        else:
            W_est = 0.0
            
        # Convert W to minutes
        W_min = W_est * 60.0
        
        # busy_util = E[min(N,c)]/c. Here c=1. min(N,1) is 1 if N>=1, 0 if N=0.
        # So busy_util is same as busy_frac for c=1.
        busy_util_est = Busy_frac_est
        
        all_L.append(L_est)
        all_W.append(W_min)
        all_busy_frac.append(Busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(Total_arrivals / N_seeds) # Wait, arr is avg per seed? "arr is statistical window average per seed count"? 
        # Prompt: "arr is statistical window average per seed person count". Ambiguous. Usually means total arrivals in window averaged over seeds?
        # Or rate? "dep_rate is per hour". "arr" likely total count in window.
        # Let's store total arrivals in window for this seed.
        all_arr[-1] = Total_arrivals
        all_blk[-1] = Total_blocked
        all_dep[-1] = Total_departures
        all_busy_util.append(busy_util_est)
        
        seeds_used += 1
        seed_list.append(seed)

    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    # Aggregate stats
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    
    # dep_rate: average departures per hour in window
    win_len_avg = H - 0.25*H
    avg_dep_rate = avg_dep / win_len_avg if win_len_avg > 0 else 0.0
    
    # lam_eff for overall report?
    avg_lam_eff = avg_arr / win_len_avg if win_len_avg > 0 else 0.0

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_loss": round(avg_p_loss, 4),
        "runtime_units": "seconds", # Not specified, but usually wall clock. We didn't measure it. Set to 0 or omit? Key required.
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len_avg, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
