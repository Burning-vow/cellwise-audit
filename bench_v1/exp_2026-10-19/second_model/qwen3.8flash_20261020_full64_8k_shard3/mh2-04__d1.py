import sys, json, random, math

def main():
    args = {}
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            val = sys.argv[i+1] if i+1 < len(sys.argv) and not sys.argv[i+1].startswith('--') else None
            if val is not None:
                try: args[key] = float(val)
                except: args[key] = val
    
    seeds_n = int(args.get('seeds', 10))
    horizon = float(args.get('horizon', 100.0)) # hours
    seed_start = int(args.get('seed-start', 1))
    pert = args.get('pert', 'none')
    
    lam_base = 5.0 # calls per hour
    mu_base = 10.0 # calls per hour (mean service time 6 min = 0.1 hr)
    
    if pert == 'lam_up': lam_base *= 1.1
    elif pert == 'mu_up': mu_base *= 1.1
    elif pert == 'c_up': pass # CV fixed by distribution choice logic below, but prompt says pert only changes params. 
                             # For mixed exponential with mean 0.1 and CV=2, we need specific rates.
                             # Let's stick to base parameters unless pert explicitly targets them.
                             # The prompt says "pert NAME ... only change parameters". 
                             # If c_up means increase CV? But CV is fixed at 2 in problem statement.
                             # Usually these perturbations scale the base rate.
                             # Let's assume standard scaling for now. If c_up implies changing service distribution shape while keeping mean/CV? 
                             # Actually, for M/G/1, W depends on E[S^2]. 
                             # Mixed Exp: S ~ p*Exp(mu1) + (1-p)*Exp(mu2).
                             # E[S] = p/mu1 + (1-p)/mu2 = 0.1
                             # Var(S) = 2*p/mu1^2 + 2*(1-p)/mu2^2 - (E[S])^2 ? No.
                             # For Exp(lambda), Mean=1/lambda, Var=1/lambda^2.
                             # Mixed Exp Variance formula is complex. 
                             # Simpler approach: Use Erlang or just sample from a distribution that matches Mean=0.1, CV=2.
                             # A common way to get high CV is heavy tail, but here it's mixed exp.
                             # Let's use a simple approximation or exact sampling if possible.
                             # However, the prompt says "P-K formula gives W... independent of specific two-stage dist".
                             # This implies we can just use ANY distribution with Mean=0.1 and CV=2.
                             # We can simulate this by drawing from a Gamma distribution with shape k=1/CV^2 = 1/4 = 0.25 and scale theta = Mean/k = 0.1/0.25 = 0.4.
                             # Gamma(k, theta) has Mean=k*theta, Var=k*theta^2. CV = sqrt(Var)/Mean = 1/sqrt(k).
                             # So k=0.25 gives CV=2.
                             # Sampling Gamma(0.25, 0.4) is easy with random.gammavariate.
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_dep = []
    results_blk = []
    results_util = []
    results_occ = []
    
    total_seeds_used = 0
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        # Parameters
        lam = lam_base
        # Service time distribution: Gamma(shape=0.25, scale=0.4) -> Mean=0.1, CV=2
        # Note: Time unit is HOURS.
        shape_k = 0.25
        scale_theta = 0.4
        
        # Simulation State
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # Statistics accumulators (for area integration)
        # Warmup: discard first 25% of horizon
        warmup_end = horizon * 0.25
        
        # Counters within window [warmup_end, horizon]
        count_arr = 0
        count_dep = 0
        count_blk = 0
        
        # Area integrals
        area_N = 0.0       # Integral of N(t) dt
        area_busy = 0.0    # Integral of I(N>0) dt
        area_wait = 0.0    # Integral of (N-1)+ dt? Or sum of waiting times?
                           # L = area_N / T_window
                           # W = Total Waiting Time / Number of Customers who waited? 
                           # Standard definition: W is average time in system.
                           # Little's Law: L = lambda_eff * W.
                           # To compute W directly: Sum of (Departure_Time - Arrival_Time) for all completed customers in window?
                           # Careful with truncation. Usually, we track individual customer sojourn times.
        
        # List to store sojourn times of customers who depart within the window
        # But what about those arriving before window end but departing after?
        # Standard practice: Only count customers who both arrive and depart within the statistical window?
        # Or count all arrivals in window and their eventual departure?
        # Given "area type quantities must be integrated before state change", let's stick to area method for L.
        # For W, we can use Little's Law derived from L and effective arrival rate, OR direct measurement.
        # Direct measurement is safer for validation.
        # Let's collect sojourn times for customers who DEPART within the window.
        # And also handle blocking.
        
        # Customer Queue
        queue = [] # list of arrival times
        
        last_event_time = 0.0
        
        # Initialize first event
        events = []
        if next_arrival <= horizon:
            events.append(('arr', next_arrival))
        if next_departure <= horizon:
            events.append(('dep', next_departure))
            
        # We need a priority queue or just check min each step since only 1 server.
        # Simple loop:
        
        # Reset stats for this seed
        local_area_N = 0.0
        local_area_busy = 0.0
        local_count_arr_win = 0
        local_count_dep_win = 0
        local_count_blk_win = 0
        local_sojourn_sum = 0.0
        local_sojourn_count = 0
        
        # Track number in system N
        N = 0
        
        # Helper to add area
        def add_area(dt, n_val):
            nonlocal local_area_N, local_area_busy
            local_area_N += n_val * dt
            if n_val > 0:
                local_area_busy += dt

        # Main Loop
        while t < horizon:
            # Determine next event time
            next_t = float('inf')
            event_type = None
            
            if next_arrival < next_t:
                next_t = next_arrival
                event_type = 'arr'
            if next_departure < next_t:
                next_t = next_departure
                event_type = 'dep'
                
            if next_t > horizon:
                break
                
            # Advance time
            dt = next_t - t
            if dt > 0:
                add_area(dt, N)
                t = next_t
            
            # Process Event
            if event_type == 'arr':
                # Check if in window
                if t >= warmup_end:
                    local_count_arr_win += 1
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # Handle arrival
                if N == 0:
                    # Server idle, start service immediately
                    N = 1
                    # Sample service time
                    serv_time = rng.gammavariate(shape_k, scale_theta)
                    next_departure = t + serv_time
                    # Store arrival time for this customer
                    # Since only 1 server, we can just keep one variable for current customer arrival
                    curr_cust_arr = t
                else:
                    # Server busy, join queue
                    N += 1
                    queue.append(t)
                    
            elif event_type == 'dep':
                # Customer departs
                if t >= warmup_end:
                    local_count_dep_win += 1
                    # Calculate sojourn time for the customer who was being served
                    # Who was being served? The one whose arrival time is curr_cust_arr
                    # Wait, if there were people in queue, the one being served is the one that started service earlier.
                    # In our logic:
                    # When N goes from 0->1, we set curr_cust_arr.
                    # When N > 1, new arrivals go to queue.
                    # When departure happens:
                    #   If queue is empty: N becomes 0.
                    #   If queue is not empty: Next person starts service.
                    
                    # We need to know the arrival time of the person finishing service.
                    # It is stored in curr_cust_arr.
                    sojourn = t - curr_cust_arr
                    local_sojourn_sum += sojourn
                    local_sojourn_count += 1
                    
                # Update state
                if len(queue) > 0:
                    # Start service for next in queue
                    next_arr_time = queue.pop(0)
                    curr_cust_arr = next_arr_time
                    # Sample new service time
                    serv_time = rng.gammavariate(shape_k, scale_theta)
                    next_departure = t + serv_time
                    # N remains same (one leaves, one enters service)
                    # Actually N counts total in system. One left, one moved from queue to service.
                    # So N decreases by 1? No.
                    # Before dep: N included the one in service and those in queue.
                    # After dep: The one in service leaves. The head of queue enters service.
                    # Total count N should decrease by 1.
                    N -= 1
                else:
                    # No one in queue, server becomes idle
                    N -= 1
                    next_departure = float('inf')
                    curr_cust_arr = None # Not strictly needed if N==0 handled correctly

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        win_len = horizon - warmup_end
        
        if win_len > 0:
            L_est = local_area_N / win_len
            busy_frac_est = local_area_busy / win_len
            
            # W estimation
            if local_sojourn_count > 0:
                W_est = local_sojourn_sum / local_sojourn_count
            else:
                W_est = 0.0
                
            # Probabilities
            # p_loss: blocked / arrived_in_window? 
            # In single server infinite queue, no loss. blk should be 0.
            # But prompt asks for blk. If system capacity is infinite, blk=0.
            # If capacity limited? Prompt doesn't say. Assume infinite buffer.
            # So p_loss = 0.
            # p_wait: fraction of customers who waited?
            # Customers who waited are those who arrived when N>=1.
            # We didn't track this explicitly in the loop above easily without more state.
            # Alternative: p_wait = 1 - P(arrival sees idle).
            # P(idle) = 1 - busy_frac.
            # So p_wait = busy_frac? 
            # Yes, for Poisson arrivals, PASTA property holds. Probability an arrival finds system busy is equal to fraction of time system is busy.
            # So p_wait = busy_frac_est.
            
            p_loss_est = 0.0
            p_wait_est = busy_frac_est
            
            # Utilization
            # busy_util = E[min(N,c)]/c. Here c=1. E[min(N,1)] = P(N>=1) = busy_frac.
            # So busy_util = busy_frac.
            # busy_occupied = 1 - pi_0 = busy_frac.
            
            util_est = busy_frac_est
            occ_est = busy_frac_est
            
            # Effective arrival rate
            # lam_eff = count_arr / win_len
            lam_eff = local_count_arr_win / win_len
            
            # Dep rate
            dep_rate = local_count_dep_win / win_len
            
            # Store results
            results_L.append(L_est)
            results_W.append(W_est)
            results_busy_frac.append(busy_frac_est)
            results_p_loss.append(p_loss_est)
            results_p_wait.append(p_wait_est)
            results_arr.append(local_count_arr_win)
            results_dep.append(local_count_dep_win)
            results_blk.append(0) # Infinite buffer
            results_util.append(util_est)
            results_occ.append(occ_est)
            
            total_seeds_used += 1

    # Aggregate over seeds
    if total_seeds_used == 0:
        avg_L = 0.0
        avg_W = 0.0
        avg_busy = 0.0
        avg_pl = 0.0
        avg_pw = 0.0
        avg_arr = 0.0
        avg_dep = 0.0
        avg_blk = 0.0
        avg_util = 0.0
        avg_occ = 0.0
        avg_lam_eff = 0.0
        avg_dep_rate = 0.0
    else:
        avg_L = sum(results_L) / total_seeds_used
        avg_W = sum(results_W) / total_seeds_used
        avg_busy = sum(results_busy_frac) / total_seeds_used
        avg_pl = sum(results_p_loss) / total_seeds_used
        avg_pw = sum(results_p_wait) / total_seeds_used
        avg_arr = sum(results_arr) / total_seeds_used
        avg_dep = sum(results_dep) / total_seeds_used
        avg_blk = sum(results_blk) / total_seeds_used
        avg_util = sum(results_util) / total_seeds_used
        avg_occ = sum(results_occ) / total_seeds_used
        
        # Recalculate averages for rates based on aggregated counts? 
        # Or average of per-seed rates?
        # Prompt: "arr is average per seed count", "dep_rate is effective departure rate"
        # dep_rate usually means per hour.
        # Let's compute global effective rates from sums?
        # Or just average the per-seed calculated rates.
        # Per-seed lam_eff was local_count_arr / win_len.
        # Global lam_eff = (Sum local_count_arr) / (Total Seeds * win_len)?
        # Same as Average(lam_eff).
        
        avg_lam_eff = sum([r_a / (horizon - horizon*0.25) for r_a in results_arr]) / total_seeds_used
        avg_dep_rate = sum([r_d / (horizon - horizon*0.25) for r_d in results_dep]) / total_seeds_used

    # Prepare JSON output
    # Keys required: L, W, busy_frac, runtime_units, seed_list, seeds_used, time_unit, win
    # Recommended: arr, blk, busy_util, dep, dep_rate, lam_eff, p_loss, p_wait, per_seed_*
    
    # time_unit: internal is hours. Output W in minutes.
    # L is dimensionless.
    # W needs conversion to minutes.
    W_minutes = avg_W * 60.0
    
    # per_seed arrays
    ps_L = [round(x, 6) for x in results_L]
    ps_W_min = [round(x * 60.0, 6) for x in results_W]
    ps_busy = [round(x, 6) for x in results_busy_frac]
    ps_pl = [round(x, 6) for x in results_p_loss]
    ps_pw = [round(x, 6) for x in results_p_wait]
    
    seed_list = [seed_start + i for i in range(total_seeds_used)]
    
    out = {
        "L": round(avg_L, 6),
        "W": round(W_minutes, 6),
        "busy_frac": round(avg_busy, 6),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": total_seeds_used,
        "time_unit": "hour",
        "win": round(horizon - horizon*0.25, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": ps_L,
        "per_seed_W": ps_W_min,
        "per_seed_busy_frac": ps_busy,
        "per_seed_p_loss": ps_pl,
        "per_seed_p_wait": ps_pw
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
