import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam = 4.0 # per hour
    mu = 10.0 # per hour (6 min mean -> 10/hr)
    c = 1
    
    if args.pert == 'lam_up': lam *= 1.1
    elif args.pert == 'mu_up': mu *= 1.1
    elif args.pert == 'c_up': c += 1
    
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occ = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    time_unit = "hour"
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {} # cust_id -> duration
        
        queue = [] # list of cust_ids waiting
        serving_cust = None
        serve_end_time = None
        
        n_in_sys = 0
        area_n = 0.0
        last_event_time = 0.0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_area = 0.0 # sum of (wait_time) for customers who waited? No, W is avg stay. Need total time in system for those who departed in window? 
        # Standard way: L = integral N dt / T. W = L / lambda_eff. Or track individual times.
        # Let's track individual departure times and arrival times to compute W directly from samples in window?
        # But prompt says "area-type quantities must be integrated before state change".
        # For W, usually we use Little's Law or sample average of sojourn times of completed services in the window.
        # Let's accumulate sojourn times of customers who depart within the statistical window.
        
        total_sojourn_time_samples = 0.0
        count_departures_for_w = 0
        
        # To handle "service time drawn at arrival":
        # We need a counter for customer IDs.
        cust_id_counter = 0
        
        while t < horizon:
            # Determine next event
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if serving_cust is not None and serve_end_time <= horizon:
                events.append(('dep', serve_end_time))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            # Integrate area up to ev_time
            dt = ev_time - last_event_time
            area_n += n_in_sys * dt
            last_event_time = ev_time
            t = ev_time
            
            if ev_type == 'arr':
                # Arrival
                dur = rng.expovariate(mu)
                service_times[cust_id_counter] = dur
                
                if t >= win_start:
                    arr_count_win += 1
                
                if len(queue) == 0 and serving_cust is None:
                    # Start service immediately
                    serving_cust = cust_id_counter
                    serve_end_time = t + dur
                    n_in_sys += 1
                else:
                    # Join queue
                    queue.append(cust_id_counter)
                    n_in_sys += 1
                
                cust_id_counter += 1
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                # Departure
                cid = serving_cust
                # Calculate sojourn time
                # We need arrival time of this customer. 
                # Since we didn't store it, let's add a dict for arrival times too.
                # Refactoring slightly inside loop logic isn't allowed by "no classes", but I can maintain dicts.
                # Wait, I missed storing arrival time. I'll assume standard DES structure where we track it.
                # Since I can't go back, I will rely on Little's Law for W calculation globally, 
                # OR I must have stored arrival times. 
                # The prompt implies strict implementation. I should have stored arrival times.
                # However, since I am generating code now, I will include arrival time tracking.
                
                # Correction: I need to track arrival times.
                # Let's restart the inner loop logic mentally to ensure correctness.
                pass 

        # Re-implementing the simulation loop correctly with arrival time tracking
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        cust_arrival_times = {}
        cust_service_durations = {}
        
        queue = []
        serving_cust = None
        serve_end_time = None
        
        n_in_sys = 0
        area_n = 0.0
        last_event_time = 0.0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        total_sojourn_time_samples = 0.0
        count_departures_for_w = 0
        
        cust_id_counter = 0
        
        while t < horizon:
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if serving_cust is not None and serve_end_time <= horizon:
                events.append(('dep', serve_end_time))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - last_event_time
            area_n += n_in_sys * dt
            last_event_time = ev_time
            t = ev_time
            
            if ev_type == 'arr':
                dur = rng.expovariate(mu)
                cust_service_durations[cust_id_counter] = dur
                cust_arrival_times[cust_id_counter] = t
                
                if t >= win_start:
                    arr_count_win += 1
                
                if len(queue) == 0 and serving_cust is None:
                    serving_cust = cust_id_counter
                    serve_end_time = t + dur
                    n_in_sys += 1
                else:
                    queue.append(cust_id_counter)
                    n_in_sys += 1
                
                cust_id_counter += 1
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                cid = serving_cust
                arr_t = cust_arrival_times.pop(cid)
                serv_dur = cust_service_durations.pop(cid)
                sojourn = t - arr_t
                
                if t >= win_start:
                    dep_count_win += 1
                    total_sojourn_time_samples += sojourn
                    count_departures_for_w += 1
                
                n_in_sys -= 1
                
                if queue:
                    next_cid = queue.pop(0)
                    serving_cust = next_cid
                    serve_end_time = t + cust_service_durations[next_cid]
                else:
                    serving_cust = None
                    serve_end_time = None
        
        # Post-simulation stats for this seed
        if win_len > 0:
            L_est = area_n / win_len
            busy_frac_est = (area_n - (win_len * 0)) / win_len # Area of N>=1? 
            # Busy fraction is E[min(N,1)]. 
            # We need to integrate indicator(N>0).
            # I didn't integrate that separately. 
            # Alternative: Busy time = Total time - Idle time.
            # Idle time occurs when N=0.
            # Let's re-calculate busy time properly.
            # Actually, simpler: Track idle time.
            pass

        # Redoing integration for busy time and wait probability
        # It is cleaner to track these during the loop.
        
        # Resetting for final clean implementation
        t = 0.0
        next_arr = rng.expovariate(lam)
        cust_arrival_times = {}
        cust_service_durations = {}
        queue = []
        serving_cust = None
        serve_end_time = None
        n_in_sys = 0
        area_n = 0.0
        area_busy = 0.0 # Integral of 1 if N>0 else 0
        area_wait = 0.0 # Integral of 1 if Queue>0 else 0 (for P_wait definition? Usually P_wait is prob an arriving customer waits. 
                        # Prompt says p_wait. In M/M/1, P(wait) = rho. 
                        # "Probability that an arriving customer has to wait".
                        # This is a discrete event stat, not area. 
                        # Count arrivals that found server busy.
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_arrivals_win = 0
        
        total_sojourn_time_samples = 0.0
        count_departures_for_w = 0
        cust_id_counter = 0
        last_event_time = 0.0
        
        while t < horizon:
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if serving_cust is not None and serve_end_time <= horizon:
                events.append(('dep', serve_end_time))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - last_event_time
            area_n += n_in_sys * dt
            if n_in_sys > 0:
                area_busy += dt
            # P_wait is defined as fraction of arrivals that wait. 
            # So we don't integrate for P_wait, we count.
            
            last_event_time = ev_time
            t = ev_time
            
            if ev_type == 'arr':
                dur = rng.expovariate(mu)
                cust_service_durations[cust_id_counter] = dur
                cust_arrival_times[cust_id_counter] = t
                
                if t >= win_start:
                    arr_count_win += 1
                    # Did they wait? If server busy or queue non-empty
                    if serving_cust is not None or len(queue) > 0:
                        wait_arrivals_win += 1
                
                if len(queue) == 0 and serving_cust is None:
                    serving_cust = cust_id_counter
                    serve_end_time = t + dur
                    n_in_sys += 1
                else:
                    queue.append(cust_id_counter)
                    n_in_sys += 1
                
                cust_id_counter += 1
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                cid = serving_cust
                arr_t = cust_arrival_times.pop(cid)
                serv_dur = cust_service_durations.pop(cid)
                sojourn = t - arr_t
                
                if t >= win_start:
                    dep_count_win += 1
                    total_sojourn_time_samples += sojourn
                    count_departures_for_w += 1
                
                n_in_sys -= 1
                
                if queue:
                    next_cid = queue.pop(0)
                    serving_cust = next_cid
                    serve_end_time = t + cust_service_durations[next_cid]
                else:
                    serving_cust = None
                    serve_end_time = None

        # Finalize Seed Stats
        if win_len > 0:
            L_est = area_n / win_len
            busy_frac_est = area_busy / win_len
            p_wait_est = wait_arrivals_win / arr_count_win if arr_count_win > 0 else 0.0
            W_est = total_sojourn_time_samples / count_departures_for_w if count_departures_for_w > 0 else 0.0
            
            # Convert W to minutes if internal unit is hours
            # Internal time is hours. Service mean 6min = 0.1hr.
            # W_est is in hours. Multiply by 60.
            W_min = W_est * 60.0
            
            # Other metrics
            busy_util_est = busy_frac_est # c=1, min(N,1)/1 = busy_frac
            busy_occ_est = busy_frac_est # 1 - pi_0 approx busy_frac
            lam_eff_est = dep_count_win / win_len
            p_loss_est = blk_count_win / arr_count_win if arr_count_win > 0 else 0.0
            dep_rate_est = lam_eff_est # per hour
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_min)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            
            all_L.append(L_est)
            all_W.append(W_min)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(arr_count_win)
            all_dep.append(dep_count_win)
            all_blk.append(blk_count_win)
            all_busy_util.append(busy_util_est)
            all_busy_occ.append(busy_occ_est)
            all_lam_eff.append(lam_eff_est)
            all_p_loss.append(p_loss_est)
            all_dep_rate.append(dep_rate_est)

    def avg(lst): return sum(lst)/len(lst) if lst else 0.0
    
    res = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_wait": avg(all_p_wait),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win_len,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_loss": avg(all_p_loss),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
