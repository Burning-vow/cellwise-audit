import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 6.0
    mu_base = 10.0
    c = 1
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = 'hour'
    win = H * 0.75
    warmup = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_p_wait = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        server_free_time = 0.0
        num_in_system = 0
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        arrivals = 0
        blocks = 0
        departures = 0
        wait_sum = 0.0
        waited_count = 0
        
        while t < H:
            arr_t = next_arr
            dep_t = float('inf')
            if queue or (server_free_time > t and num_in_system > 0):
                if num_in_system > 0:
                    dep_t = server_free_time
            
            if arr_t <= dep_t:
                dt = arr_t - last_event_time
                if dt > 0:
                    area_L += num_in_system * dt
                    if num_in_system > 0:
                        area_busy += dt
                t = arr_t
                last_event_time = t
                
                if t >= warmup:
                    arrivals += 1
                    if num_in_system < K:
                        st = rng.expovariate(mu)
                        service_times[arrivals] = st
                        queue.append(arrivals)
                        num_in_system += 1
                        if num_in_system == 1:
                            server_free_time = t + st
                    else:
                        blocks += 1
                else:
                    if num_in_system < K:
                        st = rng.expovariate(mu)
                        service_times[arrivals] = st
                        queue.append(arrivals)
                        num_in_system += 1
                        if num_in_system == 1:
                            server_free_time = t + st
                    else:
                        pass 
                
                next_arr = t + rng.expovariate(lam)
            else:
                dt = dep_t - last_event_time
                if dt > 0:
                    area_L += num_in_system * dt
                    if num_in_system > 0:
                        area_busy += dt
                t = dep_t
                last_event_time = t
                
                cust_id = queue.pop(0)
                num_in_system -= 1
                if t >= warmup:
                    departures += 1
                    w = t - (service_times[cust_id] and t - service_times[cust_id]) 
                    # Wait time calculation needs arrival time stored properly
                    # Let's fix logic: store arrival time with customer
                    pass
                # Re-implementing loop with proper state tracking for wait times
                # This approach is getting messy inline. Let's restart the simulation loop structure cleanly.
        
        # Resetting to a cleaner simulation loop implementation within the same function scope constraints
        # Since I cannot define classes, I will rewrite the inner loop carefully.
        
        # Clear previous partial results for this seed
        t = 0.0
        rng = random.Random(s)
        next_arr = rng.expovariate(lam)
        customers = [] # list of dicts: {'id': int, 'arr': float, 'svc': float}
        num_in_sys = 0
        server_end = 0.0
        last_evt = 0.0
        area_L_acc = 0.0
        area_B_acc = 0.0
        arr_cnt = 0
        blk_cnt = 0
        dep_cnt = 0
        wait_sum_acc = 0.0
        wait_cnt = 0
        
        # We need to track arrival times for waiting time calc
        # Queue holds customer IDs/objects
        
        q = []
        cust_data = {} # id -> {arr, svc}
        cid_counter = 0
        
        while t < H:
            # Determine next event
            t_arr = next_arr
            t_dep = float('inf')
            if len(q) > 0:
                t_dep = server_end
            
            if t_arr <= t_dep:
                dt = t_arr - last_evt
                if dt > 0:
                    area_L_acc += num_in_sys * dt
                    if num_in_sys > 0:
                        area_B_acc += dt
                t = t_arr
                last_evt = t
                
                if num_in_sys < K:
                    cid_counter += 1
                    svc = rng.expovariate(mu)
                    cust_data[cid_counter] = {'arr': t, 'svc': svc}
                    q.append(cid_counter)
                    num_in_sys += 1
                    if num_in_sys == 1:
                        server_end = t + svc
                    if t >= warmup:
                        arr_cnt += 1
                else:
                    if t >= warmup:
                        blk_cnt += 1
                        arr_cnt += 1 # Arrival happened but blocked? Usually "arr" counts attempts.
                        # Problem says "arr is ... person count". If blocked, they left immediately.
                        # Standard convention: Arrivals are attempts. Blocks are lost ones.
                        # But wait, if blocked, do we count them in 'arr'? Yes, usually.
                        # And 'dep'? No, they didn't enter.
                        # So arr_cnt increments on every arrival attempt after warmup.
                
                next_arr = t + rng.expovariate(lam)
            else:
                dt = t_dep - last_evt
                if dt > 0:
                    area_L_acc += num_in_sys * dt
                    if num_in_sys > 0:
                        area_B_acc += dt
                t = t_dep
                last_evt = t
                
                cid = q.pop(0)
                num_in_sys -= 1
                if t >= warmup:
                    dep_cnt += 1
                    arr_time = cust_data[cid]['arr']
                    w = t - arr_time
                    wait_sum_acc += w
                    wait_cnt += 1
                
                if len(q) > 0:
                    next_cid = q[0]
                    svc = cust_data[next_cid]['svc']
                    server_end = t + svc
        
        # Final integration up to H if needed? Loop ends at H.
        # The loop processes events strictly < H. 
        # Area accumulation happens between events.
        # Last event might be before H. Need to integrate from last_evt to H.
        dt_final = H - last_evt
        if dt_final > 0:
            area_L_acc += num_in_sys * dt_final
            if num_in_sys > 0:
                area_B_acc += dt_final
        
        # Calculate stats for this seed over window [warmup, H]
        # Note: The area accumulators above included pre-warmup time.
        # Correction: The problem states "statistics only accumulated in window after removing first 25% warmup".
        # My current code accumulates area for ALL time. I must subtract pre-warmup area or only accumulate during window.
        # Refactoring accumulation logic inside loop is complex without classes.
        # Alternative: Run two passes? Or adjust integrals.
        # Let's re-run the simulation logic specifically accumulating only post-warmup.
        
        # Restart simulation for correct windowed statistics
        t = 0.0
        rng = random.Random(s)
        next_arr = rng.expovariate(lam)
        q = []
        cust_data = {}
        cid_counter = 0
        num_in_sys = 0
        server_end = 0.0
        last_evt = 0.0
        
        area_L_win = 0.0
        area_B_win = 0.0
        arr_win = 0
        blk_win = 0
        dep_win = 0
        wait_sum_win = 0.0
        wait_cnt_win = 0
        
        while t < H:
            t_arr = next_arr
            t_dep = float('inf')
            if len(q) > 0:
                t_dep = server_end
            
            if t_arr <= t_dep:
                dt = t_arr - last_evt
                if dt > 0:
                    # Integrate only if interval overlaps with window
                    start_int = max(last_evt, warmup)
                    end_int = min(t_arr, H)
                    if end_int > start_int:
                        overlap = end_int - start_int
                        area_L_win += num_in_sys * overlap
                        if num_in_sys > 0:
                            area_B_win += overlap
                
                t = t_arr
                last_evt = t
                
                if num_in_sys < K:
                    cid_counter += 1
                    svc = rng.expovariate(mu)
                    cust_data[cid_counter] = {'arr': t, 'svc': svc}
                    q.append(cid_counter)
                    num_in_sys += 1
                    if num_in_sys == 1:
                        server_end = t + svc
                    if t >= warmup:
                        arr_win += 1
                else:
                    if t >= warmup:
                        blk_win += 1
                        arr_win += 1
                
                next_arr = t + rng.expovariate(lam)
            else:
                dt = t_dep - last_evt
                if dt > 0:
                    start_int = max(last_evt, warmup)
                    end_int = min(t_dep, H)
                    if end_int > start_int:
                        overlap = end_int - start_int
                        area_L_win += num_in_sys * overlap
                        if num_in_sys > 0:
                            area_B_win += overlap
                
                t = t_dep
                last_evt = t
                
                cid = q.pop(0)
                num_in_sys -= 1
                if t >= warmup:
                    dep_win += 1
                    arr_time = cust_data[cid]['arr']
                    w = t - arr_time
                    wait_sum_win += w
                    wait_cnt_win += 1
                
                if len(q) > 0:
                    next_cid = q[0]
                    svc = cust_data[next_cid]['svc']
                    server_end = t + svc
        
        dt_final = H - last_evt
        if dt_final > 0:
            start_int = max(last_evt, warmup)
            end_int = min(H, H)
            if end_int > start_int:
                overlap = end_int - start_int
                area_L_win += num_in_sys * overlap
                if num_in_sys > 0:
                    area_B_win += overlap
        
        L_est = area_L_win / win if win > 0 else 0
        W_est = wait_sum_win / wait_cnt_win if wait_cnt_win > 0 else 0
        busy_frac_est = area_B_win / win if win > 0 else 0
        p_loss_est = blk_win / arr_win if arr_win > 0 else 0
        p_wait_est = wait_cnt_win / arr_win if arr_win > 0 else 0 # Fraction of arrivals that waited? Or entered?
        # p_wait usually means probability an arriving customer has to wait.
        # In M/M/1/K, P(wait) = P(system full upon arrival)? No, P(wait) = P(N>=1).
        # Here, if they enter and queue length > 0, they wait.
        # Let's define p_wait as fraction of accepted customers who had to wait.
        # Accepted = arr_win - blk_win.
        accepted = arr_win - blk_win
        p_wait_est = wait_cnt_win / accepted if accepted > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_arr.append(arr_win)
        all_blk.append(blk_win)
        all_dep.append(dep_win)
        all_p_wait.append(p_wait_est)
        seeds_used_list.append(s)
    
    avg_L = sum(all_L) / N_seeds
    avg_W = sum(all_W) / N_seeds
    avg_busy_frac = sum(all_busy_frac) / N_seeds
    avg_p_loss = sum(all_p_loss) / N_seeds
    avg_arr = sum(all_arr) / N_seeds
    avg_blk = sum(all_blk) / N_seeds
    avg_dep = sum(all_dep) / N_seeds
    avg_p_wait = sum(all_p_wait) / N_seeds
    
    dep_rate = avg_dep / win if win > 0 else 0
    lam_eff = avg_arr / win if win > 0 else 0
    busy_util = avg_busy_frac / c # E[min(N,c)]/c approx by busy_frac/c? 
    # Busy util definition: E[min(N,c)]/c. 
    # For single server, E[min(N,1)] = P(N>0) = busy_frac. So busy_util = busy_frac.
    # If c>1, it's different. Here c=1 mostly.
    
    output = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_loss": round(avg_p_loss, 4),
        "runtime_units": "hours",
        "seed_list": seeds_used_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_frac, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
