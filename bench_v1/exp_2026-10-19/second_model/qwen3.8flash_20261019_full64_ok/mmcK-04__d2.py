import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr = 10/hr
    c = 2
    K = 4
    
    if pert == 'lam_up': lam = lam_base * 1.1; mu = mu_base
    elif pert == 'mu_up': lam = lam_base; mu = mu_base * 1.1
    elif pert == 'c_up': lam = lam_base; mu = mu_base; c = 3; K = 5
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    win = H * 0.75 # Remove first 25% warmup
    
    all_L = []
    all_W_sum = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_sys = 0
        next_arr_t = rng.expovariate(lam)
        # Service times are drawn upon arrival and stored
        service_times = [] 
        # We need to track when each car finishes. 
        # Since it's a queue with FCFS, we can just track the completion time of the last car in service?
        # No, multiple servers. We need a list of finish times for cars currently in service.
        # But simpler: maintain a priority queue or sorted list of departure events?
        # Discrete Event Simulation approach:
        # Events: Arrival, Departure.
        # We need to know which car departs.
        # Let's keep a list of (arrival_time, service_duration, start_service_time_if_started).
        # Actually, standard M/M/c/K simulation:
        # Maintain count n.
        # If n < c, service starts immediately. Finish time = t + exp(mu).
        # If n >= c, wait. When a server becomes free, the head of line starts.
        # To handle this efficiently without complex data structures for small K:
        # Keep a list of `finish_times` for cars currently in service.
        # Keep a queue of `waiting_cars` (just their arrival times or IDs, but we need W).
        # Better: Store objects/dicts for cars in system.
        
        cars = [] # List of dicts: {'arr_t': float, 'svc_dur': float, 'start_svc_t': float or None, 'dep_t': float or None}
        
        # Statistics accumulators for this seed (post-warmup)
        area_L = 0.0
        area_busy = 0.0 # Time where n > 0
        area_util = 0.0 # Integral of min(n, c) / c ? No, busy_util is E[min(N,c)]/c. So integral of min(n,c) dt / (win * c)
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0
        count_waited = 0 # Cars that had to wait (start_svc_t > arr_t)
        
        prev_t = 0.0
        
        while t < H:
            # Determine next event time
            # Next arrival
            na = next_arr_t
            
            # Next departure: find min dep_t among cars that have started service and not yet departed
            # Cars in service have start_svc_t != None and dep_t == None
            # Wait, if we set dep_t at start, we can just look at active services.
            
            nd = float('inf')
            for car in cars:
                if car['start_svc_t'] is not None and car['dep_t'] is None:
                    # It has started, so it will depart at start + dur
                    # But we haven't calculated dep_t yet? 
                    # Strategy: Calculate dep_t when service starts.
                    pass
            
            # Refactor state representation:
            # cars: list of {arr_t, svc_dur, status: 'wait'/'serv'/'done', start_t, end_t}
            # Simpler: 
            # n_serv = number of cars currently being served.
            # serv_end_times = list of end times for current servers.
            # wait_queue = list of arrival times of waiting cars.
            
            # Let's restart logic with clearer state:
            # n_total = len(serv_end_times) + len(wait_queue)
            # serv_end_times: sorted list of times when current services finish.
            # wait_queue: FIFO list of arrival times.
            
            # Reset for clarity
            serv_end_times = []
            wait_queue = []
            
            # Re-run loop with this structure
            t = 0.0
            next_arr_t = rng.expovariate(lam)
            
            # Stats init
            area_L = 0.0
            area_busy = 0.0
            area_min_nc = 0.0
            count_arr = 0
            count_blk = 0
            count_dep = 0
            sum_W = 0.0
            count_waited = 0
            
            prev_t = 0.0
            
            while t < H:
                # Current state before event
                n_curr = len(serv_end_times) + len(wait_queue)
                
                # Find next event
                t_arr = next_arr_t
                t_dep = min(serv_end_times) if serv_end_times else float('inf')
                
                t_next = min(t_arr, t_dep)
                
                if t_next > H:
                    break
                
                # Integrate stats from prev_t to t_next
                dt = t_next - prev_t
                if prev_t >= H * 0.25: # Only accumulate after warmup
                    area_L += n_curr * dt
                    if n_curr > 0:
                        area_busy += dt
                    area_min_nc += min(n_curr, c) * dt
                
                # Process event
                if t_arr <= t_dep:
                    # Arrival
                    t = t_arr
                    if n_curr < K:
                        # Accept
                        count_arr += 1
                        svc_dur = rng.expovariate(mu)
                        if len(serv_end_times) < c:
                            # Start service immediately
                            end_t = t + svc_dur
                            serv_end_times.append(end_t)
                            serv_end_times.sort()
                            # W = svc_dur (no wait)
                            sum_W += svc_dur
                        else:
                            # Join queue
                            wait_queue.append((t, svc_dur))
                            # W will be calculated later
                    else:
                        # Block
                        count_blk += 1
                    
                    # Schedule next arrival
                    next_arr_t = t + rng.expovariate(lam)
                    
                else:
                    # Departure
                    t = t_dep
                    # Remove one from service
                    serv_end_times.pop(0) # Sorted, so first is earliest
                    count_dep += 1
                    
                    # Check if someone waits
                    if wait_queue:
                        arr_t, svc_dur = wait_queue.pop(0)
                        w = t - arr_t
                        sum_W += w
                        if w > 1e-9:
                            count_waited += 1
                        end_t = t + svc_dur
                        serv_end_times.append(end_t)
                        serv_end_times.sort()
                    # Else, just one less in service
                
                prev_t = t
            
            # Final integration up to H if needed? Loop breaks when t_next > H.
            # The last segment from prev_t to H was not integrated because no event occurred there.
            dt_final = H - prev_t
            if prev_t >= H * 0.25:
                 n_curr = len(serv_end_times) + len(wait_queue)
                 area_L += n_curr * dt_final
                 if n_curr > 0:
                     area_busy += dt_final
                 area_min_nc += min(n_curr, c) * dt_final
            
            # Calculate per-seed metrics
            L_est = area_L / win
            W_est = sum_W / count_dep if count_dep > 0 else 0.0
            busy_frac_est = area_busy / win
            p_loss_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0.0
            p_wait_est = count_waited / count_dep if count_dep > 0 else 0.0
            busy_util_est = area_min_nc / (win * c)
            busy_occ_est = busy_frac_est # Same as 1-pi0 definition given
            
            all_L.append(L_est)
            all_W_sum.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_loss.append(p_loss_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(count_arr)
            all_blk.append(count_blk)
            all_dep.append(count_dep)
            all_busy_util.append(busy_util_est)
            all_busy_occupied.append(busy_occ_est)
            
    seeds_used = N_seeds
    seed_list = [S_start + i for i in range(seeds_used)]
    
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W_sum) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_busy_occ = sum(all_busy_occupied) / seeds_used
    
    dep_rate = avg_dep / win # per hour
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W * 60, 6), # Convert hours to minutes
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(avg_dep / win, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x * 60, 6) for x in all_W_sum],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
