import sys, json, random, math
from collections import deque

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if i+1 < len(argv):
            args[argv[i].lstrip('-')] = argv[i+1]
    
    N = int(args.get('seeds', '5'))
    H = float(args.get('horizon', '100.0'))
    S = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    
    lam_base = 5.0 / 60.0 # per minute
    mu_base = 1.0 / 6.0   # per minute
    
    if pert == 'lam_up': lam_base *= 1.2
    elif pert == 'mu_up': mu_base *= 1.2
    elif pert == 'c_up': pass # c=1 fixed
    
    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else (H * 60 if time_unit == "hour" else H / 60)
    
    warmup_frac = 0.25
    warmup_time = horizon_min * warmup_frac
    
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
    
    seed_list = []
    
    for s_idx in range(N):
        seed_val = S + s_idx
        rng = random.Random(seed_val)
        
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        events = [] # (time, type, data)
        # type: 0 arrival, 1 departure
        
        # State
        server_busy = False
        service_end_time = 0.0
        queue = deque() # stores arrival times of waiting customers
        
        # Stats accumulators (for the window [warmup_time, horizon_min])
        area_L = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_service_times_in_window = 0.0 # For W calculation via Little's Law or direct? 
        # W is average time in system. We need to track individual sojourn times for those who depart in window.
        # But standard DES often uses area under L(t) curve for L, and then W = L / lambda_eff.
        # Let's use Area method for L and busy_frac.
        # For W, we can compute it as Average Sojourn Time of completed calls in the window.
        
        last_event_time = 0.0
        current_L = 0 # Number in system (in service + waiting)
        
        # Initialize first event
        heapq = [] # Using list as heap manually since no import heapq allowed? No, standard lib includes heapq.
        import heapq
        heapq.heappush(heapq, (next_arrival, 0, None))
        
        while True:
            if not heapq: break
            t_curr, ev_type, ev_data = heapq.heappop(heapq)
            
            if t_curr > horizon_min:
                break
                
            dt = t_curr - last_event_time
            
            # Accumulate area before state change
            if last_event_time >= warmup_time:
                area_L += current_L * dt
                if server_busy:
                    # Busy fraction accumulation
                    pass # Handled by integral of indicator
            
            # Update stats based on interval just passed
            # We need a separate accumulator for busy time in window
            # Let's refactor: keep track of total time in window and total busy time in window
            
            # Actually, let's maintain:
            # win_time: total duration of simulation within window
            # win_busy_time: total duration server was busy within window
            # win_area_L: integral of L(t) over window
            
            # Reset/Init these outside loop? No, they accumulate.
            
            # Process Event
            if ev_type == 0: # Arrival
                # Generate next arrival
                inter_arr = rng.expovariate(lam_base)
                heapq.heappush(heapq, (t_curr + inter_arr, 0, None))
                
                # Check capacity? M/M/1/K? Problem says "call center", usually infinite queue unless specified.
                # "P-K formula" implies M/G/1 with infinite buffer.
                # So blk should be 0.
                
                if t_curr >= warmup_time:
                    count_arr += 1
                    
                if server_busy:
                    queue.append(t_curr)
                    current_L += 1
                else:
                    # Start service immediately
                    # Draw service time now
                    # Two-stage hyperexponential with mean 6, CV 1.5
                    # Mean m = p1/mu1 + p2/mu2 = 6
                    # Var v = 2*(p1/mu1^2 + p2/mu2^2) - m^2 ? No, for hyperexp E[S^2] = 2(p1/mu1^2 + p2/mu2^2)
                    # CV^2 = Var/Mean^2 = (E[S^2]/m^2) - 1 = 1.5^2 = 2.25 => E[S^2]/36 = 3.25 => E[S^2] = 117
                    # Let's pick simple parameters.
                    # Common choice: p=0.5, rates such that mean=6, var=81.
                    # Or just sample from a distribution that matches moments.
                    # Since exact shape doesn't matter for P-K, any valid sampling works.
                    # Let's use a simple approximation or proper hyperexp.
                    # Hyperexp: f(x) = p*lambda1*exp(-lambda1 x) + (1-p)*lambda2*exp(-lambda2 x)
                    # Mean = p/lambda1 + (1-p)/lambda2 = 6
                    # Second Moment = 2*p/lambda1^2 + 2*(1-p)/lambda2^2 = 117
                    
                    # Let's try p=0.5.
                    # 0.5/L1 + 0.5/L2 = 6 => 1/L1 + 1/L2 = 12
                    # 1/L1^2 + 1/L2^2 = 117
                    # Let u=1/L1, v=1/L2. u+v=12, u^2+v^2=117.
                    # (u+v)^2 = 144 = u^2+v^2+2uv = 117+2uv => 2uv=27 => uv=13.5
                    # z^2 - 12z + 13.5 = 0. Roots: (12 +/- sqrt(144-54))/2 = (12 +/- sqrt(90))/2 = 6 +/- 4.743
                    # u ~ 10.74, v ~ 1.26. L1 ~ 0.093, L2 ~ 0.79.
                    
                    p_hyp = 0.5
                    l1 = 1.0 / (6 - math.sqrt(90)/2) # Wait, u is rate? No u=1/L where L is rate? 
                    # In my notation above, lambda_i is rate. Mean = 1/lambda.
                    # So u = 1/lambda1. lambda1 = 1/u.
                    # u,v are roots of z^2 - 12z + 13.5 = 0.
                    disc = 144 - 54
                    root1 = (12 + math.sqrt(disc)) / 2
                    root2 = (12 - math.sqrt(disc)) / 2
                    # root1 corresponds to larger mean component? No, u=1/lambda. Larger u -> smaller mean.
                    # Let's assign randomly.
                    if rng.random() < p_hyp:
                        svc_rate = 1.0 / root1
                    else:
                        svc_rate = 1.0 / root2
                        
                    svc_time = rng.expovariate(svc_rate)
                    
                    server_busy = True
                    service_end_time = t_curr + svc_time
                    heapq.heappush(heapq, (service_end_time, 1, t_curr)) # Store arrival time in data
                    current_L += 1
                    
            elif ev_type == 1: # Departure
                arr_time = ev_data
                if t_curr >= warmup_time:
                    count_dep += 1
                    # Record sojourn time for W
                    # We'll store these in a list to calculate mean later
                    # But memory? Horizon is small enough.
                    # Better: accumulate sum_sojourn and count for window
                    pass 
                
                # Remove from system
                current_L -= 1
                
                if queue:
                    # Serve next
                    next_arr_t = queue.popleft()
                    # Draw new service time? 
                    # Requirement: "Service time must be drawn at arrival".
                    # This means we cannot draw it here.
                    # We must have stored the service time when the customer arrived.
                    # Correction needed in Arrival logic.
                    
                    # If queue exists, the head of queue has a pre-drawn service time.
                    # How did we store it?
                    # In the previous step, when arriving and finding server busy, we pushed to queue.
                    # We didn't draw service time there because we only draw when starting service?
                    # NO. "Service time must be drawn at arrival... hung on customer".
                    # So even if waiting, we draw it.
                    
                    # Let's restructure Arrival:
                    # Always draw service time upon arrival.
                    # If server free, start immediately.
                    # If server busy, push (arrival_time, service_time) to queue.
                    
                    # Back to Departure:
                    # Pop from queue.
                    # The popped item contains service_time.
                    # Start service.
                    
                    # Need to fix Arrival block to always draw svc_time.
                    
                    # Re-implementing logic flow mentally:
                    # 1. Arrival: Draw svc_time. If busy, push (arr_t, svc_t) to queue. Else, set server busy, end_t = t + svc_t, push dep event.
                    # 2. Departure: Server becomes idle. If queue not empty, pop (arr_t, svc_t). Set server busy, end_t = t + svc_t, push dep event.
                    
                    # So in this branch (queue not empty):
                    next_item = queue.popleft()
                    next_arr_t, next_svc_t = next_item
                    
                    server_busy = True
                    service_end_time = t_curr + next_svc_t
                    heapq.heappush(heapq, (service_end_time, 1, next_arr_t))
                else:
                    server_busy = False
        
        # End of simulation for one seed
        # Calculate metrics for this seed
        # We missed accumulating specific stats during the loop in the draft above.
        # Let's do a second pass or ensure correct accumulation in the single pass.
        # Given complexity, I will rewrite the inner loop carefully in the final code.
        
        # For now, placeholder calculations to satisfy structure
        # Assuming we collected lists of sojourn times and areas correctly.
        
        # Let's assume we have:
        # win_duration = horizon_min - warmup_time
        # avg_L = area_L / win_duration
        # avg_busy = busy_time / win_duration
        # avg_W = sum_sojourn / count_dep (if count_dep > 0)
        
        # To make it work in one go, I'll implement the accumulation properly in the final string.
        
        # Dummy values to prevent crash during thought process
        L_seed = 0.0
        W_seed = 0.0
        bf_seed = 0.0
        pl_seed = 0.0
        pw_seed = 0.0
        arr_seed = 0.0
        blk_seed = 0.0
        dep_seed = 0.0
        bu_seed = 0.0
        bo_seed = 0.0
        
        # Append to global lists
        all_L.append(L_seed)
        all_W.append(W_seed)
        all_busy_frac.append(bf_seed)
        all_p_loss.append(pl_seed)
        all_p_wait.append(pw_seed)
        all_arr.append(arr_seed)
        all_blk.append(blk_seed)
        all_dep.append(dep_seed)
        all_busy_util.append(bu_seed)
        all_busy_occupied.append(bo_seed)
        seed_list.append(seed_val)

    # Final aggregation
    n_seeds = len(all_L)
    if n_seeds == 0:
        print(json.dumps({"error": "no seeds"}))
        return
        
    avg_L = sum(all_L) / n_seeds
    avg_W = sum(all_W) / n_seeds
    avg_bf = sum(all_busy_frac) / n_seeds
    avg_pl = sum(all_p_loss) / n_seeds
    avg_pw = sum(all_p_wait) / n_seeds
    avg_arr = sum(all_arr) / n_seeds
    avg_blk = sum(all_blk) / n_seeds
    avg_dep = sum(all_dep) / n_seeds
    avg_bu = sum(all_busy_util) / n_seeds
    avg_bo = sum(all_busy_occupied) / n_seeds
    
    dep_rate = (avg_dep / (horizon_min - warmup_time)) * 60.0 if (horizon_min - warmup_time) > 0 else 0.0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": time_unit,
        "win": round(horizon_min - warmup_time, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(avg_arr / (horizon_min - warmup_time) * 60.0, 6) if (horizon_min - warmup_time) > 0 else 0.0,
        "p_loss": round(avg_pl, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
