import sys, json, random, math

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if i+1 < len(argv) and argv[i].startswith('--'):
            args[argv[i][2:]] = argv[i+1]
    
    seeds_n = int(args.get('seeds', '5'))
    horizon = float(args.get('horizon', '100.0'))
    seed_start = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    
    time_unit = "hour"
    lam_base = 3.0
    mu_base = 10.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
    # CV=1.5, Mean=6min=0.1h => sigma^2 = (1.5*0.1)^2 = 0.0225
    # Two-stage hyperexp: p*mean1 + (1-p)*mean2 = 0.1
    # Var = p*(mean1-mean)^2 + (1-p)*(mean2-mean)^2 + ... actually simpler to use Erlang or just sample from mixture directly?
    # The prompt says "two-stage mixed exponential". Let's assume a simple mixture of two exponentials with rates r1, r2.
    # E[T] = p/r1 + (1-p)/r2 = 0.1
    # E[T^2] = 2p/r1^2 + 2(1-p)/r2^2
    # Var(T) = E[T^2] - E[T]^2 = 0.0225
    # This is underdetermined without more constraints. However, the prompt says "P-K formula gives W and L... independent of specific distribution". 
    # But we are simulating. We need a valid distribution.
    # Let's pick a symmetric case or standard one. Often CV>1 implies heavy tail.
    # Let's try p=0.5. 
    # 0.5/r1 + 0.5/r2 = 0.1 => 1/r1 + 1/r2 = 0.2
    # 2*0.5/r1^2 + 2*0.5/r2^2 - 0.01 = 0.0225 => 1/r1^2 + 1/r2^2 = 0.0325/0.5? No.
    # Var = 2p/r1^2 + 2(1-p)/r2^2 - mean^2.
    # Let's just use a Gamma approximation or a specific mixture. 
    # Actually, for simulation correctness, any distribution with correct mean and variance works for verifying P-K approximations, but exact queue stats depend on higher moments.
    # Given the constraint "service duration must be drawn at arrival", we need a sampler.
    # Let's use a mixture of two exponentials with parameters chosen to match mean=0.1, var=0.0225.
    # Let r1 = 1/a, r2 = 1/b.
    # Simple choice: let one component be very fast, one slow.
    # Let's solve numerically or pick fixed values.
    # If we set p=0.9, r1=100 (mean 0.01), then 0.9*0.01 + 0.1*mean2 = 0.1 => 0.009 + 0.1*m2 = 0.1 => m2 = 0.91.
    # Var check: E[T^2] = 0.9*2*0.01^2 + 0.1*2*0.91^2 = 0.00018 + 0.16562 = 0.1658.
    # Var = 0.1658 - 0.01 = 0.1558 != 0.0225. Too high.
    # Need lower variance. Closer components.
    # Let's use a deterministic approach for sampling if possible, or just accept that we simulate a specific instance.
    # A common way to get CV=1.5 is a mixture of Exp(rate1) and Exp(rate2).
    # Let's use scipy-like logic manually? No, stdlib only.
    # Let's approximate with a lognormal? No, "mixed exponential".
    # Let's fix p=0.5.
    # 1/r1 + 1/r2 = 0.2
    # 1/r1^2 + 1/r2^2 = (Var + Mean^2)/Mean^2 * something?
    # E[T^2] = Var + Mean^2 = 0.0225 + 0.01 = 0.0325.
    # 2 * 0.5 * (1/r1^2 + 1/r2^2) = 0.0325 => 1/r1^2 + 1/r2^2 = 0.0325.
    # Let x = 1/r1, y = 1/r2. x+y=0.2, x^2+y^2=0.0325.
    # (x+y)^2 = x^2+y^2+2xy => 0.04 = 0.0325 + 2xy => 2xy = 0.0075 => xy = 0.00375.
    # t^2 - 0.2t + 0.00375 = 0.
    # Discriminant = 0.04 - 0.015 = 0.025. sqrt = 0.1581.
    # t = (0.2 +/- 0.1581)/2.
    # t1 = 0.179, t2 = 0.021.
    # So means are 0.179 and 0.021 hours. Rates are 1/0.179 and 1/0.021.
    
    mean1 = 0.17905
    mean2 = 0.02095
    p_mix = 0.5
    
    results = []
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_blocks = 0
    total_wait_time_sum = 0.0 # For Little's Law on waiting line? No, W is system time.
    
    per_seed_data = []
    
    win_len = horizon * 0.75
    warmup_end = horizon * 0.25
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        events = []
        def add_event(t, typ, data=None):
            events.append((t, typ, data))
            
        # Initial arrival
        next_arr_t = rng.expovariate(lam)
        add_event(next_arr_t, 'ARR')
        
        t_now = 0.0
        end_t = horizon
        
        n_in_sys = 0
        busy_until = 0.0
        last_change_t = 0.0
        area_L = 0.0
        sum_W = 0.0
        count_dep = 0
        count_arr = 0
        count_blk = 0
        busy_time = 0.0
        wait_time_sum = 0.0 # Sum of times spent waiting in queue (not service)
        
        # State variables for integration
        prev_t = 0.0
        prev_n = 0
        prev_busy = False
        
        while events:
            events.sort(key=lambda x: x[0])
            ev_t, ev_type, ev_data = events.pop(0)
            
            if ev_t > end_t:
                break
                
            # Integrate before state change
            dt = ev_t - prev_t
            if dt > 0:
                if prev_t >= warmup_end:
                    area_L += prev_n * dt
                    if prev_busy:
                        busy_time += dt
            
            prev_t = ev_t
            
            if ev_type == 'ARR':
                count_arr += 1
                # Draw service time now
                if rng.random() < p_mix:
                    svc_t = rng.expovariate(1.0/mean1)
                else:
                    svc_t = rng.expovariate(1.0/mean2)
                
                if n_in_sys == 0:
                    # Start service immediately
                    n_in_sys = 1
                    prev_busy = True
                    busy_until = ev_t + svc_t
                    add_event(busy_until, 'DEP', {'start': ev_t, 'end': busy_until})
                else:
                    # Queue
                    n_in_sys += 1
                    # Store arrival time for this customer? 
                    # In single server, we can just push to a list of waiting customers
                    # But we need to know when they start service to calculate W.
                    # Let's maintain a queue of arrival times.
                    if 'queue' not in locals():
                        queue = []
                    queue.append(ev_t)
                    
                # Schedule next arrival
                next_arr_t = ev_t + rng.expovariate(lam)
                if next_arr_t <= end_t:
                    add_event(next_arr_t, 'ARR')
                    
            elif ev_type == 'DEP':
                dep_t = ev_t
                start_t = ev_data['start']
                # Customer leaves
                n_in_sys -= 1
                count_dep += 1
                
                # Calculate W for this customer
                w_val = dep_t - start_t
                if dep_t >= warmup_end: # Only count if departure is in window? Or if entire stay is? Usually integral over window.
                    # Standard practice: include if event occurs in window.
                    sum_W += w_val
                
                # Check if there are waiting customers
                if 'queue' in locals() and len(queue) > 0:
                    arr_t_next = queue.pop(0)
                    # New service starts at dep_t
                    # Service time was already drawn? NO. 
                    # Constraint: "Service duration must be drawn at arrival".
                    # My previous code drew it at arrival but didn't store it with the queue item.
                    # I need to store (arrival_time, service_duration) in the queue.
                    pass 
                else:
                    prev_busy = False
                    # If no one waiting, server idle until next arrival
                    
            # Re-evaluating structure to handle "draw at arrival" correctly with queue.
            # I will rewrite the loop body slightly to ensure queue holds tuples.
            
            # Resetting logic for clarity inside the loop iteration isn't easy here.
            # Let's restart the inner loop logic properly.
            
            # Since I cannot easily refactor mid-loop in this thought process, I will write the final code carefully.
            # Key fix: Queue stores (arrival_time, service_duration).
            # On DEP: Pop from queue, start new service using stored duration.
            
            # Also, handling the "warmup" for W:
            # W is average time in system. Should we exclude customers who arrived during warmup but left after?
            # Usually, steady-state estimators discard initial transient.
            # Area method handles N. For W, often we sum W for all completed services in the window.
            
            # Let's refine the event processing in the final code block.
            
            # One more thing: blk (blocks). M/M/1/K? No, infinite queue implied by "average number in system".
            # Prompt doesn't specify capacity limit. Assume infinite queue. So blk=0 always?
            # "blk is ... rejected/lost". If no rejection policy, blk=0.
            # p_loss = 0.
            
            # Update prev_n and prev_busy for next integration step
            # Note: prev_busy needs to reflect state AFTER event? 
            # Integration uses state BEFORE event.
            # So `prev_n` and `prev_busy` should be updated to the NEW state for the NEXT interval.
            
            if ev_type == 'ARR':
                 # Already handled above, but need to update state vars for next loop
                 pass
            elif ev_type == 'DEP':
                 # Already handled
                 pass
                 
            # Update state for next interval
            # Wait, the integration happened at the TOP of the loop using `prev_n`.
            # So at the END of the loop, we must set `prev_n` and `prev_busy` to the CURRENT state.
            
            # Recalculating state based on event type:
            # If ARR: n increased. Busy status depends on if it started service.
            # If DEP: n decreased. Busy status depends on if queue had people.
            
            # This is getting messy in pseudo-code. I will implement cleanly in Python.
            
            # Final check on requirements:
            # - JSON output keys.
            # - Per-seed arrays.
            # - Time unit hour.
            
            # Let's construct the final script.
            
            # Correction on Queue Logic:
            # When ARR happens:
            #   Draw S.
            #   If Server Idle: Start Service. Set Busy=True. Next Event DEP at T+S.
            #   Else: Add (T, S) to Queue.
            # When DEP happens:
            #   Record Departure.
            #   If Queue Not Empty:
            #       Pop (Arr_T, S).
            #       Start Service. Next Event DEP at T+S.
            #       Busy remains True.
            #   Else:
            #       Busy becomes False.
            
            # Integration:
            #   At each event time T_curr:
            #   Delta = T_curr - T_prev.
            #   If T_prev >= Warmup:
            #       Area += N_prev * Delta
            #       BusyTime += Delta if Busy_prev else 0
            #   Then Process Event.
            #   Then Set T_prev = T_curr, N_prev = N_new, Busy_prev = Busy_new.
            
            # W Calculation:
            #   Sum of (Dep_Time - Arr_Time) for all departures where Dep_Time >= Warmup?
            #   Or Arr_Time >= Warmup?
            #   Typically, for steady state, we look at completions in the window.
            #   Let's use: Include if Dep_Time >= Warmup.
            
            # L Calculation:
            #   Area / Window_Length.
            
            # Busy_Frac:
            #   Busy_Time / Window_Length.
            
            # Runtime Units: Hour.
            
            # Perturbation: None changes structure.
            
            # Seeds: Independent streams.
            
            # Output: Single JSON line.
            
            # Let's write the code.
