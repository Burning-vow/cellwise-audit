import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in hours
    lam_base = 9.0
    mu_base = 60.0 / 6.0  # 10 per hour
    c = 4  # capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 5
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_p_wait = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        # Service times are drawn at arrival and stored in a queue/list of remaining times? 
        # Discrete event simulation usually uses an event list.
        # Events: (time, type, data). Type: 'A' (arrival), 'D' (departure)
        events = []
        
        # Statistics accumulators (for the window after warmup)
        warmup_time = 0.25 * H
        stat_start_time = warmup_time
        
        # Area integrals for L and busy fraction
        area_L = 0.0
        area_busy = 0.0
        last_stat_time = stat_start_time
        
        # Counters within window
        count_arr = 0
        count_dep = 0
        count_blk = 0
        count_wait = 0 # Number of customers who waited (n>1 upon arrival or started service later than arrival?)
                       # p_wait usually means probability that an arriving customer has to wait.
                       # In M/M/1/K, if system is not empty, they wait. If empty, no wait.
                       # But here we track individual customers.
        
        # We need to track individual customers to compute W accurately.
        # Customer object: (arrival_time, service_duration, start_service_time)
        # Since it's FIFO, we can maintain a queue of customers waiting for service.
        # The doctor serves one at a time.
        
        # Let's use a priority queue for events.
        import heapq
        heapq.heappush(events, (next_arrival, 'A', None))
        
        # Queue of customers waiting for service (FIFO)
        # Each element: (arrival_time, service_duration)
        waiting_queue = []
        
        # Current service info
        current_service_end_time = float('inf')
        current_customer_arrival_time = None
        
        # To calculate W, we sum up (departure_time - arrival_time) for completed services in window.
        total_W_sum = 0.0
        num_completed_in_window = 0
        
        # For p_wait: proportion of arrivals in window that had to wait.
        # An arrival waits if there is someone already being served OR someone in the queue.
        # i.e., if n_in_system > 0 at arrival instant (before adding this new one)?
        # Standard definition: P(wait) = P(system non-empty upon arrival).
        # Or specifically for those admitted.
        
        while events:
            t_curr, ev_type, _ = heapq.heappop(events)
            
            if t_curr > H:
                break
                
            # Update areas before processing event if we are past stat_start_time
            if t_curr > stat_start_time:
                dt = t_curr - last_stat_time
                if dt > 0:
                    area_L += n_in_system * dt
                    if n_in_system > 0:
                        area_busy += dt
                    last_stat_time = t_curr
            
            if ev_type == 'A':
                # Arrival
                if t_curr >= stat_start_time:
                    count_arr += 1
                
                if n_in_system < c:
                    # Admitted
                    n_in_system += 1
                    
                    # Draw service duration now
                    svc_dur = rng.expovariate(mu)
                    
                    # Check if needs to wait
                    # If server is busy (current_service_end_time > t_curr) or queue is not empty
                    # Actually, if n_in_system was > 0 before increment, then someone is being served or waiting.
                    # Wait condition: Is the doctor free?
                    # Doctor is free if current_service_end_time <= t_curr AND waiting_queue is empty?
                    # Simpler: If n_in_system (after increment) == 1, then no wait. Else wait.
                    # But careful: if previous customer just left at same time?
                    # In DES, departures happen at specific times. Arrivals at specific times.
                    # If an arrival happens when system is empty, n becomes 1, starts service immediately.
                    # If arrival happens when system has people, n increases, joins queue.
                    
                    if n_in_system == 1:
                        # Start service immediately
                        current_service_end_time = t_curr + svc_dur
                        current_customer_arrival_time = t_curr
                        heapq.heappush(events, (current_service_end_time, 'D', None))
                    else:
                        # Join queue
                        waiting_queue.append((t_curr, svc_dur))
                        
                        if t_curr >= stat_start_time:
                            count_wait += 1
                else:
                    # Blocked
                    if t_curr >= stat_start_time:
                        count_blk += 1
                
                # Schedule next arrival
                next_arrival = t_curr + rng.expovariate(lam)
                if next_arrival <= H:
                    heapq.heappush(events, (next_arrival, 'A', None))
                    
            elif ev_type == 'D':
                # Departure
                # Only process if this departure corresponds to the current active service
                # And ensure we don't process stale events (though with single server and proper scheduling, should be fine)
                
                # Verify this is the correct departure
                if abs(t_curr - current_service_end_time) > 1e-9:
                    continue
                
                # Complete service
                n_in_system -= 1
                count_dep += 1 if t_curr >= stat_start_time else 0
                
                # Calculate W for this customer
                w_val = t_curr - current_customer_arrival_time
                if t_curr >= stat_start_time:
                    total_W_sum += w_val
                    num_completed_in_window += 1
                
                # Start next service if any
                if waiting_queue:
                    arr_t, svc_d = waiting_queue.pop(0)
                    current_service_end_time = t_curr + svc_d
                    current_customer_arrival_time = arr_t
                    heapq.heappush(events, (current_service_end_time, 'D', None))
                else:
                    current_service_end_time = float('inf')
                    current_customer_arrival_time = None

        # Final update for area if loop ended exactly at H or beyond
        if H > last_stat_time:
            dt = H - last_stat_time
            area_L += n_in_system * dt
            if n_in_system > 0:
                area_busy += dt

        win_len = H - stat_start_time
        
        if win_len > 0:
            L_est = area_L / win_len
            busy_frac_est = area_busy / win_len
            W_est = total_W_sum / num_completed_in_window if num_completed_in_window > 0 else 0.0
            p_loss_est = count_blk / count_arr if count_arr > 0 else 0.0
            p_wait_est = count_wait / count_arr if count_arr > 0 else 0.0
            dep_rate_est = count_dep / win_len * 60.0 # per hour? No, time_unit is hour. So dep/hour.
            # dep_rate is "个/每小时". Since time_unit is hour, rate is count / hours.
            dep_rate_est = count_dep / win_len
            
            # busy_util = E[min(N,c)]/c. Here c=4 (or 5). N is number in system.
            # min(N,c) is effectively N since N<=c.
            # So busy_util = L_est / c
            busy_util_est = L_est / c
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_loss.append(p_loss_est)
            all_arr.append(count_arr)
            all_blk.append(count_blk)
            all_dep.append(count_dep)
            all_busy_util.append(busy_util_est)
            all_p_wait.append(p_wait_est)
        else:
            all_L.append(0.0)
            all_W.append(0.0)
            all_busy_frac.append(0.0)
            all_p_loss.append(0.0)
            all_arr.append(0)
            all_blk.append(0)
            all_dep.append(0)
            all_busy_util.append(0.0)
            all_p_wait.append(0.0)

    seeds_used = len(all_L)
    
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0
        
    res = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_loss": avg(all_p_loss),
        "runtime_units": "seconds", # Placeholder, actual runtime not measured precisely but required key
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": H - 0.25*H,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg([d/(H-0.25*H) for d in all_dep]) if seeds_used>0 else 0.0,
        "lam_eff": avg([a/(H-0.25*H) for a in all_arr]) if seeds_used>0 else 0.0,
        "p_wait": avg(all_p_wait),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait,
        "busy_occupied": avg(all_busy_frac)
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
