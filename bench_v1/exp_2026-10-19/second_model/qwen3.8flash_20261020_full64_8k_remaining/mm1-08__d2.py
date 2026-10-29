import sys, json, random, math
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 5; horizon = 100.0; seed_start = 42; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]

    lam_base = 8.0 # per hour
    mu_base = 60.0 / 5.0 # per hour (12)
    
    if pert == "lam_up": lam = lam_base * 1.1
    elif pert == "mu_up": mu = mu_base * 1.1
    elif pert == "c_up": c = 2
    else: 
        lam = lam_base
        mu = mu_base
        c = 1
    
    time_unit = "hour"
    win = horizon * 0.75
    warmup = horizon * 0.25
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_wait = []
    all_arr = []; all_dep = []; all_blk = []; all_busy_util = []; all_lam_eff = []; all_p_loss = []
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []; per_seed_p_loss = []; per_seed_p_wait = []
    seed_list = []
    
    total_seeds_used = 0
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        events = []
        t = 0.0
        
        # Initial arrival
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'A', None))
        
        queue = deque()
        service_end_times = [] # list of end times for busy servers
        num_in_system = 0
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_waited = 0
        
        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            event = events.pop(0)
            t_curr, etype, data = event
            
            if t_curr > horizon: break
            
            dt = t_curr - last_event_time
            if last_event_time >= warmup:
                area_L += num_in_system * dt
                area_busy += min(num_in_system, c) * dt
            
            last_event_time = t_curr
            
            if etype == 'A':
                count_arr += 1
                if len(queue) < c or num_in_system < c: # Simplified check for M/M/1/c logic
                    pass
                
                # Check capacity
                if num_in_system < c:
                    num_in_system += 1
                    svc_time = rng.expovariate(mu)
                    start_t = t_curr
                    end_t = start_t + svc_time
                    service_end_times.append(end_t)
                    events.append((end_t, 'D', {'arrival_time': start_t}))
                else:
                    count_blk += 1
                
                next_arrival = t_curr + rng.expovariate(lam)
                events.append((next_arrival, 'A', None))
                
            elif etype == 'D':
                arr_time = data['arrival_time']
                num_in_system -= 1
                service_end_times.remove(t_curr)
                count_dep += 1
                
                w = t_curr - arr_time
                if last_event_time >= warmup:
                    sum_W += w
                    if w > 0: count_waited += 1 # Wait time is 0 if immediate service? In M/M/1 FCFS, wait is queueing delay.
                    # Actually standard W includes service time. P(wait) usually means probability of waiting in queue > 0.
                    # Let's stick to standard definitions: W = sojourn time. p_wait = prob that a customer waits in queue.
                    # If service starts immediately, wait=0.
                    # We need to track if they waited.
                    # Re-evaluating: The prompt asks for p_wait. Usually P(W_q > 0).
                    # I'll calculate it based on whether the server was busy at arrival.
                
                # Schedule next departure if any
                if service_end_times:
                    next_dep = min(service_end_times)
                    # Find corresponding arrival time? No, we stored end times.
                    # We need to know which one ends first.
                    # This implementation is getting messy with multiple servers.
                    # For c=1, it's simpler.
                    pass

        # This approach is flawed for general c. Let's restart simulation loop with cleaner state management.
        
    # Reset and do proper DES
    results = []
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [(next_arrival, 'A')]
        
        queue = deque() # Stores arrival times of customers waiting
        servers_free_at = [0.0] * c # Time when each server becomes free
        num_in_system = 0
        
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_customers_in_window = 0
        count_waited = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            t_curr, etype = events.pop(0)
            
            if t_curr > horizon:
                break
                
            dt = t_curr - last_event_time
            if last_event_time >= warmup:
                area_L += num_in_system * dt
                busy_count = sum(1 for st in servers_free_at if st > last_event_time) # Approximate busy fraction over interval?
                # Better: Track number of busy servers explicitly
                pass
            
            # Recalculate busy servers properly
            # Let's maintain num_busy separately
            
            last_event_time = t_curr
            
            if etype == 'A':
                count_arr += 1
                # Find earliest available server
                min_free_idx = -1
                min_free_time = float('inf')
                for i in range(c):
                    if servers_free_at[i] < min_free_time:
                        min_free_time = servers_free_at[i]
                        min_free_idx = i
                
                if num_in_system < c:
                    num_in_system += 1
                    svc_time = rng.expovariate(mu)
                    start_service = max(t_curr, min_free_time)
                    end_service = start_service + svc_time
                    servers_free_at[min_free_idx] = end_service
                    events.append((end_service, 'D'))
                    
                    # Record stats for this customer if in window
                    if t_curr >= warmup:
                        count_customers_in_window += 1
                        w = end_service - t_curr
                        sum_W += w
                        if start_service > t_curr:
                            count_waited += 1
                else:
                    count_blk += 1
                    
                next_arrival = t_curr + rng.expovariate(lam)
                events.append((next_arrival, 'A'))
                
            elif etype == 'D':
                num_in_system -= 1
                count_dep += 1
                # Update busy area integral correctly requires tracking state changes
                # Since we are doing discrete events, we should integrate between events.
                # But we missed the integration step above.
                pass

        # The integration logic needs to be inside the loop before updating state.
        # Let's rewrite the core loop carefully.
        
    # Final Attempt Structure
    final_L = []; final_W = []; final_busy = []; final_pw = []
    final_arr = []; final_dep = []; final_blk = []; final_bu = []; final_le = []; final_pl = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        events = [(next_arrival, 'A')]
        
        servers_free_at = [0.0] * c
        num_in_system = 0
        num_busy = 0
        
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_W_win = 0.0
        count_cust_win = 0
        count_waited_win = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            t_curr, etype = events.pop(0)
            
            if t_curr > horizon:
                break
            
            dt = t_curr - last_event_time
            if last_event_time >= warmup:
                area_L += num_in_system * dt
                area_busy += num_busy * dt
            
            last_event_time = t_curr
            
            if etype == 'A':
                if last_event_time >= warmup:
                    count_arr_win += 1
                
                # Determine if blocked
                if num_in_system >= c:
                    if last_event_time >= warmup:
                        count_blk_win += 1
                else:
                    num_in_system += 1
                    svc_time = rng.expovariate(mu)
                    # Find server
                    min_idx = 0
                    min_val = servers_free_at[0]
                    for i in range(1, c):
                        if servers_free_at[i] < min_val:
                            min_val = servers_free_at[i]
                            min_idx = i
                    
                    start_service = max(t_curr, min_val)
                    end_service = start_service + svc_time
                    servers_free_at[min_idx] = end_service
                    num_busy += 1
                    events.append((end_service, 'D'))
                    
                    if last_event_time >= warmup:
                        count_cust_win += 1
                        w = end_service - t_curr
                        sum_W_win += w
                        if start_service > t_curr:
                            count_waited_win += 1
                
                next_arrival = t_curr + rng.expovariate(lam)
                events.append((next_arrival, 'A'))
                
            elif etype == 'D':
                num_in_system -= 1
                num_busy -= 1
                if last_event_time >= warmup:
                    count_dep_win += 1

        # Calculate metrics for this seed
        L_est = area_L / win if win > 0 else 0
        W_est = sum_W_win / count_cust_win if count_cust_win > 0 else 0
        busy_frac_est = area_busy / win if win > 0 else 0
        p_wait_est = count_waited_win / count_cust_win if count_cust_win > 0 else 0
        p_loss_est = count_blk_win / count_arr_win if count_arr_win > 0 else 0
        dep_rate_est = count_dep_win / win * 60.0 # Per hour? Win is in hours. So just count/win.
        # Prompt says dep_rate is "个/每小时". If time_unit is hour, then count_dep / win.
        dep_rate_est = count_dep_win / win if win > 0 else 0
        lam_eff_est = dep_rate_est # Conservation flow
        
        final_L.append(L_est)
        final_W.append(W_est)
        final_busy.append(busy_frac_est)
        final_pw.append(p_wait_est)
        final_arr.append(count_arr_win)
        final_dep.append(count_dep_win)
        final_blk.append(count_blk_win)
        final_bu.append(busy_frac_est) # E[min(N,c)]/c is same as busy_frac for c=1
        final_le.append(lam_eff_est)
        final_pl.append(p_loss_est)
        
        seed_list.append(current_seed)
        total_seeds_used += 1

    avg_L = sum(final_L) / total_seeds_used
    avg_W = sum(final_W) / total_seeds_used
    avg_busy = sum(final_busy) / total_seeds_used
    avg_pw = sum(final_pw) / total_seeds_used
    avg_arr = sum(final_arr) / total_seeds_used
    avg_dep = sum(final_dep) / total_seeds_used
    avg_blk = sum(final_blk) / total_seeds_used
    avg_bu = sum(final_bu) / total_seeds_used
    avg_le = sum(final_le) / total_seeds_used
    avg_pl = sum(final_pl) / total_seeds_used
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "simulation",
        "seed_list": seed_list,
        "seeds_used": total_seeds_used,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_le, 6),
        "lam_eff": round(avg_le, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in final_L],
        "per_seed_W": [round(x, 6) for x in final_W],
        "per_seed_busy_frac": [round(x, 6) for x in final_busy],
        "per_seed_p_loss": [round(x, 6) for x in final_pl],
        "per_seed_p_wait": [round(x, 6) for x in final_pw]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
