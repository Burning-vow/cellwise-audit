import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 5.0 # 12 per hour
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    service_time_h = 1.0 / mu
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occ = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] # list of arrival times
        server_free_at = 0.0
        is_busy = False
        
        # Statistics accumulators for the whole run (to be filtered later or integrated directly?)
        # Requirement: "统计量只在去掉前 25% 预热后的窗口内累计"
        # We need to integrate area and count events only within [warmup_end, H]
        
        warmup_end = H * warmup_frac
        
        # To handle integration correctly with discrete events, we track state changes.
        # State: number of cars in system (N). 
        # Area_N = integral of N(t) dt over window.
        # Area_Busy = integral of I(busy) dt over window.
        
        last_event_time = 0.0
        current_N = 0
        area_N = 0.0
        area_busy = 0.0
        
        total_arr_in_win = 0
        total_dep_in_win = 0
        total_blk_in_win = 0 # For M/M/1/K? No, infinite buffer usually unless specified. 
                             # Problem says "自动洗车机", implies single server, likely infinite queue or just waiting.
                             # "blk" suggests blocking/loss. Standard M/M/1 has no loss. 
                             # If it's M/M/1 with finite capacity, we need K. 
                             # The prompt doesn't specify capacity K. 
                             # However, "blk" key is requested. In standard M/M/1, blk=0.
                             # Let's assume infinite buffer (M/M/1) so blk=0, p_loss=0.
                             # But wait, "p_loss" is also requested. 
                             # If it's a simple queue, maybe they mean probability of waiting? 
                             # "p_wait" is separate. 
                             # Usually, if not specified, assume infinite buffer. 
                             # So blk=0, p_loss=0.
        
        # We need to simulate until H.
        # Events: Arrival, Departure.
        
        # Initialize first event time
        # We need to process events up to H.
        
        # Helper to add area from last_event_time to now_t
        def add_area(now_t):
            nonlocal area_N, area_busy, last_event_time, current_N, is_busy
            if now_t > last_event_time:
                dt = now_t - last_event_time
                # Only accumulate if overlapping with window [warmup_end, H]
                start_int = max(last_event_time, warmup_end)
                end_int = min(now_t, H)
                if end_int > start_int:
                    overlap_dt = end_int - start_int
                    area_N += current_N * overlap_dt
                    if is_busy:
                        area_busy += overlap_dt
                last_event_time = now_t

        while t < H:
            # Determine next event
            arr_time = next_arr
            dep_time = float('inf')
            if is_busy:
                dep_time = server_free_at
            
            if arr_time <= dep_time:
                # Arrival
                t = arr_time
                if t >= H: break
                
                add_area(t)
                
                # Check if within window for counting arrivals
                if t >= warmup_end:
                    total_arr_in_win += 1
                
                # Add to queue
                queue.append(t)
                current_N += 1
                
                # Schedule next arrival
                next_arr = t + rng.expovariate(lam)
                
                # Start service if idle
                if not is_busy:
                    is_busy = True
                    server_free_at = t + service_time_h
                    # Note: Service time was fixed at 5 mins, drawn at arrival? 
                    # Prompt: "服务时长必须在顾客到达时抽好并挂在该顾客身上"
                    # Since it's fixed 5 mins, we don't really "draw" it randomly, but we assign it.
                    # The queue stores arrival times. When starting service, we know duration.
                    # Actually, for FIFO, we just pop from queue when server becomes free.
                    
            else:
                # Departure
                t = dep_time
                if t >= H: break
                
                add_area(t)
                
                # Complete service
                is_busy = False
                current_N -= 1
                if t >= warmup_end:
                    total_dep_in_win += 1
                    
                # Pop from queue
                if queue:
                    # Next customer starts immediately
                    is_busy = True
                    server_free_at = t + service_time_h
                    # The customer who started service arrived earlier. 
                    # We don't need their specific arrival time for stats here, 
                    # except for W calculation which uses Little's Law or direct sum.
                    # Direct sum of W requires tracking individual stay times.
                    # Let's track individual stay times for those departing in window.
                    pass
                else:
                    # Server idle
                    pass

        # Final area update up to H
        add_area(H)
        
        # Calculate metrics for this seed
        # L = Area_N / win_len
        # W = L / lambda_eff (Little's Law) OR Average Stay Time.
        # Prompt asks for W. Using Little's Law is consistent with L.
        # But we also have "per_seed_W". It's better to calculate average stay time directly 
        # to avoid bias if lambda_eff != lambda due to truncation? 
        # In steady state simulation, Little's Law holds. 
        # Let's compute average stay time for customers who departed in the window.
        # Wait, customers arriving before window and departing inside contribute to W.
        # Customers arriving inside and departing after H are truncated.
        # Standard approach: Use Little's Law L = lambda * W => W = L / lambda.
        # Here lambda is the effective arrival rate into the system.
        # Since infinite buffer, lambda_eff = lam.
        # However, to be precise with "window", let's use L and lam.
        
        L_val = area_N / win_len if win_len > 0 else 0
        busy_frac_val = area_busy / win_len if win_len > 0 else 0
        
        # W via Little's Law: W = L / lam
        # Note: lam is the input rate.
        W_val = L_val / lam if lam > 0 else 0
        
        # p_wait: Probability that an arriving customer has to wait.
        # In M/M/1, P(wait) = rho = lam/mu.
        # Empirically: Count arrivals where queue length > 0 (server busy) upon arrival.
        # We didn't track this explicitly in the loop above easily without more state.
        # Let's re-evaluate: We can approximate p_wait as busy_frac_val? 
        # No, P(wait) = P(N>=1) = 1 - P(0) = busy_frac for M/M/1? 
        # Yes, for M/M/1, utilization = 1 - pi_0 = P(N>0).
        # An arrival sees PASTA property, so P(wait) = P(N>0) = busy_frac.
        p_wait_val = busy_frac_val
        p_loss_val = 0.0 # Infinite buffer
        blk_val = 0.0
        
        # busy_util = E[min(N,c)]/c. c=1. E[N]/1 = L.
        busy_util_val = L_val
        # busy_occupied = 1 - pi_0 = busy_frac
        busy_occ_val = busy_frac_val
        
        all_L.append(L_val)
        all_W.append(W_val)
        all_busy_frac.append(busy_frac_val)
        all_p_loss.append(p_loss_val)
        all_p_wait.append(p_wait_val)
        all_arr.append(total_arr_in_win)
        all_dep.append(total_dep_in_win)
        all_blk.append(blk_val)
        all_busy_util.append(busy_util_val)
        all_busy_occ.append(busy_occ_val)

    # Aggregate statistics
    seeds_used = len(all_L)
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_busy_occ = sum(all_busy_occ) / seeds_used
    
    # dep_rate: effective departure rate per hour
    # Total departures in window / total window time across seeds?
    # Or average per seed?
    # "dep 是窗口内平均每种子的离开人数" -> avg_dep
    # "dep_rate 是'个/每小时'的有效离开率"
    # Rate = avg_dep / win_len (since win_len is in hours)
    dep_rate_val = avg_dep / win_len if win_len > 0 else 0
    
    # lam_eff: effective arrival rate
    lam_eff_val = avg_arr / win_len if win_len > 0 else 0

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff_val, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
