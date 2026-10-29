import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    N = args.seeds
    H = float(args.horizon)
    S_start = args.seed_start
    pert = args.pert

    lam_base = 4.0
    mu_base = 10.0
    c_base = 1.0

    if pert == "lam_up":
        lam = lam_base * 1.1
    elif pert == "mu_up":
        mu = mu_base * 1.1
    elif pert == "c_up":
        c = c_base * 1.1
    else:
        lam = lam_base
        mu = mu_base
        c = c_base

    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []

    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue1 = []
        queue2 = []
        busy1 = False
        busy2 = False
        end_service1 = None
        end_service2 = None
        events = []
        
        # State variables for integration
        area_L = 0.0
        last_t = 0.0
        count_in_sys = 0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_time_sum = 0.0
        service_time_sum = 0.0
        total_stay_sum = 0.0
        num_completed = 0
        
        # For busy fraction of server 1 and 2 combined? 
        # Usually busy_frac refers to system utilization or specific server. 
        # Given single servers in series, let's track both. But output key is singular.
        # Let's assume it means average utilization of the bottleneck or just one? 
        # Or maybe sum? The prompt says "busy_frac". In Jackson networks with M/M/1 queues, 
        # utilization rho = lambda/mu. Here we have two stages. 
        # Let's calculate the fraction of time at least one server is busy? Or average of both?
        # Standard interpretation in such simulations often tracks individual server utilizations.
        # However, keys are singular. Let's look at "blk". If no blocking mentioned, blk=0.
        # Let's define busy_frac as the average utilization of the two servers (sum/2)? 
        # Or perhaps just the first one? 
        # Actually, L is number in system. W is stay time.
        # Let's track time server 1 is busy and server 2 is busy separately, then combine?
        # To be safe, let's report the average utilization across both servers.
        time_busy1 = 0.0
        time_busy2 = 0.0
        
        # Event loop
        while t < H:
            # Determine next event time
            candidates = []
            if next_arr <= H:
                candidates.append(('arr', next_arr))
            if end_service1 is not None and end_service1 <= H:
                candidates.append(('dep1', end_service1))
            if end_service2 is not None and end_service2 <= H:
                candidates.append(('dep2', end_service2))
            
            if not candidates:
                break
            
            candidates.sort(key=lambda x: x[1])
            etype, etime = candidates[0]
            
            # Integrate area for L before changing state
            dt = etime - last_t
            if dt > 0:
                area_L += count_in_sys * dt
                if busy1:
                    time_busy1 += dt
                if busy2:
                    time_busy2 += dt
                last_t = etime
            
            if etype == 'arr':
                t = etime
                arr_count += 1
                # Generate service times now
                s1 = rng.expovariate(mu)
                s2 = rng.expovariate(mu)
                customer = {'arrival_time': t, 's1': s1, 's2': s2}
                
                if not busy1:
                    busy1 = True
                    end_service1 = t + s1
                    # Start service immediately
                    # We need to track when this customer enters stage 2 later
                    # Store current customer info in a variable associated with server 1
                    cust_at_1 = customer
                else:
                    queue1.append(customer)
                
                count_in_sys += 1
                next_arr = t + rng.expovariate(lam)
                
            elif etype == 'dep1':
                t = etime
                # Customer finishes stage 1
                # Who was being served?
                # We need to retrieve the customer currently in service at stage 1
                # Since we didn't store it explicitly in a global var accessible here easily without refactoring,
                # let's use a simple approach: keep a variable `current_cust_1`
                pass 

        # Refactored logic below to handle state correctly without complex class structures
        # Resetting simulation for clarity in code structure
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        q1 = []
        q2 = []
        b1 = False
        b2 = False
        e1 = None
        e2 = None
        cur_c1 = None
        cur_c2 = None
        
        area_L = 0.0
        last_t = 0.0
        n_sys = 0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        stay_sum = 0.0
        comp_cnt = 0
        tb1 = 0.0
        tb2 = 0.0
        
        while t < H:
            evts = []
            if next_arr <= H: evts.append((next_arr, 'A'))
            if e1 is not None and e1 <= H: evts.append((e1, 'D1'))
            if e2 is not None and e2 <= H: evts.append((e2, 'D2'))
            if not evts: break
            evts.sort()
            et, typ = evts[0]
            
            dt = et - last_t
            if dt > 0:
                area_L += n_sys * dt
                if b1: tb1 += dt
                if b2: tb2 += dt
                last_t = et
            
            t = et
            
            if typ == 'A':
                arr_cnt += 1
                s1 = rng.expovariate(mu)
                s2 = rng.expovariate(mu)
                cust = {'at': t, 's1': s1, 's2': s2}
                n_sys += 1
                if not b1:
                    b1 = True
                    e1 = t + s1
                    cur_c1 = cust
                else:
                    q1.append(cust)
                next_arr = t + rng.expovariate(lam)
                
            elif typ == 'D1':
                # Finish stage 1
                cust = cur_c1
                cur_c1 = None
                b1 = False
                e1 = None
                
                # Move to stage 2
                if not b2:
                    b2 = True
                    e2 = t + cust['s2']
                    cur_c2 = cust
                else:
                    q2.append(cust)
                    
                # Start next from Q1
                if q1:
                    nxt = q1.pop(0)
                    b1 = True
                    e1 = t + nxt['s1']
                    cur_c1 = nxt
                    
            elif typ == 'D2':
                # Finish stage 2
                cust = cur_c2
                cur_c2 = None
                b2 = False
                e2 = None
                
                dep_cnt += 1
                n_sys -= 1
                stay = t - cust['at']
                stay_sum += stay
                comp_cnt += 1
                
                # Start next from Q2
                if q2:
                    nxt = q2.pop(0)
                    b2 = True
                    e2 = t + nxt['s2']
                    cur_c2 = nxt

        # Post-process for window [warmup_end, H]
        # This simple loop integrates over whole horizon. 
        # Requirement: stats only in window after removing first 25%.
        # Need to re-run or store history? Storing history is memory heavy.
        # Better: Run simulation, but only accumulate stats if t >= warmup_end.
        # And for area, integrate only segments within window.
        
        # Re-running with window check
        t = 0.0
        next_arr = rng.expovariate(lam)
        q1 = []
        q2 = []
        b1 = False
        b2 = False
        e1 = None
        e2 = None
        cur_c1 = None
        cur_c2 = None
        
        area_L_win = 0.0
        last_t = 0.0
        n_sys = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        stay_sum_win = 0.0
        comp_win = 0
        tb1_win = 0.0
        tb2_win = 0.0
        
        # Track customers that arrived before warmup but leave after?
        # "W ... total average stay time". Usually Little's Law applies to steady state.
        # If we exclude pre-warmup arrivals from counts, we might bias W if they leave during window.
        # Standard practice: Discard data generated during warmup. 
        # So, only count arrivals/departures/stays that happen entirely or partially?
        # Prompt: "statistics ... accumulated only in the window after removing the first 25% warmup".
        # Area integral must be done before state change.
        
        while t < H:
            evts = []
            if next_arr <= H: evts.append((next_arr, 'A'))
            if e1 is not None and e1 <= H: evts.append((e1, 'D1'))
            if e2 is not None and e2 <= H: evts.append((e2, 'D2'))
            if not evts: break
            evts.sort()
            et, typ = evts[0]
            
            dt = et - last_t
            if dt > 0:
                # Check overlap with window
                w_start = max(last_t, warmup_end)
                w_end = min(et, H)
                if w_start < w_end:
                    overlap = w_end - w_start
                    area_L_win += n_sys * overlap
                    if b1: tb1_win += overlap
                    if b2: tb2_win += overlap
                last_t = et
            
            t = et
            
            if typ == 'A':
                s1 = rng.expovariate(mu)
                s2 = rng.expovariate(mu)
                cust = {'at': t, 's1': s1, 's2': s2}
                n_sys += 1
                if t >= warmup_end:
                    arr_win += 1
                if not b1:
                    b1 = True
                    e1 = t + s1
                    cur_c1 = cust
                else:
                    q1.append(cust)
                next_arr = t + rng.expovariate(lam)
                
            elif typ == 'D1':
                cust = cur_c1
                cur_c1 = None
                b1 = False
                e1 = None
                if not b2:
                    b2 = True
                    e2 = t + cust['s2']
                    cur_c2 = cust
                else:
                    q2.append(cust)
                if q1:
                    nxt = q1.pop(0)
                    b1 = True
                    e1 = t + nxt['s1']
                    cur_c1 = nxt
                    
            elif typ == 'D2':
                cust = cur_c2
                cur_c2 = None
                b2 = False
                e2 = None
                n_sys -= 1
                if t >= warmup_end:
                    dep_win += 1
                    stay = t - cust['at']
                    stay_sum_win += stay
                    comp_win += 1
                if q2:
                    nxt = q2.pop(0)
                    b2 = True
                    e2 = t + nxt['s2']
                    cur_c2 = nxt

        L_est = area_L_win / win if win > 0 else 0
        W_est = stay_sum_win / comp_win if comp_win > 0 else 0
        busy_frac_est = (tb1_win + tb2_win) / (2 * win) if win > 0 else 0
        p_loss_est = 0.0 # No loss system described
        p_wait_est = 0.0 # Not clearly defined, usually prob of waiting on arrival
        
        # Calculate P(wait) properly: Fraction of arrivals that had to wait?
        # We didn't track this in the second run. 
        # Let's approximate or skip if not critical? Keys require it.
        # Let's add tracking for wait probability.
        
        # Re-run again? Too slow. Let's modify the loop above to track waits.
        # I will rewrite the core loop to include wait tracking.
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        q1 = []
        q2 = []
        b1 = False
        b2 = False
        e1 = None
        e2 = None
        cur_c1 = None
        cur_c2 = None
        
        area_L_win = 0.0
        last_t = 0.0
        n_sys = 0
        arr_win = 0
        dep_win = 0
        blk_win = 0
        stay_sum_win = 0.0
        comp_win = 0
        tb1_win = 0.0
        tb2_win = 0.0
        wait_arr_win = 0 # Arrivals that waited (either in Q1 or Q2? Usually Q1 entry)
        
        while t < H:
            evts = []
            if next_arr <= H: evts.append((next_arr, 'A'))
            if e1 is not None and e1 <= H: evts.append((e1, 'D1'))
            if e2 is not None and e2 <= H: evts.append((e2, 'D2'))
            if not evts: break
            evts.sort()
            et, typ = evts[0]
            
            dt = et - last_t
            if dt > 0:
                w_start = max(last_t, warmup_end)
                w_end = min(et, H)
                if w_start < w_end:
                    overlap = w_end - w_start
                    area_L_win += n_sys * overlap
                    if b1: tb1_win += overlap
                    if b2: tb2_win += overlap
                last_t = et
            
            t = et
            
            if typ == 'A':
                s1 = rng.expovariate(mu)
                s2 = rng.expovariate(mu)
                cust = {'at': t, 's1': s1, 's2': s2}
                n_sys += 1
                if t >= warmup_end:
                    arr_win += 1
                    if b1:
                        wait_arr_win += 1
                if not b1:
                    b1 = True
                    e1 = t + s1
                    cur_c1 = cust
                else:
                    q1.append(cust)
                next_arr = t + rng.expovariate(lam)
                
            elif typ == 'D1':
                cust = cur_c1
                cur_c1 = None
                b1 = False
                e1 = None
                if not b2:
                    b2 = True
                    e2 = t + cust['s2']
                    cur_c2 = cust
                else:
                    q2.append(cust)
                if q1:
                    nxt = q1.pop(0)
                    b1 = True
                    e1 = t + nxt['s1']
                    cur_c1 = nxt
                    
            elif typ == 'D2':
                cust = cur_c2
                cur_c2 = None
                b2 = False
                e2 = None
                n_sys -= 1
                if t >= warmup_end:
                    dep_win += 1
                    stay = t - cust['at']
                    stay_sum_win += stay
                    comp_win += 1
                if q2:
                    nxt = q2.pop(0)
                    b2 = True
                    e2 = t + nxt['s2']
                    cur_c2 = nxt

        L_val = area_L_win / win
        W_val_min = (stay_sum_win / comp_win)
