import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    lam_base = 8.0 # per hour
    mu_base = 60.0 / 12.0 # per hour (mean service time 12 min)
    c = 3
    K = 4 # max capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 4
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H * 0.75 # discard first 25% warmup
    warmup_end = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # State variables
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        # Service completion times for up to c servers
        # We track when each server becomes free. 
        # Since we don't assign specific servers, we can just track the number of busy servers and their finish times.
        # But for discrete event simulation with multiple servers, it's easier to maintain a list of finish times.
        finish_times = [] 
        
        # Statistics accumulators (for area integration)
        # L is average number in system over time window [warmup_end, H]
        # W is average waiting time? No, W usually means sojourn time (waiting + service). 
        # The problem asks for W (minutes). In queueing theory, W often denotes mean sojourn time.
        # Let's assume W is mean sojourn time (time spent in system).
        
        sum_time_weighted_n = 0.0
        last_event_time = 0.0
        total_sojourn_time_sum = 0.0
        count_departures = 0
        count_arrivals = 0
        count_blocked = 0
        
        # For busy fraction: time where n > 0
        sum_time_busy = 0.0
        
        # For busy_util: E[min(n,c)]/c. We need integral of min(n(t), c) dt.
        sum_time_min_nc = 0.0
        
        # Events: Arrival or Departure
        while True:
            # Determine next event time
            next_dep = min(finish_times) if finish_times else float('inf')
            next_ev = min(next_arrival, next_dep)
            
            if next_ev > H:
                break
                
            # Integrate statistics from last_event_time to next_ev
            dt = next_ev - last_event_time
            if last_event_time >= warmup_end:
                # Only accumulate stats after warmup
                # But wait, the prompt says "statistics only accumulated in window after removing first 25% warmup".
                # And "area-type quantities must be integrated before changing state".
                # So we integrate over [max(last_event_time, warmup_end), next_ev]
                
                start_int = max(last_event_time, warmup_end)
                end_int = next_ev
                if start_int < end_int:
                    interval_len = end_int - start_int
                    sum_time_weighted_n += n_in_system * interval_len
                    sum_time_busy += (1 if n_in_system > 0 else 0) * interval_len
                    sum_time_min_nc += min(n_in_system, c) * interval_len
            
            # Process event
            if next_ev == next_arrival:
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    # Draw service time now
                    svc_time = rng.expovariate(mu)
                    finish_times.append(next_ev + svc_time)
                else:
                    count_blocked += 1
                next_arrival = next_ev + rng.expovariate(lam)
            else: # Departure
                # Remove one departure
                idx = finish_times.index(next_ev)
                del finish_times[idx]
                n_in_system -= 1
                count_departures += 1
                # Note: To calculate W (sojourn time), we need arrival time of this customer.
                # This simple model doesn't track individual customers' arrival times easily without a queue structure.
                # However, Little's Law L = lambda * W holds for stable systems.
                # Or we can track entry times. Let's modify approach slightly to track entry times.
                pass
            
            last_event_time = next_ev

        # Re-run with proper tracking for W
        # Reset
        rng = random.Random(s)
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        finish_times = []
        entry_times = [] # Parallel array to finish_times
        
        sum_time_weighted_n = 0.0
        last_event_time = 0.0
        total_sojourn_time_sum = 0.0
        count_departures = 0
        count_arrivals = 0
        count_blocked = 0
        sum_time_busy = 0.0
        sum_time_min_nc = 0.0
        
        while True:
            next_dep = min(finish_times) if finish_times else float('inf')
            next_ev = min(next_arrival, next_dep)
            
            if next_ev > H:
                break
                
            dt = next_ev - last_event_time
            if last_event_time < H: # Always integrate until H, but filter by warmup later? 
                                   # Prompt: "statistics only ... in window after removing first 25%"
                                   # So we integrate only parts within [warmup_end, H]
                start_int = max(last_event_time, warmup_end)
                end_int = min(next_ev, H)
                if start_int < end_int:
                    interval_len = end_int - start_int
                    sum_time_weighted_n += n_in_system * interval_len
                    sum_time_busy += (1 if n_in_system > 0 else 0) * interval_len
                    sum_time_min_nc += min(n_in_system, c) * interval_len

            if next_ev == next_arrival:
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    svc_time = rng.expovariate(mu)
                    finish_times.append(next_ev + svc_time)
                    entry_times.append(next_ev)
                else:
                    count_blocked += 1
                next_arrival = next_ev + rng.expovariate(lam)
            else:
                idx = finish_times.index(next_ev)
                del finish_times[idx]
                entry_time = entry_times.pop(idx)
                n_in_system -= 1
                count_departures += 1
                if entry_time >= warmup_end:
                    total_sojourn_time_sum += (next_ev - entry_time)
            
            last_event_time = next_ev

        # Calculate metrics for this seed
        effective_window = H - warmup_end
        if effective_window <= 0:
            continue
            
        L_est = sum_time_weighted_n / effective_window
        busy_frac_est = sum_time_busy / effective_window
        busy_util_est = sum_time_min_nc / (effective_window * c)
        
        p_loss_est = count_blocked / count_arrivals if count_arrivals > 0 else 0.0
        
        # W estimation: Mean sojourn time of those who departed during/after warmup?
        # Usually W is estimated by total time in system / number of departures in window.
        # But careful: customers arriving before warmup might leave after.
        # Standard estimator: Sum of sojourn times of customers who completed service in window / Count of such customers?
        # Or use Little's Law: W = L / lambda_eff.
        # Let's use direct measurement for consistency with "W (minutes)".
        # If no departures in window, fallback to Little's law or 0.
        if count_departures > 0:
             # Note: total_sojourn_time_sum only includes those who entered after warmup.
             # This might bias if many enter before and leave after.
             # Better: Track all completions.
             pass
        
        # Let's re-evaluate W calculation strategy.
        # Simpler robust way: Use Little's Law on the steady-state estimates.
        # lambda_eff = (count_arrivals - count_blocked) / effective_window ? No, arrivals are Poisson.
        # Effective arrival rate into system = (count_arrivals - count_blocked) / effective_window?
        # Actually, let's stick to the definition: W = Average time spent in system.
        # Estimator: Total time spent by all customers who were in system during window? Complex.
        # Common DES estimator: Sum(sojourn times of all customers who departed during the observation window) / Number of such departures.
        # But we filtered entry_time >= warmup_end above. That's wrong.
        # We should include all departures that happened in [warmup_end, H].
        
        # Let's restart the loop logic for W specifically or fix it.
        # Fix: Accumulate sojourn time for ANY departure occurring in [warmup_end, H].
        
        # Re-running again with corrected W logic
        rng = random.Random(s)
        t = 0.0
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        finish_times = []
        entry_times = []
        
        sum_time_weighted_n = 0.0
        last_event_time = 0.0
        total_sojourn_time_sum = 0.0
        count_departures_in_win = 0
        count_arrivals = 0
        count_blocked = 0
        sum_time_busy = 0.0
        sum_time_min_nc = 0.0
        
        while True:
            next_dep = min(finish_times) if finish_times else float('inf')
            next_ev = min(next_arrival, next_dep)
            
            if next_ev > H:
                break
                
            start_int = max(last_event_time, warmup_end)
            end_int = min(next_ev, H)
            if start_int < end_int:
                interval_len = end_int - start_int
                sum_time_weighted_n += n_in_system * interval_len
                sum_time_busy += (1 if n_in_system > 0 else 0) * interval_len
                sum_time_min_nc += min(n_in_system, c) * interval_len

            if next_ev == next_arrival:
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    svc_time = rng.expovariate(mu)
                    finish_times.append(next_ev + svc_time)
                    entry_times.append(next_ev)
                else:
                    count_blocked += 1
                next_arrival = next_ev + rng.expovariate(lam)
            else:
                idx = finish_times.index(next_ev)
                del finish_times[idx]
                entry_time = entry_times.pop(idx)
                n_in_system -= 1
                
                # Check if departure is in window
                if next_ev >= warmup_end:
                    total_sojourn_time_sum += (next_ev - entry_time)
                    count_departures_in_win += 1
            
            last_event_time = next_ev

        L_est = sum_time_weighted_n / effective_window
        busy_frac_est = sum_time_busy / effective_window
        busy_util_est = sum_time_min_nc / (effective_window * c)
        p_loss_est = count_blocked / count_arrivals if count_arrivals > 0 else 0.0
        
        if count_departures_in_win > 0:
            W_est_hours = total_sojourn_time_sum / count_departures_in_win
        else:
            # Fallback to Little's Law if no departures observed in window (unlikely for large H)
            # lambda_eff = (count_arrivals - count_blocked) / effective_window ?? 
            # Actually, flow balance: dep_rate approx arr_rate * (1-p_loss)
            # Let's use L / lambda_eff
            lam_eff_est = (count_arrivals - count_blocked) / effective_window
            if lam_eff_est > 0:
                W_est_hours = L_est / lam_eff_est
            else:
                W_est_hours = 0.0
                
        W_est_minutes = W_est_hours * 60.0
        
        # p_wait: Probability of waiting? 
        # In M/M/c/K, waiting means joining queue (n >= c upon arrival).
        # We didn't track this directly. 
        # Approximation: P(wait) = P(n >= c) at arrival instants?
        # Or use Erlang C formula approximation? 
        # Let's estimate from simulation: Count arrivals that had to wait vs total admitted.
        # Need to track if an arrival found n >= c.
        
        # One more pass to get p_wait accurately? Or combine.
        # Let's combine everything in one final clean run.
        
        rng = random.Random(s)
        n_in_system = 0
        next_arrival = rng.expovariate(lam)
        finish_times = []
        entry_times = []
        
        sum_time_weighted_n = 0.0
        last_event_time = 0.0
        total_sojourn_time_sum = 0.0
        count_departures_in_win = 0
        count_arrivals = 0
        count_blocked = 0
        count_admitted = 0
        count_waiting_admitted = 0 # Arrivals that joined when n >= c
        sum_time_busy = 0.0
        sum_time_min_nc = 0.0
        
        while True:
            next_dep = min(finish_times) if finish_times else float('inf')
            next_ev = min(next_arrival, next_dep)
            
            if next_ev > H:
                break
                
            start_int = max(last_event_time, warmup_end)
            end_int = min(next_ev, H)
            if start_int < end_int:
                interval_len = end_int - start_int
                sum_time_weighted_n += n_in_system * interval_len
                sum_time_busy += (1 if n_in_system > 0 else 0) * interval_len
                sum_time_min_nc += min(n_in_system, c) * interval_len

            if next_ev == next_arrival:
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    count_admitted += 1
                    if n_in_system > c: # Was already full of servers? 
                        # If n_in_system was c before increment, then this car waits.
                        # Before increment: n_old = n_in_system.
                        # If n_old >= c, then new car waits.
                        # Wait, I incremented n_in_system already.
                        # Let's check condition BEFORE increment.
                        pass
                    
                    # Correction:
                    # Move increment back
                    n_in_system -= 1 
                    count_admitted -= 1
                    
                    if n_in_system >= c:
                        count_waiting_admitted += 1
                        
                    n_in_system += 1
                    count_admitted += 1
                    
                    svc_time = rng.expovariate(mu)
                    finish_times.append(next_ev + svc_time)
                    entry_times.append(next_ev)
                else:
                    count_blocked += 1
                next_arrival = next_ev + rng.expovariate(lam)
            else:
                idx = finish_times.index(next_ev)
                del finish_times[idx]
                entry_time = entry_times.pop(idx)
                n_in_system -= 1
                
                if next_ev >= warmup_end:
                    total_sojourn_time_sum += (next_ev - entry_time)
                    count_departures_in_win += 1
            
            last_event_time = next_ev

        L_est = sum_time_weighted_n / effective_window
        busy_frac_est = sum_time_busy / effective_window
        busy_util_est = sum_time_min_nc / (effective_window * c)
        p_loss_est = count_blocked / count_arrivals if count_arrivals > 0 else 0.0
        
        if count_departures_in_win > 0:
            W_est_hours = total_sojourn_time_sum / count_departures_in_win
        else:
            lam_eff_est = count_admitted / effective_window
            W_est_hours = L_est / lam_eff_est if lam_eff_est > 0 else 0.0
            
        W_est_minutes = W_est_hours * 60.0
        
        p_wait_est = count_waiting_admitted / count_admitted if count_admitted > 0 else 0.0
        
        dep_rate_est = count_departures_in_win / effective_window # per hour
        
        all_L.append(L_est)
        all_W.append(W_est_minutes)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arrivals / N_seeds) # Per seed average? Prompt: "arr is avg per seed count"
        all_blk.append(count_blocked / N_seeds)
        all_dep.append(count_departures_in_win / N_seeds)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        
        seeds_used += 1
        seed_list.append(s)

    # Aggregate results
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
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    
    # Identity checks
    # L = W * lambda_eff?
    # lambda_eff = (avg_arr - avg_blk) / effective_window? No, avg_arr is count.
    # Rate = Count / Time.
    # eff_lambda = (sum(all_arr)*N_seeds - sum(all_blk)*N_seeds) / (seeds_used * effective_window)?
    # Actually all_arr is already divided by N_seeds? No, I did `count_arrivals / N_seeds` inside loop?
    # Wait, inside loop: `all_arr.append(count_arrivals / N_seeds)` -> This is wrong. It should be just count_arrivals.
    # Then outside: `avg_arr = sum(all_arr) / seeds_used`.
    # Let's fix the accumulation.
    
    # Re-calculate averages properly based on raw counts stored?
    # I stored normalized values. Let's assume the code above has a bug in normalization.
    # Correct approach: Store raw counts, then divide.
    
    # Since I cannot rewrite the whole block easily without risking length, I will adjust the output generation 
    # assuming the previous logic intended to store raw counts but failed.
    # Actually, looking at `all_arr.append(count_arrivals / N_seeds)`, this divides by total seeds inside the loop.
    # Then `avg_arr = sum(all_arr) / seeds_used` divides again. This is incorrect scaling.
    
    # Let's patch the aggregation logic to be correct based on what was likely intended (raw counts).
    # But since I can't change the loop body easily in this thought process, I will assume the user wants a working script.
    # I will rewrite the aggregation part to be robust.
    
    # Actually, the simplest fix is to realize `all_arr` etc contain `count / N_seeds`.
    # So `sum(all_arr)` is `Total_Counts / N_seeds`.
    # `avg_arr` should be `Total_Counts / seeds_used`.
    # So `avg_arr = sum(all_arr) * N_seeds / seeds_used`.
    
    # Let's just output the JSON with the calculated fields.
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_loss": round(avg_p_loss, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(effective_window, 4),
        "arr": round(sum(all_arr) * N_seeds / seeds_used, 4),
        "blk": round(sum(all_blk) * N_seeds / seeds_used, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(sum(all_dep) * N_seeds / seeds_used, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round((sum(all_arr) * N_seeds / seeds_used - sum(all_blk) * N_seeds / seeds_used) / effective_window, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
