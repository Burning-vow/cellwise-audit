import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    lam_h = 6.0
    mu_min = 5.0
    if a.pert == "lam_up": lam_h *= 1.1
    elif a.pert == "mu_up": mu_min /= 1.1
    
    time_unit = "minute"
    horizon = a.horizon * 60.0 if time_unit == "minute" else a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
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
    total_wait_time = 0.0
    total_busy_time = 0.0
    total_window_len = 0.0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_h / 60.0)
        queue = []
        service_end = float('inf')
        is_busy = False
        
        # For area integration of L and busy fraction
        last_event_t = 0.0
        current_N = 0
        area_L = 0.0
        area_busy = 0.0
        
        # For waiting probability: count customers who waited (arrival found server busy or queue non-empty)
        # But standard definition: P(wait) = prob that an arriving customer has to wait.
        # In M/M/1, this is rho. We estimate by counting arrivals where system was not empty.
        n_arrivals_in_win = 0
        n_waits_in_win = 0
        n_losses_in_win = 0 # M/M/1 infinite buffer, so 0 losses usually, but we track if any logic implies it. Here no blocking.
        
        # Store arrival times and service durations for those who arrive before horizon
        # To compute W accurately over the window, we need departure times of customers who arrived in window?
        # Or all customers who departed in window?
        # Standard simulation output analysis: 
        # L = integral N(t) dt / T
        # W = sum(time in system for customers who completed during window) / number of such customers?
        # Better: Little's Law consistency. 
        # Let's track each customer: arrival time, service start time, departure time.
        # We only care about statistics in [win_start, horizon].
        
        events = [] # Not using event list, just loop
        
        # We need to handle the fact that some customers arrive before win_start and depart after.
        # Their time in system contributes to W if they depart in window? 
        # Usually W is average time in system for customers served in the steady state.
        # A common approach: collect all customers who DEPARTED in the window.
        # Another: collect all customers who ARRIVED in the window and eventually departed.
        # Given the prompt asks for "average stay time W", and "area type quantities must be integrated before changing state",
        # L is clearly area-based. W is often calculated as sum(T_i)/N_departed or similar.
        # Let's use: Sum of time in system for all customers who DEPARTED within the window divided by count of such departures.
        # This aligns with dep_rate.
        
        # Data structures to hold active customers
        # Each customer: dict(arr_t, svc_dur, start_t=None, end_t=None)
        active_customers = [] 
        
        while t < horizon:
            # Determine next event
            arr_t = next_arr
            dep_t = service_end if is_busy else float('inf')
            
            if arr_t <= dep_t:
                # Arrival
                t_next = arr_t
                # Integrate areas up to t_next
                dt = t_next - last_event_t
                if last_event_t >= win_start:
                    area_L += current_N * dt
                    if is_busy: area_busy += dt
                
                # Process arrival
                # Check if we are past warmup for counting stats? 
                # The prompt says "statistics only accumulated in window after removing first 25% warmup".
                # So we only record data for events happening in [win_start, horizon].
                
                # Generate service duration NOW
                svc_dur = rng.expovariate(1.0 / mu_min)
                cust = {"arr": t_next, "svc": svc_dur, "start": None, "end": None}
                
                if is_busy:
                    queue.append(cust)
                    # Customer waits
                    if t_next >= win_start:
                        n_arrivals_in_win += 1
                        n_waits_in_win += 1 # Server busy means wait
                else:
                    is_busy = True
                    service_end = t_next + svc_dur
                    cust["start"] = t_next
                    cust["end"] = service_end
                    active_customers.append(cust)
                    if t_next >= win_start:
                        n_arrivals_in_win += 1
                        # No wait if server idle
                
                current_N += 1
                last_event_t = t_next
                t = t_next
                next_arr = t + rng.expovariate(lam_h / 60.0)
                
            else:
                # Departure
                t_next = dep_t
                dt = t_next - last_event_t
                if last_event_t >= win_start:
                    area_L += current_N * dt
                    if is_busy: area_busy += dt
                
                # Process departure
                # Find the customer who finishes
                # Since we only have one server, the one at front of processing is the one finishing.
                # We stored the active customer in active_customers when it started.
                # Actually, simpler: maintain a pointer or pop from a list of currently served.
                # Let's restructure slightly: keep 'current_cust' being served.
                pass 

        # The above loop structure is getting messy for tracking specific customers for W.
        # Let's restart the inner loop logic with a cleaner state machine.
        
        # Reset variables for this seed
        t = 0.0
        next_arr = rng.expovariate(lam_h / 60.0)
        queue = []
        current_cust = None # Dict with arr, svc, start, end
        is_busy = False
        last_event_t = 0.0
        current_N = 0
        area_L = 0.0
        area_busy = 0.0
        
        # Lists to store completion info for customers departing in window
        # We can't easily know if they depart in window until they do.
        # So we process events. If a departure happens in window, we add its time-in-system to sum.
        sum_time_in_sys = 0.0
        count_departures = 0
        count_arrivals = 0
        count_waits = 0
        
        while t < horizon:
            arr_t = next_arr
            dep_t = current_cust["end"] if current_cust else float('inf')
            
            if arr_t <= dep_t:
                t_next = arr_t
                dt = t_next - last_event_t
                if last_event_t >= win_start:
                    area_L += current_N * dt
                    if is_busy: area_busy += dt
                
                svc_dur = rng.expovariate(1.0 / mu_min)
                new_cust = {"arr": t_next, "svc": svc_dur, "start": None, "end": None}
                
                if is_busy:
                    queue.append(new_cust)
                    if t_next >= win_start:
                        count_arrivals += 1
                        count_waits += 1
                else:
                    is_busy = True
                    new_cust["start"] = t_next
                    new_cust["end"] = t_next + svc_dur
                    current_cust = new_cust
                    if t_next >= win_start:
                        count_arrivals += 1
                
                current_N += 1
                last_event_t = t_next
                t = t_next
                next_arr = t + rng.expovariate(lam_h / 60.0)
            else:
                t_next = dep_t
                dt = t_next - last_event_t
                if last_event_t >= win_start:
                    area_L += current_N * dt
                    if is_busy: area_busy += dt
                
                # Departure
                if t_next >= win_start:
                    time_in_sys = current_cust["end"] - current_cust["arr"]
                    sum_time_in_sys += time_in_sys
                    count_departures += 1
                
                current_N -= 1
                is_busy = False
                current_cust = None
                
                if queue:
                    next_cust = queue.pop(0)
                    is_busy = True
                    next_cust["start"] = t_next
                    next_cust["end"] = t_next + next_cust["svc"]
                    current_cust = next_cust
                    # Note: The arrival of this queued customer was already counted in count_arrivals/waits earlier.
                    # Its departure will be counted later.
                
                last_event_t = t_next
                t = t_next
        
        # Final integration step if needed? Loop ends at horizon.
        # The last interval was handled in the last event iteration.
        
        window_len = horizon - win_start
        if window_len > 0:
            L_est = area_L / window_len
            busy_est = area_busy / window_len
            W_est = sum_time_in_sys / count_departures if count_departures > 0 else 0.0
            p_wait_est = count_waits / count_arrivals if count_arrivals > 0 else 0.0
            p_loss_est = 0.0 # Infinite buffer
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(busy_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            
            total_arr += count_arrivals
            total_dep += count_departures
            total_blk += 0
            total_time_in_sys += sum_time_in_sys
            total_wait_time += 0 # Not used directly
            total_busy_time += area_busy
            total_window_len += window_len
            seeds_used.append(seed)

    num_seeds = len(seeds_used)
    if num_seeds == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum(per_seed_L) / num_seeds
    avg_W = sum(per_seed_W) / num_seeds
    avg_busy = sum(per_seed_busy_frac) / num_seeds
    avg_p_loss = sum(per_seed_p_loss) / num_seeds
    avg_p_wait = sum(per_seed_p_wait) / num_seeds
    
    avg_arr_per_seed = total_arr / num_seeds
    avg_dep_per_seed = total_dep / num_seeds
    avg_blk_per_seed = total_blk / num_seeds
    
    # dep_rate in per hour
    # Total departures across all seeds / Total time across all seeds (in hours)
    total_time_hours = (total_window_len / 60.0) * num_seeds # Wait, window_len is same for all seeds? Yes.
    # Actually, total_window_len accumulated is num_seeds * single_window_len.
    # So total time simulated in window = total_window_len minutes.
    # Convert to hours: total_window_len / 60.0
    dep_rate = avg_dep_per_seed / (total_window_len / num_seeds / 60.0) if total_window_len > 0 else 0.0
    
    lam_eff = avg_arr_per_seed / (total_window_len / num_seeds / 60.0) if total_window_len > 0 else 0.0
    
    # busy_util = E[min(N,c)]/c. c=1. E[N] approx L. So L/1.
    busy_util = avg_L
    # busy_occupied = 1 - pi_0. pi_0 is prob system empty. 
    # In steady state M/M/1, pi_0 = 1-rho. Busy frac = rho.
    # Our busy_est is fraction of time busy. So busy_occupied = busy_est.
    busy_occupied = avg_busy
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "minutes",
        "seed_list": seeds_used,
        "seeds_used": num_seeds,
        "time_unit": "minute",
        "win": round(total_window_len / num_seeds, 6),
        "arr": round(avg_arr_per_seed, 6),
        "blk": round(avg_blk_per_seed, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep_per_seed, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
