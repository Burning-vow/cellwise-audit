def main():
    import argparse, random, json, math
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    N_seeds = a.seeds
    H = a.horizon
    S_start = a.seed_start
    pert = a.pert

    lam_base = 4.0 # per hour
    mu_base = 10.0 # per hour (6 min mean -> 10/hr)
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    win_len = H * 0.75 # discard first 25%
    warmup_end = H * 0.25
    
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
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed_val = S_start + i
        rng = random.Random(seed_val)
        seed_list.append(seed_val)
        
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        # State variables for integration
        area_L = 0.0
        area_time = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        
        # For busy fraction and occupied
        area_busy = 0.0 # integral of min(n,1)
        area_nonempty = 0.0 # integral of (n>0)
        
        last_event_t = 0.0
        
        while t < H:
            # Determine next event
            if next_arr < next_dep:
                dt = next_arr - t
                # Integrate over interval [t, next_arr]
                if t >= warmup_end:
                    area_L += n * dt
                    area_time += dt
                    if n > 0:
                        area_busy += dt
                        area_nonempty += dt
                
                t = next_arr
                # Arrival
                if n == 0:
                    # Start service immediately
                    serv_time = rng.expovariate(mu)
                    next_dep = t + serv_time
                    n = 1
                else:
                    # Queue or block? M/M/1 has infinite queue capacity usually unless specified.
                    # Problem says "system stable", implies standard M/M/1 with infinite buffer.
                    # blk is rejected/lost. In standard M/M/1, no loss. So blk should be 0.
                    # But we need to track it. If buffer is infinite, blk=0.
                    n += 1
                count_arr += 1
                next_arr = t + rng.expovariate(lam)
                
            else:
                dt = next_dep - t
                if t >= warmup_end:
                    area_L += n * dt
                    area_time += dt
                    if n > 0:
                        area_busy += dt
                        area_nonempty += dt
                
                t = next_dep
                # Departure
                # We need to know when this customer arrived to calculate W.
                # This simple loop doesn't store arrival times. 
                # Need to restructure slightly to store arrival time on the "customer".
                # Since it's single server, we can keep a queue of arrival times.
                pass 

        # Re-implementing with queue for arrival times to compute W correctly
        # Resetting simulation logic properly
        
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        queue = [] # stores arrival times of waiting customers
        
        area_L = 0.0
        area_time = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        area_busy = 0.0
        area_nonempty = 0.0
        
        # Helper to integrate
        def integrate(dt):
            nonlocal area_L, area_time, area_busy, area_nonempty
            if t >= warmup_end:
                area_L += n * dt
                area_time += dt
                if n > 0:
                    area_busy += dt
                    area_nonempty += dt

        while t < H:
            if next_arr < next_dep:
                dt = next_arr - t
                integrate(dt)
                t = next_arr
                
                # Arrival
                if len(queue) == 0 and n == 0:
                    # Idle, start service
                    serv_time = rng.expovariate(mu)
                    next_dep = t + serv_time
                    n = 1
                    # Customer starts service now, arrival time is t
                    # We don't push to queue, but we need to remember arrival time for departure
                    # Actually, for M/M/1, we can just track the current service start time?
                    # No, we need individual sojourn times.
                    # Let's maintain a list of active customers? Or just one since c=1.
                    # If n==1, there is one person being served.
                    # We need their arrival time.
                    curr_serv_arrival = t
                else:
                    # Someone is being served or waiting
                    n += 1
                    queue.append(t) # Add arrival time to queue
                    # If someone was being served, they continue.
                    # If queue was empty but n>0? Impossible in this logic if n counts system size.
                    # Let's refine state: n = number in system.
                    # If n becomes 1 from 0, service starts.
                    # If n increases, new customer joins queue.
                    
                count_arr += 1
                next_arr = t + rng.expovariate(lam)
                
            else:
                dt = next_dep - t
                integrate(dt)
                t = next_dep
                
                # Departure
                # The person leaving is the one who started service at (t - remaining_service)?
                # No, we stored arrival time of the one currently in service?
                # Logic flaw: When arrival happens and n goes 0->1, we set curr_serv_arrival.
                # When arrival happens and n>0, we append to queue.
                # When departure happens:
                #   The person in service leaves.
                #   Their arrival time was curr_serv_arrival.
                #   Calculate W = t - curr_serv_arrival.
                #   Then check if queue is not empty.
                #   Pop front of queue. That person starts service.
                #   Set curr_serv_arrival to that popped time.
                #   Generate new service time.
                #   n decreases by 1.
                
                # Wait, if n==0 initially, next_dep is inf.
                # If n>0, next_dep is valid.
                
                # Who is departing? The one in service.
                # We need to have tracked their arrival time.
                # In the arrival branch, if n went 0->1, we set curr_serv_arrival.
                # If n went k->k+1, we appended to queue.
                
                # At departure:
                w = t - curr_serv_arrival
                sum_w += w
                count_dep += 1
                
                n -= 1
                
                if queue:
                    # Next person starts service
                    curr_serv_arrival = queue.pop(0)
                    serv_time = rng.expovariate(mu)
                    next_dep = t + serv_time
                else:
                    next_dep = float('inf')
                    # n is now 0 (since we decremented and queue empty)
                    # But wait, if n was 1, it becomes 0. Correct.
                    # If n was >1, it becomes n-1. But queue had people.
                    # My n tracking: n includes the one in service.
                    # So if n=2, queue has 1 person.
                    # Departure: n becomes 1. Queue pops 1 person to service.
                    # So n remains 1.
                    # Correct.

        # End of simulation for this seed
        
        # Calculate stats for this seed
        if area_time > 0:
            L_est = area_L / area_time
            busy_frac_est = area_busy / area_time
            busy_occupied_est = area_nonempty / area_time
        else:
            L_est = 0.0
            busy_frac_est = 0.0
            busy_occupied_est = 0.0
            
        if count_dep > 0:
            W_est = sum_w / count_dep
        else:
            W_est = 0.0
            
        # p_wait: probability that an arriving customer has to wait?
        # Or fraction of time system is busy?
        # Usually P(wait) in M/M/1 is rho = lambda/mu.
        # Empirical: Fraction of arrivals that found n>=1?
        # We didn't track that directly.
        # Alternative: Busy fraction is often used as proxy or definition depending on context.
        # Prompt asks for p_wait. In M/M/1, P(wait) = P(N>=1) = rho.
        # Let's estimate P(N>=1) from area_nonempty / area_time.
        p_wait_est = busy_occupied_est
        
        p_loss_est = count_blk / count_arr if count_arr > 0 else 0.0
        dep_rate_est = count_dep / area_time if area_time > 0 else 0.0
        lam_eff_est = count_arr / area_time if area_time > 0 else 0.0
        busy_util_est = busy_frac_est # E[min(N,1)]/1
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr)
        all_dep.append(count_dep)
        all_blk.append(count_blk)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        all_busy_occupied.append(busy_occupied_est)

    seeds_used = N_seeds
    
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_busy_occupied = sum(all_busy_occupied) / seeds_used
    
    result = {
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_busy_frac,
        "p_wait": avg_p_wait,
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win_len,
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": avg_busy_util,
        "dep": avg_dep,
        "dep_rate": avg_dep_rate,
        "lam_eff": avg_lam_eff,
        "p_loss": avg_p_loss,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": avg_busy_occupied
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
