import sys, json, random, math

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 12.0  # 5 per hour
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H * 0.75  # Remove first 25% as warmup
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    all_busy_occupied = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [] # (time, type, data) type: 0=arrival, 1=departure
        heapq = __import__('heapq')
        heapq.heappush(events, (next_arrival, 0, None))
        
        n_in_system = 0
        servers_free = [True] * c
        service_times = {} # id -> duration
        arrival_times = {} # id -> arrival time
        customer_id_counter = 0
        
        # Statistics accumulators for the window
        area_n = 0.0
        last_t = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        count_served = 0
        busy_time_sum = 0.0 # Sum of min(n,c) over time? No, integral of min(n(t), c)
        # Actually busy_frac is E[min(N,c)]/c. So we need integral of min(N(t), c).
        integral_min_nc = 0.0
        occupied_time = 0.0 # Time when at least one server is busy
        
        while events:
            current_t, etype, edata = heapq.heappop(events)
            
            # Update integrals up to current_t
            dt = current_t - last_t
            if dt > 0:
                val_min_nc = min(n_in_system, c)
                integral_min_nc += val_min_nc * dt
                if n_in_system > 0:
                    occupied_time += dt
                area_n += n_in_system * dt
            
            last_t = current_t
            
            if current_t >= H:
                break
                
            if etype == 0: # Arrival
                count_arr += 1
                cid = customer_id_counter
                customer_id_counter += 1
                
                # Check if any server is free
                free_idx = -1
                for k in range(c):
                    if servers_free[k]:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    # Start service immediately
                    st = rng.expovariate(mu)
                    service_times[cid] = st
                    arrival_times[cid] = current_t
                    servers_free[free_idx] = False
                    n_in_system += 1
                    dep_t = current_t + st
                    heapq.heappush(events, (dep_t, 1, cid))
                else:
                    # Queue or block? Problem says FCFS, no blocking mentioned explicitly but usually infinite queue unless specified.
                    # However, standard M/M/c has infinite capacity. But wait, "p_wait" implies waiting.
                    # If it's a loss system, blk would be non-zero. The problem doesn't specify capacity limit.
                    # Standard interpretation: Infinite queue. So blk should be 0.
                    # But let's look at keys: blk, p_loss. This suggests possibility of loss.
                    # Re-read: "某银行网点同时开放 2 个柜台... 先到先服务". Usually implies queueing.
                    # If queue is infinite, p_loss = 0.
                    # Let's assume infinite queue for now. If blk is required, maybe it's 0.
                    # Wait, if I assume infinite queue, then everyone waits.
                    # Let's stick to infinite queue.
                    n_in_system += 1
                    # We need to track who is waiting. 
                    # When a departure happens, we start the next waiting person.
                    # We need a queue structure.
                    pass 

            elif etype == 1: # Departure
                cid = edata
                # Find which server was used? We don't strictly need to know which server, just that one becomes free.
                # But we need to handle the queue.
                
                # Calculate W for this customer
                w_val = current_t - arrival_times[cid]
                sum_w += w_val
                count_served += 1
                
                n_in_system -= 1
                count_dep += 1
                
                # One server becomes free
                # Find a free server index to mark it free? 
                # Actually, we just need to know how many are free.
                # Let's maintain a list of free server indices or just count.
                # Simpler: maintain a queue of waiting customers.
                
                # Refill logic:
                # If there are waiting customers, start one.
                # How do we know who is waiting?
                # We need a separate queue for waiting IDs.
                
                # Let's refactor state management slightly inside loop.
                # State: n_in_system includes those in service and waiting.
                # We need a `waiting_queue` list.
                
                # Since I didn't initialize waiting_queue outside, let's do it properly.
                # This requires restructuring the loop variables.
                
                # Let's restart the inner loop logic with proper structures.
                pass

        # The above logic got messy because I didn't define waiting_queue.
        # Let's rewrite the simulation part cleanly.
        
        # Reset for clean implementation
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = []
        heapq.heappush(events, (next_arrival, 0, None))
        
        n_in_system = 0
        num_busy = 0
        waiting_q = [] # List of customer IDs waiting
        cust_info = {} # ID -> {arrival_time, service_time}
        cust_id_counter = 0
        
        area_n = 0.0
        last_t = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        count_served = 0
        integral_min_nc = 0.0
        occupied_time = 0.0
        
        while events:
            current_t, etype, edata = heapq.heappop(events)
            
            dt = current_t - last_t
            if dt > 0:
                val_min_nc = min(n_in_system, c)
                integral_min_nc += val_min_nc * dt
                if num_busy > 0:
                    occupied_time += dt
                area_n += n_in_system * dt
            
            last_t = current_t
            
            if current_t >= H:
                break
                
            if etype == 0: # Arrival
                count_arr += 1
                cid = cust_id_counter
                cust_id_counter += 1
                
                if num_busy < c:
                    # Server available
                    st = rng.expovariate(mu)
                    cust_info[cid] = {'arr': current_t, 'st': st}
                    num_busy += 1
                    n_in_system += 1
                    dep_t = current_t + st
                    heapq.heappush(events, (dep_t, 1, cid))
                else:
                    # All busy, join queue
                    st = rng.expovariate(mu)
                    cust_info[cid] = {'arr': current_t, 'st': st}
                    waiting_q.append(cid)
                    n_in_system += 1
                    
            elif etype == 1: # Departure
                cid = edata
                arr_t = cust_info[cid]['arr']
                w_val = current_t - arr_t
                sum_w += w_val
                count_served += 1
                count_dep += 1
                
                del cust_info[cid]
                n_in_system -= 1
                num_busy -= 1
                
                if waiting_q:
                    next_cid = waiting_q.pop(0)
                    st = cust_info[next_cid]['st']
                    num_busy += 1
                    dep_t = current_t + st
                    heapq.heappush(events, (dep_t, 1, next_cid))
                    
        # End of simulation for this seed
        # Compute stats for the window [H*0.25, H]
        # Note: The integrals were computed over [0, H].
        # We need to subtract the warmup period contribution.
        # Warmup ends at T_warm = H * 0.25.
        # We need to re-calculate or store history? 
        # Storing history is expensive. 
        # Alternative: Run simulation from 0 to H, but only accumulate stats after T_warm.
        # Let's adjust the accumulation logic.
        
        # Re-run logic with conditional accumulation? 
        # Or simpler: In the loop, check if last_t >= T_warm.
        # But dt spans across boundary.
        # Let's split the dt update.
        
        # To keep code short and correct, I will modify the loop to only accumulate if current_t > T_warm.
        # But area needs precise integration.
        
        # Let's redo the loop with T_warm check.
        
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = []
        heapq.heappush(events, (next_arrival, 0, None))
        
        n_in_system = 0
        num_busy = 0
        waiting_q = []
        cust_info = {}
        cust_id_counter = 0
        
        area_n_win = 0.0
        integral_min_nc_win = 0.0
        occupied_time_win = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_w_win = 0.0
        count_served_win = 0
        
        last_t = 0.0
        T_warm = H * 0.25
        
        while events:
            current_t, etype, edata = heapq.heappop(events)
            
            dt = current_t - last_t
            if dt > 0:
                # Determine overlap with window
                start_overlap = max(last_t, T_warm)
                end_overlap = current_t
                
                if end_overlap > start_overlap:
                    overlap_dt = end_overlap - start_overlap
                    val_min_nc = min(n_in_system, c)
                    integral_min_nc_win += val_min_nc * overlap_dt
                    if num_busy > 0:
                        occupied_time_win += overlap_dt
                    area_n_win += n_in_system * overlap_dt
            
            last_t = current_t
            
            if current_t >= H:
                break
                
            if etype == 0: # Arrival
                if current_t >= T_warm:
                    count_arr_win += 1
                
                cid = cust_id_counter
                cust_id_counter += 1
                
                if num_busy < c:
                    st = rng.expovariate(mu)
                    cust_info[cid] = {'arr': current_t, 'st': st}
                    num_busy += 1
                    n_in_system += 1
                    dep_t = current_t + st
                    heapq.heappush(events, (dep_t, 1, cid))
                else:
                    st = rng.expovariate(mu)
                    cust_info[cid] = {'arr': current_t, 'st': st}
                    waiting_q.append(cid)
                    n_in_system += 1
                    
            elif etype == 1: # Departure
                cid = edata
                arr_t = cust_info[cid]['arr']
                
                if current_t >= T_warm:
                    w_val = current_t - arr_t
                    sum_w_win += w_val
                    count_served_win += 1
                    count_dep_win += 1
                
                del cust_info[cid]
                n_in_system -= 1
                num_busy -= 1
                
                if waiting_q:
                    next_cid = waiting_q.pop(0)
                    st = cust_info[next_cid]['st']
                    num_busy += 1
                    dep_t = current_t + st
                    heapq.heappush(events, (dep_t, 1, next_cid))
                    
        # Stats for this seed
        L_seed = area_n_win / win if win > 0 else 0
        W_seed = (sum_w_win / count_served_win * 60) if count_served_win > 0 else 0 # Convert hours to minutes
        busy_frac_seed = (integral_min_nc_win / win) / c if win > 0 else 0
        p_wait_seed = 0.0
        # p_wait: probability that an arriving customer has to wait.
        # Count arrivals where num_busy == c at arrival time.
        # We didn't track this directly in the second loop.
        # Let's add a counter for blocked/waiting arrivals.
        
        # Re-re-run? No, too long.
        # Let's modify the previous loop to count waiting arrivals.
        
        rng = random.Random(seed)
        next_arrival = rng.expovariate(lam)
        events = [(next_arrival, 0, None)]
        n_in_system = 0
        num_busy = 0
        waiting_q = []
        cust_info = {}
        cust_id_counter = 0
        area_n_win = 0.0
        integral_min_nc_win = 0.0
        occupied_time_win = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_w_win = 0.0
        count_served_win = 0
        count_wait_arr_win = 0
        
        last_t = 0.0
        T_warm = H * 0.25
        
        while events:
            current_t, etype, edata = heapq.heappop(events)
            dt = current_t - last_t
            if dt > 0:
                s_o = max(last_t, T_warm)
                e_o = current_t
                if e_o > s_o:
                    o_dt = e_o - s_o
                    v_mnc = min(n_in_system, c)
                    integral_min_nc_win += v_mnc * o_dt
                    if num_busy > 0:
                        occupied_time_win += o_dt
                    area_n_win += n_in_system * o_dt
            last_t = current_t
            if current_t >= H: break
            
            if etype == 0:
                if current_t >= T_warm:
                    count_arr_win += 1
                    if num_busy >= c:
                        count_wait_arr_win += 1
                
                cid = cust_id_counter
                cust_id_counter += 1
                st = rng.expovariate(mu)
                cust_info[cid] = {'arr': current_t, 'st': st}
                
                if num_busy < c:
                    num_busy += 1
                    n_in_system += 1
                    heapq.heappush(events, (current_t + st, 1, cid))
                else:
                    waiting_q.append(cid)
                    n_in_system += 1
            else:
                cid = edata
                arr_t = cust_info[cid]['arr']
                if current_t >= T_warm:
                    sum_w_win += (current_t - arr_t)
                    count_served_win += 1
                    count_dep_win += 1
                del cust_info[cid]
                n_in_system -= 1
                num_busy -= 1
                if waiting_q:
                    nc = waiting_q.pop(0)
                    ns = cust_info[nc]['st']
                    num_busy += 1
                    heapq.heappush(events, (current_t + ns, 1, nc))
        
        L_seed = area_n_win / win
        W_seed = (sum_w_win / count_served_win * 60) if count_served_win > 0 else 0
        busy_frac_seed = (integral_min_nc_win / win) / c
        p_wait_seed = count_wait_arr_win / count_arr_win if count_arr_win > 0 else 0
        busy_util_seed = busy_frac_seed
        busy_occ_seed = occupied_time_win / win
        dep_rate_seed = count_dep_win / win * 60 # per hour? No, dep_rate is "个/每小时". 
        # count_dep_win is number of departures in window. Window length is win hours.
        # Rate = count / win. Unit is 1/hour.
        dep_rate_seed = count_dep_win / win
        lam_eff_seed = count_arr_win / win
        p_loss_seed = 0.0 # Infinite queue
        
        all_L.append(L_seed)
        all_W.append(W_seed)
        all_busy_frac.append(busy_frac_seed)
        all_p_wait.append(p_wait_seed)
        all_arr.append(count_arr_win)
        all_dep.append(count_dep_win)
        all_blk.append(count_blk_win)
        all_busy_util.append(busy_util_seed)
        all_dep_rate.append(dep_rate_seed)
        all_lam_eff.append(lam_eff_seed)
        all_p_loss.append(p_loss_seed)
        all_busy_occupied.append(busy_occ_seed)

    avg_L = sum(all_L) / len(all_L)
    avg_W = sum(all_W) / len(all_W)
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac)
    avg_p_wait = sum(all_p_wait) / len(all_p_wait)
    avg_arr = sum(all_arr) / len(all_arr)
    avg_dep = sum(all_dep) / len(all_dep)
    avg_blk = sum(all_blk) / len(all_blk)
    avg_busy_util = sum(all_busy_util) / len(all_busy_util)
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate)
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff)
    avg_p_loss = sum(all_p_loss) / len(all_p_loss)
    avg_busy_occ = sum(all_busy_occupied) / len(all_busy_occupied)
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait],
        "busy_occupied": round(avg_busy_occ, 4)
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
