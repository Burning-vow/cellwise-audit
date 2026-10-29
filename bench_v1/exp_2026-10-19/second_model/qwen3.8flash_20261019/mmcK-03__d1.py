import random, json, argparse, math

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

    # Parameters in hours
    lam_base = 8.0
    mu_base = 5.0 # 60/12 = 5 per hour
    c = 2
    K = 4 # max capacity including service

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
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
    all_lam_eff = []
    all_dep_rate = []
    
    seeds_used_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # list of (arrival_time, service_duration)
        n_in_system = 0
        
        # Statistics accumulators (for area and counts)
        warmup_end = H * 0.25
        total_time_window = H - warmup_end
        
        area_n = 0.0
        last_event_time = 0.0
        last_n = 0
        
        arrivals_in_window = 0
        blocks_in_window = 0
        departures_in_window = 0
        wait_times_sum = 0.0 # sum of W_i for those who waited? No, L is avg number in system. W is avg time in system.
        # To get W, we need sum of (departure_time - arrival_time) for completed services in window.
        # But standard Little's Law uses average over the population. 
        # We will track sum of sojourn times for customers that DEPARTED within the window.
        # And count of such departures.
        sojourn_sum = 0.0
        
        # For busy fraction (station not empty), we integrate indicator(n>0)
        area_non_empty = 0.0
        
        # For busy_util E[min(N,c)]/c, we integrate min(n, c)
        area_min_nc = 0.0
        
        events = []
        
        def add_event(time, etype, data=None):
            events.append((time, etype, data))
            
        # Initial event
        add_event(next_arrival, 'arrival')
        
        while True:
            if not events:
                break
            
            # Find next event
            events.sort(key=lambda x: x[0])
            current_t, etype, data = events.pop(0)
            
            if current_t > H:
                break
                
            # Update areas before changing state
            dt = current_t - last_event_time
            if last_event_time >= warmup_end or current_t <= warmup_end:
                # Only accumulate if the interval overlaps with the measurement window
                overlap_start = max(last_event_time, warmup_end)
                overlap_end = min(current_t, H)
                if overlap_end > overlap_start:
                    overlap_dt = overlap_end - overlap_start
                    area_n += last_n * overlap_dt
                    area_non_empty += (1 if last_n > 0 else 0) * overlap_dt
                    area_min_nc += min(last_n, c) * overlap_dt
            
            last_event_time = current_t
            
            if etype == 'arrival':
                # Generate next arrival
                inter_arrival = rng.expovariate(lam)
                next_arrival_t = current_t + inter_arrival
                if next_arrival_t <= H:
                    add_event(next_arrival_t, 'arrival')
                
                # Check capacity
                if n_in_system < K:
                    # Accept
                    n_in_system += 1
                    last_n = n_in_system
                    
                    # Determine service start time
                    # Find earliest free server
                    min_free_idx = -1
                    min_free_time = float('inf')
                    for j in range(c):
                        if servers_free_at[j] < min_free_time:
                            min_free_time = servers_free_at[j]
                            min_free_idx = j
                    
                    # Service duration drawn now
                    svc_dur = rng.expovariate(mu)
                    
                    start_time = max(current_t, min_free_time)
                    end_time = start_time + svc_dur
                    
                    # Schedule departure
                    add_event(end_time, 'departure', {'start': start_time, 'end': end_time, 'arr': current_t})
                    
                    # Update server availability
                    servers_free_at[min_free_idx] = end_time
                    
                    if current_t >= warmup_end:
                        arrivals_in_window += 1
                else:
                    # Block
                    if current_t >= warmup_end:
                        blocks_in_window += 1
                        
            elif etype == 'departure':
                # Customer leaves
                n_in_system -= 1
                last_n = n_in_system
                
                arr_t = data['arr']
                dep_t = current_t
                sojourn = dep_t - arr_t
                
                if current_t >= warmup_end:
                    departures_in_window += 1
                    sojourn_sum += sojourn

        # Calculate metrics for this seed
        if total_time_window > 0:
            L_est = area_n / total_time_window
            busy_frac_est = area_non_empty / total_time_window
            busy_util_est = (area_min_nc / total_time_window) / c
            
            if departures_in_window > 0:
                W_est = (sojourn_sum / departures_in_window) * 60.0 # Convert hours to minutes
            else:
                W_est = 0.0
                
            p_loss_est = blocks_in_window / (arrivals_in_window + blocks_in_window) if (arrivals_in_window + blocks_in_window) > 0 else 0.0
            
            # p_wait: probability a customer waits. 
            # Need to track how many accepted customers had start_time > arrival_time.
            # This requires more detailed tracking during simulation. 
            # Let's re-run logic or store it. Since I can't easily go back, I'll approximate or fix code structure.
            # Actually, let's just count waits in the loop.
            
            # Re-evaluating: I didn't track wait counts. 
            # I will modify the loop above to track `waits_in_window`.
            pass 

        # Because I cannot edit the loop above without rewriting the whole block, 
        # I will rewrite the inner simulation part to include wait counting properly.
        
        # Resetting for correct implementation below
        # (The previous block was draft logic, replacing with complete single-pass logic)
        
        # --- Corrected Single Seed Simulation ---
        rng = random.Random(s)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        n_in_system = 0
        
        warmup_end = H * 0.25
        total_time_window = H - warmup_end
        
        area_n = 0.0
        area_non_empty = 0.0
        area_min_nc = 0.0
        last_event_time = 0.0
        last_n = 0
        
        arrivals_in_window = 0
        blocks_in_window = 0
        departures_in_window = 0
        sojourn_sum = 0.0
        waits_in_window = 0 # Count of customers who waited (start > arrival)
        
        events = [(next_arrival, 'arrival', None)]
        
        while events:
            events.sort(key=lambda x: x[0])
            current_t, etype, data = events.pop(0)
            
            if current_t > H:
                break
            
            dt_overlap_start = max(last_event_time, warmup_end)
            dt_overlap_end = min(current_t, H)
            if dt_overlap_end > dt_overlap_start:
                dt = dt_overlap_end - dt_overlap_start
                area_n += last_n * dt
                area_non_empty += (1 if last_n > 0 else 0) * dt
                area_min_nc += min(last_n, c) * dt
            
            last_event_time = current_t
            
            if etype == 'arrival':
                inter_arrival = rng.expovariate(lam)
                next_arrival_t = current_t + inter_arrival
                if next_arrival_t <= H:
                    events.append((next_arrival_t, 'arrival', None))
                
                if n_in_system < K:
                    n_in_system += 1
                    last_n = n_in_system
                    
                    min_free_idx = -1
                    min_free_time = float('inf')
                    for j in range(c):
                        if servers_free_at[j] < min_free_time:
                            min_free_time = servers_free_at[j]
                            min_free_idx = j
                    
                    svc_dur = rng.expovariate(mu)
                    start_time = max(current_t, min_free_time)
                    end_time = start_time + svc_dur
                    
                    events.append((end_time, 'departure', {'start': start_time, 'end': end_time, 'arr': current_t}))
                    servers_free_at[min_free_idx] = end_time
                    
                    if current_t >= warmup_end:
                        arrivals_in_window += 1
                        if start_time > current_t:
                            waits_in_window += 1
                else:
                    if current_t >= warmup_end:
                        blocks_in_window += 1
                        
            elif etype == 'departure':
                n_in_system -= 1
                last_n = n_in_system
                
                arr_t = data['arr']
                dep_t = current_t
                sojourn = dep_t - arr_t
                
                if current_t >= warmup_end:
                    departures_in_window += 1
                    sojourn_sum += sojourn

        if total_time_window > 0:
            L_est = area_n / total_time_window
            busy_frac_est = area_non_empty / total_time_window
            busy_util_est = (area_min_nc / total_time_window) / c
            
            if departures_in_window > 0:
                W_est = (sojourn_sum / departures_in_window) * 60.0
            else:
                W_est = 0.0
                
            total_accepted = arrivals_in_window
            total_attempts = arrivals_in_window + blocks_in_window
            p_loss_est = blocks_in_window / total_attempts if total_attempts > 0 else 0.0
            p_wait_est = waits_in_window / total_accepted if total_accepted > 0 else 0.0
            
            dep_rate_est = departures_in_window / total_time_window if total_time_window > 0 else 0.0
            lam_eff_est = arrivals_in_window / total_time_window if total_time_window > 0 else 0.0
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_loss.append(p_loss_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(arrivals_in_window)
            all_blk.append(blocks_in_window)
            all_dep.append(departures_in_window)
            all_busy_util.append(busy_util_est)
            all_lam_eff.append(lam_eff_est)
            all_dep_rate.append(dep_rate_est)
            seeds_used_list.append(s)

    seeds_used = len(seeds_used_list)
    
    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    
    output = {
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_busy_frac,
        "p_loss": avg_p_loss,
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": H - (H*0.25),
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": avg_busy_util,
        "dep": avg_dep,
        "dep_rate": avg_dep_rate,
        "lam_eff": avg_lam_eff,
        "p_wait": avg_p_wait,
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
