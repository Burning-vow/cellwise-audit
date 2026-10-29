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

    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 12.0  # 5 per hour
    c = 2

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu_base = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        c = 3
    else:
        lam = lam_base
    
    mu = mu_base

    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_wait = []
    results_arr = []
    results_dep = []
    results_blk = []
    results_busy_util = []
    results_p_loss = []
    
    total_time_units = H
    warmup_ratio = 0.25
    warmup_end = H * (1 - warmup_ratio)
    window_len = H - warmup_end

    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        service_times = {} # id -> finish time
        active_services = [] # list of finish times
        
        # Statistics accumulators (for the window [warmup_end, H])
        area_n = 0.0
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0
        count_waiting_on_arrival_window = 0
        sum_w_window = 0.0 # Sum of W for customers who arrived and departed within window? 
                           # Standard definition: Average time spent in system for those counted.
                           # Usually we track individual sojourn times.
        
        # To calculate L correctly as time-average, we integrate n(t).
        # To calculate W correctly, we need average sojourn time of completed services in window.
        # p_wait is probability that an arriving customer finds queue non-empty (n >= c).
        # busy_frac is E[min(n,c)]/c. We can compute this by integrating min(n,c)/c over time.
        
        last_event_time = 0.0
        current_min_n_c = 0
        
        # We need to handle events until H.
        # Events: Arrival, Departure.
        
        # Initialize first event
        events = []
        if next_arrival <= H:
            events.append((next_arrival, 'A'))
            
        # We need a way to manage departures. Since service times are exponential, 
        # we can just keep a heap or sorted list of departure times.
        import heapq
        dep_heap = []
        
        # Pre-generate arrival stream? No, dynamic.
        # But we must generate service time at arrival.
        
        # Reset state for this seed
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        dep_heap = []
        
        # Stats for integration
        area_n = 0.0
        area_min_nc = 0.0
        last_t = 0.0
        
        # Counters for window stats
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_count_win = 0
        sum_sojourn_win = 0.0
        
        # For p_wait: fraction of arrivals in window that had to wait.
        # Note: If blocked, do they count as waiting? Usually "waiting" means joining queue. 
        # Blocked means lost. So p_wait should be among those who entered? 
        # Or probability that an arrival FINDS queue full? 
        # Definition: "probability that an arriving customer has to wait". 
        # If blocked, they don't enter, so they don't wait in system. They are lost.
        # So p_wait = (Arrivals entering with n>=c) / (Total Arrivals)? 
        # Or (Arrivals entering with n>=c) / (Successful Entries)?
        # Standard M/M/c/K: P(wait) usually refers to conditional on entry or unconditional?
        # Let's assume unconditional probability that an arrival event results in waiting (queue length > 0 upon arrival).
        # If blocked, queue is full, so they didn't wait.
        # So numerator: arrivals where n < K (capacity infinite here? No, bank has queues? 
        # Problem says "bank branch", usually implies infinite queue unless specified. 
        # "Blocked/Lost" key exists in output requirements. This implies finite capacity?
        # Wait, standard M/M/c has no blocking. M/M/c/K has blocking.
        # The prompt asks for `blk` and `p_loss`. This strongly suggests a finite buffer or loss system.
        # However, it doesn't specify capacity K. 
        # Re-reading: "average waiting + processing time W". If blocked, W is undefined or 0?
        # Usually in these sims, if not specified, assume infinite queue (M/M/c). 
        # BUT `blk` and `p_loss` are required keys. 
        # If infinite queue, blk=0, p_loss=0.
        # Let's assume infinite queue capacity for now, so blk=0 always.
        # If the model was M/M/c/K, K would be given. It is not.
        # So I will implement M/M/c (infinite queue). blk will be 0.
        
        while True:
            # Determine next event time
            next_dep = dep_heap[0] if dep_heap else float('inf')
            next_arr = next_arrival
            
            if next_arr == float('inf') and next_dep == float('inf'):
                break
                
            t_next = min(next_arr, next_dep)
            
            if t_next > H:
                # Integrate up to H
                dt = H - last_t
                area_n += n_in_system * dt
                area_min_nc += min(n_in_system, c) * dt
                break
            
            # Integrate from last_t to t_next
            dt = t_next - last_t
            area_n += n_in_system * dt
            area_min_nc += min(n_in_system, c) * dt
            last_t = t_next
            
            if t_next == next_arr:
                # Arrival
                # Check if waiting needed BEFORE adding to system?
                # "Arriving customer needs to wait" means queue length > 0.
                # Queue length = max(0, n_in_system - c).
                # If n_in_system >= c, they wait.
                
                if t_next >= warmup_end:
                    arr_count_win += 1
                    if n_in_system >= c:
                        wait_count_win += 1
                
                # Generate service time NOW
                svc_time = rng.expovariate(mu)
                dep_time = t_next + svc_time
                heapq.heappush(dep_heap, dep_time)
                n_in_system += 1
                
                # Schedule next arrival
                next_arrival = t_next + rng.expovariate(lam)
                
            elif t_next == next_dep:
                # Departure
                heapq.heappop(dep_heap)
                n_in_system -= 1
                
                if t_next >= warmup_end:
                    dep_count_win += 1
                    # Calculate sojourn time? 
                    # We need to know when this specific customer arrived.
                    # With simple heap, we lose arrival time.
                    # Need to store (dep_time, arr_time) in heap.
                    
                # Fix: Store tuple in heap
                pass
        
        # Restart loop with correct heap structure
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        dep_heap = [] # stores (finish_time, start_time)
        last_t = 0.0
        area_n = 0.0
        area_min_nc = 0.0
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        wait_count_win = 0
        sum_sojourn_win = 0.0
        
        while True:
            next_dep = dep_heap[0][0] if dep_heap else float('inf')
            next_arr = next_arrival
            
            if next_arr == float('inf') and next_dep == float('inf'):
                break
            
            t_next = min(next_arr, next_dep)
            
            if t_next > H:
                dt = H - last_t
                area_n += n_in_system * dt
                area_min_nc += min(n_in_system, c) * dt
                break
            
            dt = t_next - last_t
            area_n += n_in_system * dt
            area_min_nc += min(n_in_system, c) * dt
            last_t = t_next
            
            if t_next == next_arr:
                if t_next >= warmup_end:
                    arr_count_win += 1
                    if n_in_system >= c:
                        wait_count_win += 1
                
                svc_time = rng.expovariate(mu)
                finish_time = t_next + svc_time
                heapq.heappush(dep_heap, (finish_time, t_next))
                n_in_system += 1
                next_arrival = t_next + rng.expovariate(lam)
                
            elif t_next == next_dep:
                finish_time, start_time = heapq.heappop(dep_heap)
                n_in_system -= 1
                
                if t_next >= warmup_end:
                    dep_count_win += 1
                    sojourn = finish_time - start_time
                    sum_sojourn_win += sojourn

        # Compute metrics for this seed
        # L = Time-average number in system
        L_seed = area_n / H if H > 0 else 0
        
        # Busy Fraction = E[min(N,c)]/c
        busy_frac_seed = (area_min_nc / H) / c if H > 0 else 0
        
        # W = Average sojourn time of customers who DEPARTED in the window
        # Note: Customers arriving before window but departing inside are included?
        # Standard regenerative simulation often uses Little's Law consistency.
        # Here, we calculated sum_sojourn for departures in window.
        if dep_count_win > 0:
            W_seed = sum_sojourn_win / dep_count_win
        else:
            W_seed = 0.0
            
        # p_wait = Probability an ARRIVAL in window had to wait
        if arr_count_win > 0:
            p_wait_seed = wait_count_win / arr_count_win
        else:
            p_wait_seed = 0.0
            
        # p_loss = blk / arr. Since infinite queue, blk=0.
        p_loss_seed = 0.0
        
        # busy_util is same as busy_frac definition provided? 
        # Prompt: "busy_frac ... = E[min(N,c)]/c". "busy_util=E[min(N,c)]/c".
        # So busy_util_seed = busy_frac_seed.
        busy_util_seed = busy_frac_seed
        
        # Accumulate for global averages
        results_L.append(L_seed)
        results_W.append(W_seed)
        results_busy_frac.append(busy_frac_seed)
        results_p_wait.append(p_wait_seed)
        results_arr.append(arr_count_win)
        results_dep.append(dep_count_win)
        results_blk.append(blk_count_win)
        results_busy_util.append(busy_util_seed)
        results_p_loss.append(p_loss_seed)

    # Global Averages
    avg_L = sum(results_L) / len(results_L)
    avg_W = sum(results_W) / len(results_W)
    avg_busy_frac = sum(results_busy_frac) / len(results_busy_frac)
    avg_p_wait = sum(results_p_wait) / len(results_p_wait)
    avg_arr = sum(results_arr) / len(results_arr)
    avg_dep = sum(results_dep) / len(results_dep)
    avg_blk = sum(results_blk) / len(results_blk)
    avg_busy_util = sum(results_busy_util) / len(results_busy_util)
    avg_p_loss = sum(results_p_loss) / len(results_p_loss)
    
    # Dep rate per hour
    # Total departures in window across all seeds / Total window time across all seeds
    # Window time per seed = window_len
    total_window_time = N_seeds * window_len
    if total_window_time > 0:
        dep_rate = (sum(results_dep) / total_window_time) * 60.0 # Convert to per hour? 
        # Wait, time_unit is hour. So dep_rate is "count per hour".
        # sum(results_dep) is total counts.
        # Rate = Total Counts / Total Hours.
        dep_rate_val = sum(results_dep) / total_window_time
    else:
        dep_rate_val = 0.0
        
    # Lam eff
    if total_window_time > 0:
        lam_eff_val = sum(results_arr) / total_window_time
    else:
        lam_eff_val = 0.0

    output = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "hour",
        "seed_list": [seed_start + i for i in range(N_seeds)],
        "seeds_used": N_seeds,
        "time_unit": "hour",
        "win": round(window_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff_val, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in results_L],
        "per_seed_W": [round(x, 4) for x in results_W],
        "per_seed_busy_frac": [round(x, 4) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in results_p_wait]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
