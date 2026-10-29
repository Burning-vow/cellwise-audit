import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    # Arrival rate: 8 per hour -> lambda = 8 /hr
    # Service time: mean 12 min = 0.2 hr -> mu = 1/0.2 = 5 /hr
    lam_base = 8.0
    mu_base = 5.0
    c = 2
    K = 4 # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
        K = 5
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
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        # We need to track departure times for each car currently in system
        # Since it's M/M/c/K, we can just keep a list of remaining service times or absolute end times
        # But standard DES uses event queue. Let's use an event list approach or simple loop.
        # Given small scale, event list is fine.
        
        events = [] # (time, type, data) type: 0=arrival, 1=departure
        heapq_imported = False
        try:
            import heapq
            heapq_imported = True
        except:
            pass
            
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * H
        
        # Accumulators for area integration (only after warmup)
        area_n = 0.0
        time_since_last_event = 0.0
        last_t = 0.0
        
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_w_times = 0.0 # Sum of waiting times? No, W is avg time in system usually? 
        # Problem says "W (minutes)". Usually W is average time in system (sojourn time).
        # Let's assume W = Average Time in System.
        # To calculate average time in system, we need sum of sojourn times / number of departures.
        # Or use Little's Law L = lam_eff * W. If we compute L via area, we can derive W.
        # However, direct measurement is better.
        # We need to store arrival time for each customer to calculate sojourn time upon departure.
        
        # Customer tracking
        # When a customer arrives, they get a unique ID and arrival time.
        # When they depart, we add (t - arrival_time) to sum_sojourn.
        
        cust_id_counter = 0
        active_customers = {} # id -> arrival_time
        
        # Event Queue
        # Initialize with first arrival
        events.append((next_arrival, 0, None)) # 0: arrival
        
        while events:
            if not heapq_imported:
                events.sort(key=lambda x: x[0])
            
            current_t, etype, edata = events.pop(0) if not heapq_imported else heapq.heappop(events)
            
            # Integrate area from last_t to current_t
            dt = current_t - last_t
            if last_t >= warmup_end:
                area_n += n_in_system * dt
            elif current_t > warmup_end:
                # Partial overlap
                overlap_dt = current_t - warmup_end
                area_n += n_in_system * overlap_dt
                
            last_t = current_t
            
            if current_t > H:
                break
                
            if etype == 0: # Arrival
                count_arr += 1
                if n_in_system < K:
                    n_in_system += 1
                    # Schedule departure
                    svc_time = rng.expovariate(mu)
                    dep_time = current_t + svc_time
                    events.append((dep_time, 1, cust_id_counter))
                    active_customers[cust_id_counter] = current_t
                    cust_id_counter += 1
                else:
                    count_blk += 1
                
                # Schedule next arrival
                next_arrival = current_t + rng.expovariate(lam)
                events.append((next_arrival, 0, None))
                
            elif etype == 1: # Departure
                cid = edata
                if cid in active_customers:
                    arr_t = active_customers.pop(cid)
                    sojourn = current_t - arr_t
                    if last_t >= warmup_end or arr_t >= warmup_end:
                        # Only count if the entire stay or at least part of it is in window?
                        # Standard practice: Count customers who DEPART within the window.
                        # Their sojourn time is fully observed.
                        if current_t >= warmup_end:
                            sum_w_times += sojourn
                            count_dep += 1
                    
                    n_in_system -= 1

        # Calculate metrics for this seed
        win_len = H - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        L_avg = area_n / win_len
        
        # Busy fraction: proportion of time system is not empty (n > 0)
        # We didn't integrate busy time separately. Let's re-run logic or approximate?
        # Better: Track busy time during simulation.
        # I missed tracking busy time explicitly in the loop above.
        # Let's fix by adding a variable `area_busy` and updating it similarly.
        
        # Re-simulation needed because I forgot to track busy time and wait time properly in the single pass above?
        # Actually, I can compute busy time if I tracked transitions.
        # Let's restart the inner loop logic slightly more carefully for accuracy.
        
        # Resetting for correct calculation
        rng = random.Random(seed)
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        events = [(next_arrival, 0, None)]
        cust_id_counter = 0
        active_customers = {}
        
        area_n = 0.0
        area_busy = 0.0 # Time where n > 0
        sum_sojourn = 0.0
        count_dep_win = 0
        count_arr_win = 0
        count_blk_win = 0
        
        last_t = 0.0
        
        while events:
            if not heapq_imported:
                events.sort(key=lambda x: x[0])
            
            current_t, etype, edata = events.pop(0) if not heapq_imported else heapq.heappop(events)
            
            dt = current_t - last_t
            
            # Update areas only if we are past warmup start
            if last_t >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
            elif current_t > warmup_end:
                overlap_dt = current_t - warmup_end
                area_n += n_in_system * overlap_dt
                if n_in_system > 0:
                    area_busy += overlap_dt
            
            last_t = current_t
            
            if current_t > H:
                break
                
            if etype == 0: # Arrival
                if current_t >= warmup_end:
                    count_arr_win += 1
                
                if n_in_system < K:
                    n_in_system += 1
                    svc_time = rng.expovariate(mu)
                    dep_time = current_t + svc_time
                    events.append((dep_time, 1, cust_id_counter))
                    active_customers[cust_id_counter] = current_t
                    cust_id_counter += 1
                else:
                    if current_t >= warmup_end:
                        count_blk_win += 1
                
                next_arrival = current_t + rng.expovariate(lam)
                events.append((next_arrival, 0, None))
                
            elif etype == 1: # Departure
                cid = edata
                if cid in active_customers:
                    arr_t = active_customers.pop(cid)
                    sojourn = current_t - arr_t
                    n_in_system -= 1
                    
                    if current_t >= warmup_end:
                        sum_sojourn += sojourn
                        count_dep_win += 1

        # Metrics
        L_val = area_n / win_len if win_len > 0 else 0
        busy_frac_val = area_busy / win_len if win_len > 0 else 0
        p_loss_val = count_blk_win / count_arr_win if count_arr_win > 0 else 0
        W_val_min = (sum_sojourn / count_dep_win * 60) if count_dep_win > 0 else 0
        
        # busy_util = E[min(N,c)]/c
        # Need to integrate min(n, c)
        # I didn't track that. Approximation or re-calc?
        # For strict compliance, let's assume we can derive it or skip if too complex.
        # But prompt asks for it.
        # Let's do a quick third pass or modify second pass.
        # Modifying second pass is better.
        
        # Re-running again with full tracking
        rng = random.Random(seed)
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        events = [(next_arrival, 0, None)]
        cust_id_counter = 0
        active_customers = {}
        
        area_n = 0.0
        area_busy = 0.0
        area_min_nc = 0.0
        sum_sojourn = 0.0
        count_dep_win = 0
        count_arr_win = 0
        count_blk_win = 0
        count_wait_win = 0 # Customers who waited? P_wait usually prob of waiting.
        # In M/M/c/K, waiting means joining queue. Queue length > 0.
        # A customer waits if upon arrival, all servers are busy (n >= c).
        
        last_t = 0.0
        
        while events:
            if not heapq_imported:
                events.sort(key=lambda x: x[0])
            
            current_t, etype, edata = events.pop(0) if not heapq_imported else heapq.heappop(events)
            
            dt = current_t - last_t
            
            if last_t >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
                area_min_nc += min(n_in_system, c) * dt
            elif current_t > warmup_end:
                overlap_dt = current_t - warmup_end
                area_n += n_in_system * overlap_dt
                if n_in_system > 0:
                    area_busy += overlap_dt
                area_min_nc += min(n_in_system, c) * overlap_dt
            
            last_t = current_t
            
            if current_t > H:
                break
                
            if etype == 0: # Arrival
                if current_t >= warmup_end:
                    count_arr_win += 1
                    # Check if waits: if n_in_system >= c (all servers busy)
                    if n_in_system >= c:
                        count_wait_win += 1
                
                if n_in_system < K:
                    n_in_system += 1
                    svc_time = rng.expovariate(mu)
                    dep_time = current_t + svc_time
                    events.append((dep_time, 1, cust_id_counter))
                    active_customers[cust_id_counter] = current_t
                    cust_id_counter += 1
                else:
                    if current_t >= warmup_end:
                        count_blk_win += 1
                
                next_arrival = current_t + rng.expovariate(lam)
                events.append((next_arrival, 0, None))
                
            elif etype == 1: # Departure
                cid = edata
                if cid in active_customers:
                    arr_t = active_customers.pop(cid)
                    sojourn = current_t - arr_t
                    n_in_system -= 1
                    
                    if current_t >= warmup_end:
                        sum_sojourn += sojourn
                        count_dep_win += 1

        L_val = area_n / win_len if win_len > 0 else 0
        busy_frac_val = area_busy / win_len if win_len > 0 else 0
        p_loss_val = count_blk_win / count_arr_win if count_arr_win > 0 else 0
        W_val_min = (sum_sojourn / count_dep_win * 60) if count_dep_win > 0 else 0
        busy_util_val = (area_min_nc / win_len) / c if win_len > 0 else 0
        p_wait_val = count_wait_win / count_arr_win if count_arr_win > 0 else 0
        dep_rate_val = count_dep_win / win_len if win_len > 0 else 0
        lam_eff_val = count_arr_win / win_len if win_len > 0 else 0
        
        all_L.append(L_val)
        all_W.append(W_val_min)
        all_busy_frac.append(busy_frac_val)
        all_p_loss.append(p_loss_val)
        all_p_wait.append(p_wait_val)
        all_arr.append(count_arr_win)
        all_blk.append(count_blk_win)
        all_dep.append(count_dep_win)
        all_busy_util.append(busy_util_val)
        all_dep_rate.append(dep_rate_val)
        all_lam_eff.append(lam_eff_val)

    seeds_used = len(all_L)
    seed_list = [seed_start + i for i in range(seeds_used)]
    
    def avg(lst):
        return sum(lst)/len(lst) if lst else 0.0
        
    res = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_loss": avg(all_p_loss),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": H - 0.25*H,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_wait": avg(all_p_wait),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
