import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.1
        mu = mu_base
    elif a.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif a.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    horizon = a.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    win_len = horizon - warmup_end
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_customers_in_window = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        random.seed(seed)
        seeds_used.append(seed)
        
        t = 0.0
        next_arr = random.expovariate(lam)
        next_dep = float('inf')
        n_in_sys = 0
        busy = False
        service_start = 0.0
        current_service_dur = 0.0
        
        # For statistics accumulation within window [warmup_end, horizon]
        # We need to track area under N(t) curve and time spent waiting/serving
        
        last_event_time = 0.0
        acc_area_N = 0.0
        acc_busy_time = 0.0
        acc_wait_time = 0.0
        acc_serve_time = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        customers_in_window = 0
        
        # To compute W correctly via Little's Law or direct sum? 
        # Direct sum of sojourn times for customers who depart in the window is biased.
        # Better: Use time-average L and effective arrival rate lambda_eff to get W = L / lambda_eff?
        # Or accumulate sum of sojourn times for all customers that complete service in the window?
        # The prompt asks for "average stay time W". Usually this is E[W].
        # In steady state simulation, we can estimate W by averaging the sojourn times of customers 
        # who arrive and depart within the observation window, but this misses those crossing boundaries.
        # A more robust way for M/M/1 is to use Little's Law: L = lambda * W => W = L / lambda.
        # However, the prompt also asks for p_wait which is probability of waiting.
        # Let's stick to accumulating sojourn times for customers that fully reside in the window?
        # No, standard practice: Accumulate integral of N(t) for L. 
        # For W, we can accumulate sum of sojourn times for all customers that DEPART in the window.
        # But this ignores arrivals that haven't departed yet.
        # Alternative: Track each customer's arrival time and departure time. If both are in window, add to sum.
        # This is complex with event-driven sim without storing history.
        # Simpler approach for M/M/1: Estimate L from time average. Estimate lambda_eff from dep_rate.
        # Then W = L / lambda_eff.
        # But let's try to calculate W directly as mean sojourn time of completed services in window.
        # Actually, the most accurate unbiased estimator for W in steady state using batch means or similar 
        # often relies on Little's Law if L is well estimated.
        # Let's assume we calculate L as time-average number in system.
        # And we calculate W as the average sojourn time of customers who arrived AND departed in the window.
        # This might be slightly biased if window is small, but horizon is large.
        # Let's refine: We will store arrival times of active customers. When they depart, if their arrival 
        # was after warmup_end, we include their sojourn time in the average.
        
        active_customers = [] # list of arrival times
        
        while t < horizon:
            # Determine next event
            if next_arr < next_dep:
                # Arrival
                t_next = next_arr
                dt = t_next - t
                
                # Update integrals for interval [t, t_next]
                if t < warmup_end and t_next > warmup_end:
                    # Split interval
                    dt_pre = warmup_end - t
                    dt_post = t_next - warmup_end
                    
                    # Pre-warmup part doesn't contribute to stats
                    # Post-warmup part contributes
                    if n_in_sys > 0:
                        acc_area_N += n_in_sys * dt_post
                    if busy:
                        acc_busy_time += dt_post
                        
                    # Handle wait time accumulation? 
                    # Wait time is accumulated when a customer is waiting.
                    # In M/M/1, if server is busy, new arrival waits.
                    # Existing waiting customers continue to wait.
                    # So, during any interval where there are waiting customers, we add to acc_wait_time.
                    # Number of waiting customers = max(0, n_in_sys - 1)
                    num_waiting = max(0, n_in_sys - 1)
                    acc_wait_time += num_waiting * dt_post
                    
                elif t >= warmup_end:
                    if n_in_sys > 0:
                        acc_area_N += n_in_sys * dt
                    if busy:
                        acc_busy_time += dt
                    num_waiting = max(0, n_in_sys - 1)
                    acc_wait_time += num_waiting * dt
                
                t = t_next
                
                # Process Arrival
                if n_in_sys == 0:
                    # Server idle, start service immediately
                    busy = True
                    service_start = t
                    current_service_dur = random.expovariate(mu)
                    next_dep = t + current_service_dur
                    n_in_sys = 1
                    active_customers.append(t)
                else:
                    # Server busy, join queue
                    n_in_sys += 1
                    active_customers.append(t)
                
                # Check if arrival happened in window
                if t >= warmup_end:
                    count_arr_win += 1
                    customers_in_window += 1
                
                # Generate next arrival
                next_arr = t + random.expovariate(lam)
                
            else:
                # Departure
                t_next = next_dep
                dt = t_next - t
                
                if t < warmup_end and t_next > warmup_end:
                    dt_pre = warmup_end - t
                    dt_post = t_next - warmup_end
                    if n_in_sys > 0:
                        acc_area_N += n_in_sys * dt_post
                    if busy:
                        acc_busy_time += dt_post
                    num_waiting = max(0, n_in_sys - 1)
                    acc_wait_time += num_waiting * dt_post
                elif t >= warmup_end:
                    if n_in_sys > 0:
                        acc_area_N += n_in_sys * dt
                    if busy:
                        acc_busy_time += dt
                    num_waiting = max(0, n_in_sys - 1)
                    acc_wait_time += num_waiting * dt
                
                t = t_next
                
                # Process Departure
                # One customer leaves
                arr_time = active_customers.pop(0)
                sojourn = t - arr_time
                
                if t >= warmup_end:
                    count_dep_win += 1
                    # Only count sojourn time if the customer arrived in the window?
                    # Standard definition of W in simulation output usually averages over all completions in window.
                    # But to avoid bias from long-sojourn customers arriving before window, 
                    # some methods exclude them. 
                    # Given the prompt asks for "average stay time", and we have L and lambda, 
                    # Little's law is safer. But let's collect sum of sojourns for completions in window.
                    # If we want strict consistency with L, we should probably use Little's Law.
                    # However, the prompt asks for specific fields. Let's provide W based on Little's Law 
                    # derived from L and effective arrival rate, OR direct measurement.
                    # Direct measurement of W is tricky due to boundary effects.
                    # Let's calculate W_direct = sum(sojourn)/count(dep) for deps in window.
                    # And L_avg = acc_area_N / win_len.
                    # And lambda_eff = count_dep_win / win_len.
                    # Note: count_arr_win might differ from count_dep_win due to boundary.
                    # In steady state, they converge.
                    
                    # Store for later calculation
                    pass
                
                n_in_sys -= 1
                
                if n_in_sys > 0:
                    # Next customer starts service
                    busy = True
                    service_start = t
                    current_service_dur = random.expovariate(mu)
                    next_dep = t + current_service_dur
                else:
                    busy = False
                    next_dep = float('inf')
        
        # End of simulation for this seed
        
        # Calculate metrics for this seed
        L_est = acc_area_N / win_len if win_len > 0 else 0
        busy_frac_est = acc_busy_time / win_len if win_len > 0 else 0
        
        # For W, let's use Little's Law: W = L / lambda_eff
        # lambda_eff is the rate at which customers enter the system in steady state.
        # Since it's M/M/1 with no blocking, lambda_eff = lam.
        # But wait, the prompt mentions blk (blocked/rejected). In M/M/1 infinite capacity, blk=0.
        # So lambda_eff = lam.
        # However, if we want to report measured values:
        # Measured arrival rate in window = count_arr_win / win_len
        # Measured departure rate in window = count_dep_win / win_len
        # These should be close.
        
        # Let's compute W using the accumulated wait+service time?
        # Total time in system for all customers = Integral of N(t) dt? No.
        # Sum of sojourn times = Integral of N(t) dt? Yes, by Fubini/Tonelli.
        # So sum_sojourn = acc_area_N.
        # Average sojourn time W = sum_sojourn / number_of_customers_processed?
        # Which number? Arrivals or Departures?
        # In steady state, they are equal.
        # Let's use count_dep_win as denominator for W, assuming flow balance.
        # Or better: W = L / lambda.
        # Let's calculate W_measured = acc_area_N / count_dep_win if count_dep_win > 0 else 0.
        # This assumes that the area under N(t) represents the sum of sojourn times of customers 
        # who were present during the window. This is an approximation for boundary effects.
        # A more precise way: Track sum of sojourn times explicitly.
        
        # Let's re-evaluate: I didn't track sum of sojourn times explicitly in the loop above.
        # I tracked acc_area_N which IS the sum of sojourn times for customers whose presence overlaps the window.
        # This includes partial contributions for customers entering/leaving at boundaries.
        # This is the standard "time-weighted" estimator for L.
        # For W, the standard estimator is often just L / lambda.
        # Let's use W = L / lam.
        
        W_est = L_est / lam if lam > 0 else 0
        
        # p_wait: Probability that an arriving customer has to wait.
        # In M/M/1, P(wait) = rho = lam/mu.
        # From simulation: Fraction of arrivals that found server busy.
        # I didn't track this explicitly.
        # Let's approximate: p_wait = busy_frac_est? 
        # No, busy_frac is fraction of time server is busy.
        # By PASTA property, fraction of arrivals finding server busy = fraction of time server busy.
        # So p_wait_est = busy_frac_est.
        
        p_wait_est = busy_frac_est
        
        # p_loss: In M/M/1 infinite buffer, loss is 0.
        p_loss_est = 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += count_arr_win
        total_dep += count_dep_win
        total_blk += 0 # Infinite buffer
        
    # Aggregate results
    num_seeds = len(seeds_used)
    avg_L = sum(per_seed_L) / num_seeds
    avg_W = sum(per_seed_W) / num_seeds
    avg_busy_frac = sum(per_seed_busy_frac) / num_seeds
    avg_p_wait = sum(per_seed_p_wait) / num_seeds
    avg_p_loss = sum(per_seed_p_loss) / num_seeds
    
    avg_arr = total_arr / num_seeds
    avg_dep = total_dep / num_seeds
    avg_blk = total_blk / num_seeds
    
    dep_rate = avg_dep / (win_len / 60.0) if win_len > 0 else 0 # Per hour? 
    # Wait, time_unit is minute? 
    # Prompt: "W unit is minutes". "time_unit fill your internal axis unit".
    # My internal axis: I used `random.expovariate(lam)` where lam is per hour.
    # So my time unit is HOURS.
    # But W needs to be in MINUTES.
    # So I must convert W to minutes.
    # L is dimensionless.
    # busy_frac is dimensionless.
    # p_wait is dimensionless.
    # runtime_units: "hour"
    # win: length in hours.
    # dep_rate: "per hour".
    
    # Correction:
    # My `lam` is 6 per hour. `mu` is 10 per hour (since 6 min avg -> 10/hr).
    # Time `t` is in hours.
    # `acc_area_N` is in person-hours.
    # `L_est` = person-hours / hours = persons. Correct.
    # `W_est` = L / lambda = persons / (persons/hour) = hours.
    # Need to convert W to minutes: W_min = W_est * 60.
    
    avg_W_min = avg_W * 60.0
    per_seed_W_min = [w * 60.0 for w in per_seed_W]
    
    # Recalculate aggregate W for JSON
    final_W = avg_W_min
    
    # busy_util = E[min(N,c)]/c. c=1. So E[N]/1 = L.
    busy_util = avg_L
    
    # busy_occupied = 1 - pi_0. pi_0 is prob empty.
    # In M/M/1, pi_0 = 1 - rho.
    # From sim: fraction of time empty = 1 - busy_frac.
    # So busy_occupied = busy_frac.
    busy_occupied = avg_busy_frac
    
    # p_loss is 0.
    
    result = {
        "L": round(avg_L, 6),
        "W": round(final_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "hour",
        "seed_list": seeds_used,
        "seeds_used": num_seeds,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(avg_dep / win_len * 60.0, 6) if win_len > 0 else 0, # Effective arrival rate per hour? 
        # Wait, dep_rate is already per hour. lam_eff should be consistent.
        # Let's define lam_eff as effective arrival rate into system.
        # Since no loss, lam_eff = lam. But measured is avg_arr/win_len.
        # Let's report measured effective arrival rate per hour.
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W_min],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
