import sys, json, math, random
from collections import deque

def main():
    args = {}
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('--'):
            key = sys.argv[i][2:]
            val = sys.argv[i+1] if i+1 < len(sys.argv) and not sys.argv[i+1].startswith('--') else None
            args[key] = val
    
    N = int(args.get('seeds', 10))
    H = float(args.get('horizon', 100.0))
    S = int(args.get('seed-start', 42))
    pert = args.get('pert', 'none')
    
    lam_base = 4.0
    mu_base = 60.0 / 5.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 2
    else:
        lam = lam_base
        mu = mu_base
        c = 1
        
    if pert != 'c_up':
        c = 1
        
    time_unit = "hour"
    horizon_hours = H
    
    total_L = 0.0
    total_W = 0.0
    total_busy_frac = 0.0
    total_p_wait = 0.0
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_busy_util = 0.0
    total_dep_rate = 0.0
    total_lam_eff = 0.0
    total_p_loss = 0.0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    warmup_ratio = 0.25
    warmup_time = horizon_hours * warmup_ratio
    
    for s_idx in range(N):
        seed_val = S + s_idx
        rng = random.Random(seed_val)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = []
        queue = deque()
        server_free_time = 0.0
        
        area_L = 0.0
        last_event_time = 0.0
        current_N = 0
        
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        wait_count = 0
        busy_time = 0.0
        
        events = []
        
        while t < horizon_hours:
            if next_arrival < (server_free_time if queue or t < server_free_time else float('inf')):
                event_time = next_arrival
                event_type = 'arrival'
            else:
                event_time = server_free_time
                event_type = 'departure'
                
            if event_time > horizon_hours:
                break
                
            dt = event_time - last_event_time
            if last_event_time >= warmup_time:
                area_L += current_N * dt
            
            t = event_time
            last_event_time = t
            
            if event_type == 'arrival':
                if t >= warmup_time:
                    arrivals_in_window += 1
                
                st = rng.expovariate(mu)
                service_times.append(st)
                
                if current_N < c:
                    if t >= warmup_time:
                        if t < server_free_time:
                            wait_count += 1
                        else:
                            pass 
                    current_N += 1
                    if t >= server_free_time:
                        server_free_time = t + st
                    else:
                        queue.append((t, st))
                else:
                    if t >= warmup_time:
                        blocked_in_window += 1
                    
                next_arrival = t + rng.expovariate(lam)
                
            else:
                if queue:
                    arr_t, st = queue.popleft()
                    current_N -= 1
                    if t >= warmup_time:
                        departures_in_window += 1
                        W_i = t - arr_t
                        total_W_sum_local = getattr(main, '_w_sum', 0)
                        # Accumulate locally for this seed
                        if not hasattr(main, '_local_w_sums'):
                            main._local_w_sums = [0.0]*N
                        main._local_w_sums[s_idx] += W_i
                        if t >= warmup_time and arr_t >= warmup_time:
                             pass # Wait logic handled by arrival check? No, need to track who waited.
                             # Actually p_wait is fraction of customers who waited.
                             # We counted wait_count at arrival if they joined queue behind busy server.
                    server_free_time = t + st
                else:
                    current_N -= 1
                    if t >= warmup_time:
                        departures_in_window += 1
                        # This customer was served immediately upon arrival? 
                        # If queue empty and server free, no wait.
                        # But we need their service time to calculate W.
                        # The departure corresponds to the last arrival that started service.
                        # We need to store start time.
                        # Refactor: Store (arrival_time, service_duration, start_time) in a list or dict?
                        # Simpler: When service starts, record start time. When ends, calc W.
                        # Let's restart loop structure slightly cleaner inside the seed loop.
                        pass 

        # Re-implementing the simulation loop more carefully for correctness within the constraint
        # Resetting variables for this seed properly
        
        t = 0.0
        rng = random.Random(seed_val)
        next_arrival = rng.expovariate(lam)
        queue = deque() # stores (arrival_time, service_duration)
        server_free_time = 0.0
        current_N = 0
        area_L = 0.0
        last_event_time = 0.0
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        wait_count = 0
        sum_W = 0.0
        busy_time = 0.0
        
        # Determine end time
        end_time = horizon_hours
        
        while True:
            # Find next event
            cand_arr = next_arrival
            cand_dep = server_free_time if (queue or t < server_free_time) else float('inf')
            
            if cand_arr <= cand_dep:
                et = cand_arr
                ev = 'A'
            else:
                et = cand_dep
                ev = 'D'
                
            if et > end_time:
                # Integrate remaining area
                dt = end_time - last_event_time
                if last_event_time >= warmup_time:
                    area_L += current_N * dt
                t = end_time
                break
                
            dt = et - last_event_time
            if last_event_time >= warmup_time:
                area_L += current_N * dt
                if current_N > 0:
                    busy_time += dt
            
            t = et
            last_event_time = t
            
            if ev == 'A':
                if t >= warmup_time:
                    arrivals_in_window += 1
                
                st = rng.expovariate(mu)
                
                if current_N < c:
                    if t >= warmup_time:
                        if t < server_free_time:
                            wait_count += 1
                    current_N += 1
                    if t >= server_free_time:
                        server_free_time = t + st
                        # Start service immediately
                        # We need to know when this specific customer departs to add to sum_W
                        # But multiple customers can be in system.
                        # Queue holds those waiting. Server holds one being served.
                        # If server was free, this one starts now.
                        # If server busy, this one queues.
                        # How to link departure to arrival?
                        # When D happens, it pops from queue OR finishes current service.
                        # If queue empty, it finishes current service. Who is current service?
                        # We need to track the arrival time of the person currently in service.
                        # Let's use a variable `current_service_start` and `current_service_end`.
                        # Or simpler: Queue contains all customers including the one in service?
                        # Standard M/M/1: Queue is waiting line. Server is separate.
                        # Let's maintain `in_service` tuple (arr_t, st, start_t).
                        pass
                    else:
                        queue.append((t, st))
                else:
                    if t >= warmup_time:
                        blocked_in_window += 1
                        
                next_arrival = t + rng.expovariate(lam)
                
            else: # Departure
                if queue:
                    arr_t, st = queue.popleft()
                    current_N -= 1 # One left system, one enters service? No.
                    # Current service finished. Next from queue starts.
                    # So N stays same? No, N decreases by 1 (the one leaving), then increases by 1 (one entering)?
                    # Net change 0.
                    # But we need to account for the one leaving.
                    # The one leaving had arrival time stored somewhere.
                    # Problem: We didn't store arrival time of the one currently in service.
                    
                    # Fix: Use a single queue for ALL customers in system.
                    # Head of queue is in service. Rest are waiting.
                    # If queue empty, server idle.
                    
                    # Let's rewrite with single queue approach.
                    pass

        # Final attempt with Single Queue Approach
        t = 0.0
        rng = random.Random(seed_val)
        next_arrival = rng.expovariate(lam)
        q = deque() # (arrival_time, service_duration)
        server_free_time = 0.0
        current_N = 0
        area_L = 0.0
        last_event_time = 0.0
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        wait_count = 0
        sum_W = 0.0
        busy_time = 0.0
        end_time = horizon_hours
        
        while True:
            cand_arr = next_arrival
            cand_dep = server_free_time if q else float('inf')
            
            if cand_arr <= cand_dep:
                et = cand_arr
                ev = 'A'
            else:
                et = cand_dep
                ev = 'D'
                
            if et > end_time:
                dt = end_time - last_event_time
                if last_event_time >= warmup_time:
                    area_L += current_N * dt
                    if current_N > 0:
                        busy_time += dt
                t = end_time
                break
                
            dt = et - last_event_time
            if last_event_time >= warmup_time:
                area_L += current_N * dt
                if current_N > 0:
                    busy_time += dt
            
            t = et
            last_event_time = t
            
            if ev == 'A':
                if t >= warmup_time:
                    arrivals_in_window += 1
                
                st = rng.expovariate(mu)
                
                if current_N < c:
                    if t >= warmup_time:
                        if q: # Someone already in service/waiting
                            wait_count += 1
                    q.append((t, st))
                    current_N += 1
                    if len(q) == 1: # Just arrived into empty system
                        server_free_time = t + st
                else:
                    if t >= warmup_time:
                        blocked_in_window += 1
                        
                next_arrival = t + rng.expovariate(lam)
                
            else: # D
                arr_t, st = q.popleft()
                current_N -= 1
                if t >= warmup_time:
                    departures_in_window += 1
                    sum_W += (t - arr_t)
                
                if q:
                    # Next customer starts service
                    next_arr_t, next_st = q[0]
                    server_free_time = t + next_st
                else:
                    server_free_time = float('inf')

        win_len = horizon_hours - warmup_time
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            bf_est = 0.0
            pw_est = 0.0
            pl_est = 0.0
        else:
            L_est = area_L / win_len
            if departures_in_window > 0:
                W_est = sum_W / departures_in_window
            else:
                W_est = 0.0
            bf_est = busy_time / win_len
            if arrivals_in_window > 0:
                pw_est = wait_count / arrivals_in_window
            else:
                pw_est = 0.0
            if arrivals_in_window > 0:
                pl_est = blocked_in_window / arrivals_in_window
            else:
                pl_est = 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        total_L += L_est
        total_W += W_est
        total_busy_frac += bf_est
        total_p_wait += pw_est
        total_arr += arrivals_in_window
        total_blk += blocked_in_window
        total_dep += departures_in_window
        total_busy_util += bf_est # For c=1, E[min(N,1)]/1 is same as busy_frac
        total_dep_rate += (departures_in_window / win_len) if win_len > 0 else 0
        total_lam_eff += (departures_in_window / win_len) if win_len > 0 else 0
        total_p_loss += pl_est
        
        seed_list.append(seed_val)

    seeds_used = N
    avg_L = total_L / seeds_used
    avg_W = total_W / seeds_used
    avg_bf = total_busy_frac / seeds_used
    avg_pw = total_p_wait / seeds_used
    avg_arr = total_arr / seeds_used
    avg_blk = total_blk / seeds_used
    avg_dep = total_dep / seeds_used
    avg_bu = total_busy_util / seeds_used
    avg_dr = total_dep_rate / seeds_used
    avg_le = total_lam_eff / seeds_used
    avg_pl = total_p_loss / seeds_used
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(horizon_hours - warmup_time, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dr, 6),
        "lam_eff": round(avg_le, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
