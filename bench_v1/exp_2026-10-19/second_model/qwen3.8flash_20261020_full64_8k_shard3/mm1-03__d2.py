import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    if a.pert == 'lam_up': lam_base *= 1.1
    elif a.pert == 'mu_up': mu_base *= 1.1
    elif a.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam_base)
        service_time = None
        next_dep = float('inf')
        
        area_n = 0.0
        area_busy = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        total_stay_sum = 0.0
        
        # For tracking arrival times to compute stay time
        arrivals_in_window = []
        
        while t < horizon:
            # Determine next event
            if next_arr <= next_dep:
                # Arrival
                t_prev = t
                dt = next_arr - t
                if t >= win_start:
                    area_n += n * dt
                    if n > 0:
                        area_busy += dt
                t = next_arr
                
                if t >= win_start:
                    arr_count += 1
                
                # Generate service time at arrival
                svc = rng.expovariate(mu_base)
                
                if n == 0:
                    # Start service immediately
                    n = 1
                    service_time = svc
                    next_dep = t + svc
                else:
                    # Queue or block? M/M/1 with infinite queue -> no blocking
                    # But problem says "system stable", standard M/M/1 has infinite capacity
                    # So no blocking in standard M/M/1
                    n += 1
                    # If this is the first in queue, it will start when current finishes
                    # We need to track individual customers for W calculation
                    # Simpler: use Little's law approximation via area integral for L, 
                    # and for W we can estimate from average stay of completed customers in window
                    # Let's store arrival time for each customer in system
                    # Actually, let's maintain a list of arrival times for customers currently in system
                    # This gets complex. Alternative: track completions and their stay times.
                    
                    # Let me restructure: keep a deque of arrival times for queued customers
                    # When service completes, pop the oldest arrival (FIFO)
                    pass
                
                # Schedule next arrival
                next_arr = t + rng.expovariate(lam_base)
                
            else:
                # Departure
                t_prev = t
                dt = next_dep - t
                if t >= win_start:
                    area_n += n * dt
                    if n > 0:
                        area_busy += dt
                t = next_dep
                
                # Customer leaves
                if n > 0:
                    if t >= win_start:
                        dep_count += 1
                        # Need to know how long this customer stayed
                        # We need to track arrival times properly
                        pass
                    
                    n -= 1
                    if n > 0:
                        # Next customer starts service
                        # We need their pre-generated service time... but we didn't store per-customer svc times
                        # Let me redo the approach with explicit customer objects
                        pass
                    else:
                        next_dep = float('inf')
                        service_time = None
        
        # The above logic is flawed because I need per-customer service times stored at arrival
        # Let me rewrite cleanly using a proper event-driven simulation with customer records
        
        # Reset and do it right
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        
        # List of (arrival_time, service_duration) for customers in system
        # FIFO order
        customers = []
        
        area_n = 0.0
        area_busy = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        stay_times_completed = []
        
        while t < horizon:
            if next_arr <= next_dep:
                dt = next_arr - t
                if t >= win_start:
                    area_n += n * dt
                    if n > 0:
                        area_busy += dt
                t = next_arr
                
                if t >= win_start:
                    arr_count += 1
                
                svc = rng.expovariate(mu_base)
                customers.append((t, svc))
                n = len(customers)
                
                if n == 1:
                    # First customer starts service now
                    next_dep = t + svc
                
                next_arr = t + rng.expovariate(lam_base)
                
            else:
                dt = next_dep - t
                if t >= win_start:
                    area_n += n * dt
                    if n > 0:
                        area_busy += dt
                t = next_dep
                
                # Complete service of front customer
                if customers:
                    arr_t, svc_dur = customers.pop(0)
                    n = len(customers)
                    
                    if t >= win_start:
                        dep_count += 1
                        stay = t - arr_t
                        stay_times_completed.append(stay)
                    
                    if n > 0:
                        # Next customer starts service
                        next_dep = t + customers[0][1]
                    else:
                        next_dep = float('inf')
        
        # Compute statistics for this seed
        if win_len > 0:
            L_est = area_n / win_len
            busy_frac_est = area_busy / win_len
            
            if dep_count > 0:
                W_est = sum(stay_times_completed) / dep_count
            else:
                W_est = 0.0
            
            p_wait_est = 0.0
            # Probability of waiting: fraction of arrivals that had to wait
            # In M/M/1, an arriving customer waits if server is busy
            # We can approximate by checking state at arrival times within window
            # Or use theoretical relation. Let's count directly.
            # Re-simulate just for p_wait counting would be wasteful.
            # Alternative: during sim, at each arrival in window, check if n_before > 0
            # I didn't track that. Let me add a counter.
            
            # Since I already ran the sim, let me note: p_wait in M/M/1 steady state = rho = lambda/mu
            # But we want empirical. Let me re-run quickly or adjust.
            # For brevity, I'll compute p_wait as dep_count-based proxy isn't right.
            # Let me just use the fact that in the loop, at arrival, if n>0 before adding, they wait.
            # I'll modify the main loop slightly in my head: actually, let me just recalculate.
            
            # Given constraints, let me assume p_wait ≈ busy_frac for single server approx, 
            # but better: count arrivals where server was busy.
            # I'll do a second quick pass or integrate into first. Let me integrate properly.
            
            # Redoing with proper p_wait tracking:
            rng = random.Random(seed)
            t = 0.0
            n = 0
            next_arr = rng.expovariate(lam_base)
            next_dep = float('inf')
            customers = []
            area_n = 0.0
            area_busy = 0.0
            arr_count = 0
            dep_count = 0
            blk_count = 0
            stay_times_completed = []
            wait_count = 0
            
            while t < horizon:
                if next_arr <= next_dep:
                    dt = next_arr - t
                    if t >= win_start:
                        area_n += n * dt
                        if n > 0:
                            area_busy += dt
                    t = next_arr
                    
                    if t >= win_start:
                        arr_count += 1
                        if n > 0:
                            wait_count += 1
                    
                    svc = rng.expovariate(mu_base)
                    customers.append((t, svc))
                    n = len(customers)
                    
                    if n == 1:
                        next_dep = t + svc
                    
                    next_arr = t + rng.expovariate(lam_base)
                    
                else:
                    dt = next_dep - t
                    if t >= win_start:
                        area_n += n * dt
                        if n > 0:
                            area_busy += dt
                    t = next_dep
                    
                    if customers:
                        arr_t, svc_dur = customers.pop(0)
                        n = len(customers)
                        
                        if t >= win_start:
                            dep_count += 1
                            stay = t - arr_t
                            stay_times_completed.append(stay)
                        
                        if n > 0:
                            next_dep = t + customers[0][1]
                        else:
                            next_dep = float('inf')
            
            L_est = area_n / win_len if win_len > 0 else 0.0
            busy_frac_est = area_busy / win_len if win_len > 0 else 0.0
            W_est = sum(stay_times_completed) / dep_count if dep_count > 0 else 0.0
            p_wait_est = wait_count / arr_count if arr_count > 0 else 0.0
            p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
            dep_rate_est = dep_count / win_len if win_len > 0 else 0.0
            lam_eff_est = arr_count / win_len if win_len > 0 else 0.0
            busy_util_est = busy_frac_est  # E[min(N,1)]/1 = P(N>=1) = busy_frac
            busy_occ_est = busy_frac_est   # 1 - pi_0 = P(N>=1)
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(busy_frac_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(arr_count)
            all_blk.append(blk_count)
            all_dep.append(dep_count)
            all_busy_util.append(busy_util_est)
            all_busy_occupied.append(busy_occ_est)
            all_lam_eff.append(lam_eff_est)
            all_p_loss.append(p_loss_est)
            all_dep_rate.append(dep_rate_est)
    
    avg_L = sum(all_L) / seeds_used if seeds_used > 0 else 0.0
    avg_W = sum(all_W) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_frac = sum(all_busy_frac) / seeds_used if seeds_used > 0 else 0.0
    avg_p_wait = sum(all_p_wait) / seeds_used if seeds_used > 0 else 0.0
    avg_arr = sum(all_arr) / seeds_used if seeds_used > 0 else 0.0
    avg_blk = sum(all_blk) / seeds_used if seeds_used > 0 else 0.0
    avg_dep = sum(all_dep) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_util = sum(all_busy_util) / seeds_used if seeds_used > 0 else 0.0
    avg_busy_occ = sum(all_busy_occupied) / seeds_used if seeds_used > 0 else 0.0
    avg_lam_eff = sum(all_lam_eff) / seeds_used if seeds_used > 0 else 0.0
    avg_p_loss = sum(all_p_loss) / seeds_used if seeds_used > 0 else 0.0
    avg_dep_rate = sum(all_dep_rate) / seeds_used if seeds_used > 0 else 0.0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(avg_busy_occ, 6)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
