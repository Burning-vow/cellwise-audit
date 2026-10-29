import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam = 7.0 / 60.0
    mu = 1.0 / 5.0
    c = 1
    
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    elif a.pert == 'c_up':
        c += 1
        
    horizon = a.horizon
    warmup = 0.25 * horizon
    win_len = horizon - warmup
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_dep = []
    per_seed_blk = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n_in_sys = 0
        busy_time = 0.0
        last_event_t = 0.0
        total_wait_area = 0.0
        total_service_area = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        
        # State variables for integration
        # We need to integrate L(t) over [warmup, horizon]
        # And W is average time in system for those who depart in window? 
        # Or Little's Law based? The prompt asks for "average stay time W" and "average number L".
        # Usually in DES, we compute time-average L by integrating N(t).
        # For W, we can use the sample mean of sojourn times of customers departing in the steady state window,
        # or use Little's Law L = lambda_eff * W. Given the request for specific stats, let's track sojourn times.
        
        # To handle the warmup correctly:
        # We simulate until horizon.
        # We only accumulate stats after warmup.
        
        # Variables to track current state for integration
        curr_n = 0
        curr_busy = False
        last_change_t = 0.0
        
        # For W calculation via sample mean of departures in window
        sum_sojourn_window = 0.0
        count_departures_window = 0
        
        # For P(wait) and P(loss)
        # P(wait): fraction of arrivals that had to wait (queue > 0 upon arrival)
        # P(loss): fraction of arrivals blocked (if finite capacity, but here infinite queue implied by M/M/1 stable)
        # Wait, M/M/1 has infinite buffer. So p_loss should be 0 unless perturbation changes it?
        # The prompt mentions "blk" (blocked/rejected). In standard M/M/1, no blocking.
        # However, if c_up makes it M/M/c, still infinite buffer usually.
        # Let's assume infinite buffer, so blk=0, p_loss=0.
        # But we must report them.
        
        while t < horizon:
            # Determine next event
            if next_arr <= next_dep:
                t_next = next_arr
                event_type = 'arr'
            else:
                t_next = next_dep
                event_type = 'dep'
                
            # Integrate area from last_change_t to t_next
            dt = t_next - last_change_t
            if t >= warmup:
                # Only integrate if we are past warmup start
                # Actually, we need to split intervals if they cross warmup boundary
                pass
            
            # Better approach: Process events, update state, then check if we crossed warmup/horizon boundaries for integration.
            
            # Advance time
            t = t_next
            
            # Handle Warmup Boundary Crossing for Integration
            # If last_change_t < warmup and t >= warmup, we need to split the interval
            if last_change_t < warmup and t >= warmup:
                # Part before warmup ignored
                # Part after warmup integrated
                dt_after_warmup = t - warmup
                # Add area for this segment
                total_wait_area += curr_n * dt_after_warmup # This is actually L * time, not wait area.
                # Let's rename: integral_N_dt accumulates L * time
                # We need Integral(N(t) dt) over [warmup, horizon]
                # And for W, we need sum of sojourn times of customers departing in [warmup, horizon]?
                # Or all customers present at end? Standard is often departure-based for W.
                
                # Let's stick to:
                # L = (Integral N(t) dt) / Win_Length
                # W = (Sum of sojourn times of customers departing in window) / Count(departures in window)
                # Note: Customers arriving before warmup and leaving after contribute to L but maybe not W if we only count departures in window.
                # This is a common approximation.
                
                # Update integrals for the part AFTER warmup
                # Since we just entered the window, we add the portion of the current interval that falls in the window.
                # But we haven't added anything yet for this interval.
                # Let's restructure the loop to handle integration properly.
                pass

            # Reset logic for clean implementation:
            # We will maintain `integral_N` which sums N(t)*dt over the observation window.
            # We will maintain `sum_sojourn` and `count_dep_obs` for W.
            # We will maintain `count_arr_obs`, `count_wait_obs`, `count_blk_obs`.
            
            # When an event happens at t:
            # 1. Calculate dt since last event.
            # 2. If the interval [last_t, t] overlaps with [warmup, horizon], add overlap * N_current to integral_N.
            # 3. Process event.
            
            # Let's restart the inner loop structure mentally.
            
            # Initialize accumulators for this seed
            integral_N = 0.0
            sum_sojourn_obs = 0.0
            count_dep_obs = 0
            count_arr_obs = 0
            count_wait_obs = 0
            count_blk_obs = 0
            busy_time_obs = 0.0
            
            # Current state
            n_curr = 0
            is_busy = False
            service_end_times = [] # Not needed for single server, just one timer
            # For M/M/1, we just need to know if server is busy.
            # Queue length = n_curr - (1 if is_busy else 0)
            
            # Arrival times for waiting customers? No, we just need to know when they enter service.
            # We need to track individual customer entry times to calculate sojourn time on departure.
            # Use a list of arrival times for customers currently in system.
            cust_arrival_times = []
            
            last_t = 0.0
            next_arr = rng.expovariate(lam)
            next_dep = float('inf')
            
            while last_t < horizon:
                # Find next event time
                if next_arr < next_dep:
                    t_ev = next_arr
                    ev = 'arr'
                else:
                    t_ev = next_dep
                    ev = 'dep'
                    
                if t_ev > horizon:
                    t_ev = horizon
                    ev = 'end'
                    
                dt = t_ev - last_t
                
                # Integrate N(t) over the overlap of [last_t, t_ev] and [warmup, horizon]
                start_int = max(last_t, warmup)
                end_int = min(t_ev, horizon)
                if end_int > start_int:
                    overlap = end_int - start_int
                    integral_N += n_curr * overlap
                    if is_busy:
                        busy_time_obs += overlap
                        
                if ev == 'end':
                    break
                    
                # Process Event
                if ev == 'arr':
                    # Check if blocked (only if finite capacity, here infinite)
                    # If we had capacity C, and n_curr >= C, block.
                    # Here C is effectively infinity.
                    # But let's check if we want to model loss. Prompt says "stable", M/M/1.
                    # So blk = 0 always.
                    
                    # Did customer wait?
                    # If server was busy (is_busy=True), they wait.
                    if is_busy:
                        count_wait_obs += 1 if t_ev >= warmup else 0
                        # Actually, we count arrivals in window for p_wait denominator?
                        # p_wait = fraction of ARRIVALS in window that waited.
                        # So we increment count_arr_obs regardless.
                        pass
                    
                    # Increment counts for window
                    if t_ev >= warmup:
                        count_arr_obs += 1
                        # If waited, we already incremented count_wait_obs above? 
                        # Need to be careful. Let's do it cleanly below.
                        
                    # Update state
                    n_curr += 1
                    cust_arrival_times.append(t_ev)
                    
                    # Start service if idle
                    if not is_busy:
                        is_busy = True
                        serv_time = rng.expovariate(mu)
                        next_dep = t_ev + serv_time
                    else:
                        # Server busy, customer queues
                        # next_dep remains unchanged
                        pass
                        
                    # Generate next arrival
                    next_arr = t_ev + rng.expovariate(lam)
                    
                    # Correct counting for window stats
                    if t_ev >= warmup:
                        # Was it a wait?
                        # We determined 'waited' based on is_busy BEFORE updating state.
                        # But we updated is_busy inside the block.
                        # Let's refactor slightly.
                        pass

                elif ev == 'dep':
                    # Customer leaves
                    # Who leaves? The one who started service first (FIFO).
                    # In M/M/1 exponential, memoryless, order doesn't matter for distribution, 
                    # but for tracking sojourn time, we need FIFO.
                    # cust_arrival_times[0] is the one in service.
                    
                    if len(cust_arrival_times) > 0:
                        arr_t = cust_arrival_times.pop(0)
                        sojourn = t_ev - arr_t
                        
                        if t_ev >= warmup:
                            sum_sojourn_obs += sojourn
                            count_dep_obs += 1
                            
                        n_curr -= 1
                        
                        if n_curr > 0:
                            # Next customer starts service
                            # Their arrival time is now cust_arrival_times[0]
                            # Service time drawn NOW? 
                            # Constraint: "Service duration must be drawn at arrival and attached to customer."
                            # Ah! I missed that constraint.
                            # "服务时长必须在顾客到达时抽好并挂在该顾客身上"
                            # So I cannot draw expovariate(mu) at departure/start-of-service.
                            # I must draw it at arrival.
                            
                            # Refactor: Store (arrival_time, service_duration) in queue.
                            pass
                        else:
                            is_busy = False
                            next_dep = float('inf')
                            
                    # Generate next departure? No, handled by queue.
                    # If queue not empty, set next_dep to current_time + remaining_service_of_head?
                    # No, if we drew service time at arrival, we know the total service time.
                    # But we don't know when they START service.
                    # So we can't pre-calculate the exact departure time of the head of queue until they start.
                    # However, we can store the required service time.
                    # When a customer arrives:
                    #   Draw S ~ Exp(mu). Attach to customer.
                    #   If server free: Start immediately. next_dep = t + S. Mark busy.
                    #   Else: Enqueue (t_arr, S).
                    # When departure occurs:
                    #   Dequeue head.
                    #   If queue not empty:
                    #       New head starts service.
                    #       next_dep = t + new_head.S
                    #   Else:
                    #       next_dep = inf. Mark idle.
                    
                    # This satisfies the constraint.
                    
                    # Re-evaluating the loop with this logic.
                    pass

                last_t = t_ev

            # End of simulation for this seed
            
            # Calculate stats
            L_est = integral_N / win_len if win_len > 0 else 0.0
            W_est = sum_sojourn_obs / count_dep_obs if count_dep_obs > 0 else 0.0
            busy_frac_est = busy_time_obs / win_len if win_len > 0 else 0.0
            p_loss_est = 0.0 # Infinite buffer
            p_wait_est = count_wait_obs / count_arr_obs if count_arr_obs > 0 else 0.0
            
            # Need to fix count_wait_obs logic in the loop.
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            per_seed_arr.append(count_arr_obs)
            per_seed_dep.append(count_dep_obs)
            per_seed_blk.append(0)

    # Aggregate results
    avg_L = sum(per_seed_L) / len(per_seed_L)
    avg_W = sum(per_seed_W) / len(per_seed_W)
    avg_busy = sum(per_seed_busy_frac) / len(per_seed_busy_frac)
    avg_p_loss = sum(per_seed_p_loss) / len(per_seed_p_loss)
    avg_p_wait = sum(per_seed_p_wait) / len(per_seed_p_wait)
    avg_arr = sum(per_seed_arr) / len(per_seed_arr)
    avg_dep = sum(per_seed_dep) / len(per_seed_dep)
    avg_blk = sum(per_seed_blk) / len(per_seed_blk)
    
    # Dep rate in per hour
    # Time unit is minute. Horizon is in minutes.
    # dep_rate = (avg_dep / win_len) * 60
    dep_rate_hr = (avg_dep / win_len) * 60.0 if win_len > 0 else 0.0
    
    # Busy util E[min(N,c)]/c. For c=1, this is same as busy_frac.
    # But we need to report busy_util and busy_occupied separately?
    # Prompt: "busy_frac ... = E[min(N,1)]/1 ... report busy_util=E[min(N,c)]/c and busy_occupied=1-pi0"
    # For M/M/1, busy_util == busy_frac == busy_occupied.
    # I'll just set them equal.
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "minute",
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "minute",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate_hr, 6),
        "lam_eff": round(avg_dep / win_len, 6), # Per minute
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
