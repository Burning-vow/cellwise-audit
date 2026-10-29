import sys, json, random, math
from collections import deque

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if i + 1 < len(argv):
            args[argv[i].strip('-')] = argv[i+1]
    
    seeds_n = int(args.get('seeds', 1))
    horizon = float(args.get('horizon', 100.0)) # Default to hours? Problem says H unit matches time_unit. Let's assume hour for internal logic or minute? 
    # "time_unit 填你程序内部时间轴的单位". Let's use minutes internally as service is fixed 6 mins.
    # But arrival rate is per hour. Let's stick to Minutes for time axis to avoid float precision issues with small numbers? Or Hours?
    # Service = 6 min = 0.1 hr. Arrival = 8/hr.
    # Let's use MINUTES as time_unit.
    # Horizon H passed from CLI. If default is not specified, what is it? The prompt says "H 是整数样式的仿真时域长度... 解析时请写成 float(...)".
    # If no arg, we need a default. Let's assume the caller provides it. If not, pick a reasonable default like 1000 minutes?
    # Actually, standard practice: if --horizon is missing, maybe use a large number.
    # Let's check constraints. "不带任何参数时也必须能用默认值跑完".
    # I will set default horizon to 10000 minutes (approx 166 hours) to ensure steady state.
    
    seed_start = int(args.get('seed-start', 0))
    pert = args.get('pert', 'none')
    
    time_unit = "minute"
    lam_per_hr = 8.0
    mu_service_min = 6.0
    
    if pert == 'lam_up':
        lam_per_hr *= 1.1
    elif pert == 'mu_up':
        mu_service_min /= 1.1 # Faster service -> higher throughput? Or lower time? "mu_up" usually means rate up. Rate = 1/time. So time down.
    elif pert == 'c_up':
        pass # c=1 fixed
        
    lam_per_min = lam_per_hr / 60.0
    
    total_horizon_min = horizon if 'horizon' in args else 10000.0
    warmup_frac = 0.25
    warmup_end = total_horizon_min * warmup_frac
    
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
    
    actual_seeds_used = 0
    used_seed_list = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival_time = rng.expovariate(lam_per_min)
        
        queue = deque()
        server_free_time = 0.0
        is_server_busy = False
        
        # Statistics accumulators for this seed
        area_N = 0.0
        last_event_time = 0.0
        current_N = 0
        
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0 # Sum of waiting times (in system) for completed cars
        
        # For busy fraction calculation via integration
        # We need E[min(N,1)] which is just P(N>=1). 
        # And 1 - pi_0. Same thing.
        # We also need busy_util = E[min(N,c)]/c. Since c=1, same as above.
        # Wait, definition: busy_util = E[min(N,c)]/c. busy_occupied = 1-pi_0.
        # In M/M/1, these are identical.
        
        while t < total_horizon_min:
            # Determine next event
            events = []
            if next_arrival_time <= total_horizon_min:
                events.append(('arr', next_arrival_time))
            
            if is_server_busy and server_free_time <= total_horizon_min:
                events.append(('dep', server_free_time))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Update area before changing state
            dt = etime - last_event_time
            if last_event_time >= warmup_end:
                area_N += current_N * dt
            
            last_event_time = etime
            t = etime
            
            if etype == 'arr':
                count_arr += 1
                # Generate service time (fixed 6 min, but attached to car)
                svc_time = mu_service_min
                
                if not is_server_busy:
                    # Start service immediately
                    is_server_busy = True
                    server_free_time = t + svc_time
                    # Car enters system at t, leaves at server_free_time
                    # Waiting time in system = server_free_time - t
                    # But we record departure stats later.
                    # Store arrival time in queue? No, direct start.
                    # We need to track this car's arrival time to calculate W upon departure.
                    # Since it starts immediately, its "arrival" is now.
                    # We can push a tuple (arrival_time, service_duration) to a "in-service" tracker?
                    # Simpler: When dep happens, we know who left.
                    # If queue was empty, the departing car is the one that arrived at 't'.
                    # We need to store the arrival time of the car currently being served.
                    # Let's add a variable `current_car_arrival_time`.
                    current_car_arrival_time = t
                    current_N += 1
                else:
                    # Server busy, join queue
                    queue.append((t, svc_time))
                    current_N += 1
                
                # Schedule next arrival
                next_arrival_time = t + rng.expovariate(lam_per_min)
                
            elif etype == 'dep':
                # A car finishes service
                count_dep += 1
                # Calculate W for this car
                w_val = t - current_car_arrival_time
                if last_event_time > warmup_end: # Only accumulate stats after warmup? 
                    # Usually W is average over completed jobs in window.
                    # Prompt: "统计量只在去掉前 25% 预热后的窗口内累计"
                    # This implies we only count departures that happen AFTER warmup_end?
                    # Or do we count the W of cars that departed after warmup?
                    # Standard discrete event sim: Accumulate metrics based on events occurring in the measurement window.
                    # So if dep time > warmup_end, add to sum_W and count for avg.
                    if t > warmup_end:
                        sum_W += w_val
                
                current_N -= 1
                
                if queue:
                    # Next car starts service
                    arr_t, svc_dur = queue.popleft()
                    current_car_arrival_time = arr_t
                    server_free_time = t + svc_dur
                    # is_server_busy remains True
                else:
                    is_server_busy = False
                    server_free_time = 0.0 # Reset
            
            # Handle potential blockage? 
            # Problem doesn't specify capacity limit. "自动洗车机... 先到先洗". Implies infinite queue.
            # So blk should be 0. p_loss 0.
            
        # End of simulation for this seed
        
        # Calculate final stats for this seed
        # L = Area_N / Window_Length
        win_len = total_horizon_min - warmup_end
        if win_len <= 0:
            win_len = 1e-9
            
        L_est = area_N / win_len
        
        # W = sum_W / count_dep_in_window
        # We need count of departures in window.
        # Re-scan? No, we didn't store individual dep times.
        # We incremented count_dep for ALL deps.
        # We need count_dep_win.
        # Let's fix the loop to track count_dep_win.
        
        # Correction: I need to re-run or modify logic to capture count_dep_win.
        # Since I can't easily re-run without duplicating code, I'll adjust the logic inside the loop.
        # I will restart the inner loop logic mentally to ensure correctness in the final code.
        
        # Busy Fraction:
        # Integral of indicator(N>0) / win_len.
        # I tracked area_N (integral of N). I need integral of I(N>0).
        # Let's call it area_I.
        
        # I will rewrite the core loop in the final code to include:
        # area_I, count_dep_win, sum_W_win.
        
        # For now, assuming the structure below handles it correctly.
        
        # Placeholder calculations using variables that WILL be defined in the corrected loop:
        # L_est = area_N / win_len
        # W_est = sum_W_win / count_dep_win if count_dep_win > 0 else 0
        # busy_frac_est = area_I / win_len
        # p_loss_est = 0.0
        # p_wait_est = ... ? 
        # "p_wait": Probability of waiting? Or fraction of time spent waiting?
        # Usually in Little's Law context, W is mean sojourn time.
        # p_wait often refers to probability an arriving customer has to wait (P(N>=1)).
        # Let's assume p_wait = P(arrival finds server busy).
        # We need to count arrivals that found server busy vs total arrivals in window.
        
        # Let's refine the metric collection in the code generation.
        
        actual_seeds_used += 1
        used_seed_list.append(current_seed)
        
        # These will be populated by the correct loop implementation
        # For the sake of generating the single block, I will implement the full loop properly.
        
        # Resetting placeholders to force proper implementation in the final string
        pass 

    # The above loop structure was draft. Now writing the final clean code.
    
    results = {
        "L": 0, "W": 0, "busy_frac": 0, "runtime_units": 0, 
        "seed_list": [], "seeds_used": 0, "time_unit": "minute", "win": 0,
        "arr": 0, "blk": 0, "busy_util": 0, "dep": 0, "dep_rate": 0, 
        "lam_eff": 0, "p_loss": 0, "p_wait": 0,
        "per_seed_L": [], "per_seed_W": [], "per_seed_busy_frac": [], 
        "per_seed_p_loss": [], "per_seed_p_wait": []
    }
    
    # Re-implementing main logic cleanly
    
    seed_stats = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival_time = rng.expovariate(lam_per_min)
        
        queue = deque()
        server_free_time = 0.0
        is_server_busy = False
        current_car_arrival_time = 0.0
        
        # Stats
        area_N = 0.0
        area_I = 0.0 # Integral of I(N>0)
        last_event_time = 0.0
        current_N = 0
        
        count_arr_total = 0
        count_dep_total = 0
        
        # Window-specific stats
        count_arr_win = 0
        count_dep_win = 0
        sum_W_win = 0.0
        count_wait_win = 0 # Arrivals that had to wait (server busy)
        
        while t < total_horizon_min:
            events = []
            if next_arrival_time <= total_horizon_min:
                events.append(('arr', next_arrival_time))
            if is_server_busy and server_free_time <= total_horizon_min:
                events.append(('dep', server_free_time))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            dt = etime - last_event_time
            if last_event_time >= warmup_end:
                area_N += current_N * dt
                if current_N > 0:
                    area_I += dt
            
            last_event_time = etime
            t = etime
            
            if etype == 'arr':
                count_arr_total += 1
                if t > warmup_end:
                    count_arr_win += 1
                    
                svc_time = mu_service_min
                
                if not is_server_busy:
                    is_server_busy = True
                    server_free_time = t + svc_time
                    current_car_arrival_time = t
                    current_N += 1
                else:
                    queue.append((t, svc_time))
                    current_N += 1
                    if t > warmup_end:
                        count_wait_win += 1
                
                next_arrival_time = t + rng.expovariate(lam_per_min)
                
            elif etype == 'dep':
                count_dep_total += 1
                w_val = t - current_car_arrival_time
                
                if t > warmup_end:
                    count_dep_win += 1
                    sum_W_win += w_val
                
                current_N -= 1
                
                if queue:
                    arr_t, svc_dur = queue.popleft()
                    current_car_arrival_time = arr_t
                    server_free_time = t + svc_dur
                else:
                    is_server_busy = False
                    server_free_time = 0.0
        
        win_len = total_horizon_min - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = area_N / win_len
        W_est = sum_W_win / count_dep_win if count_dep_win > 0 else 0.0
        busy_frac_est = area_I / win_len
        p_loss_est = 0.0 # Infinite queue
        p_wait_est = count_wait_win / count_arr_win if count_arr_win > 0 else 0.0
        
        seed_stats.append({
            'L': L_est, 'W': W_est, 'busy_frac': busy_frac_est,
            'p_loss': p_loss_est, 'p_wait': p_wait_est,
            'arr': count_arr_win, 'dep': count_dep_win, 'blk': 0
        })
        
    n_seeds = len(seed_stats)
    if n_seeds == 0:
        print(json.dumps(results))
        return
        
    avg_L = sum(s['L'] for s in seed_stats) / n_seeds
    avg_W = sum(s['W'] for s in seed_stats) / n_seeds
    avg_busy_frac = sum(s['busy_frac'] for s in seed_stats) / n_seeds
    avg_p_loss = sum(s['p_loss'] for s in seed_stats) / n_seeds
    avg_p_wait = sum(s['p_wait'] for s in seed_stats) / n_seeds
    avg_arr = sum(s['arr'] for s in seed_stats) / n_seeds
    avg_dep = sum(s['dep'] for s in seed_stats) / n_seeds
    avg_blk = sum(s['blk'] for s in seed_stats) / n_seeds
    
    # busy_util = E[min(N,c)]/c. With c=1, min(N,1) is I(N>=1). So same as busy_frac.
    avg_busy_util = avg_busy_frac
    # busy_occupied = 1 - pi_0. pi_0 is prob empty. 1-pi_0 is prob busy. Same as busy_frac.
    avg_busy_occ = avg_busy_frac
    
    dep_rate = avg_dep / (win_len / 60.0) if win_len > 0 else 0 # Per hour
    lam_eff = dep_rate # Conservation of flow in stable system
    
    results.update({
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": n_seeds,
        "seed_list": used_seed_list,
        "seeds_used": n_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(s['L'], 4) for s in seed_stats],
        "per_seed_W": [round(s['W'], 4) for s in seed_stats],
        "per_seed_busy_frac": [round(s['busy_frac'], 4) for s in seed_stats],
        "per_seed_p_loss": [round(s['p_loss'], 4) for s in seed_stats],
        "per_seed_p_wait": [round(s['p_wait'], 4) for s in seed_stats]
    })
    
    print(json.dumps(results))

if __name__ == "__main__":
    main()
