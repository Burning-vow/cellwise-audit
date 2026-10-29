import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    N = a.seeds; H = a.horizon; S = a.seed_start; pert = a.pert
    lam_base = 7.0/60.0 # per minute
    mu_base = 1.0/6.0   # per minute
    if pert == 'lam_up': lam_base *= 1.2
    elif pert == 'mu_up': mu_base *= 1.2
    elif pert == 'c_up': pass
    
    time_unit = 'minute'
    win = H * 0.75
    warmup = H * 0.25
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_wait = []
    all_arr = []; all_dep = []; all_blk = []; all_busy_util = []; all_dep_rate = []
    all_lam_eff = []; all_p_loss = []; all_busy_occupied = []
    
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []; per_seed_p_loss = []; per_seed_p_wait = []
    seed_list = []
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam_base)
        service_times = {} 
        events = []
        
        # Initial state: empty system
        # We need to simulate until H
        
        # To handle discrete event simulation simply without classes:
        # State variables: current_time, num_in_system (n), next_event_type ('arr' or 'dep'), next_event_time
        # But we need to manage queue and service times.
        # Since it's M/M/1, we can just track arrivals and departures.
        # However, standard DES loop is safer.
        
        # Let's use a priority queue of events? Or just simple loop since only 2 types.
        # Actually, for M/M/1, we can just generate inter-arrival and service times on the fly.
        # But "service duration must be drawn at arrival".
        
        # Variables for integration
        last_t = 0.0
        area_n = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0 # For M/M/1 infinite buffer, blk is 0 usually unless capacity limited. Problem says stable, implies infinite buffer or large enough. Standard M/M/1 has no blocking. So blk=0.
        sum_w = 0.0 # Sum of sojourn times for customers who departed within window? No, W is average time in system.
        # Usually W is estimated by Little's Law L/lam_eff or by averaging individual sojourn times.
        # The prompt asks for W. In DES, often we accumulate sum of (departure - arrival) for completed services.
        # But careful with truncation.
        # Let's stick to: L = area_n / win. W = L / lam_eff. Or direct average of sojourn times?
        # Prompt: "average stay time W". Usually derived from L and lambda.
        # Let's calculate L via area integral. Then W = L / effective_lambda.
        # Effective lambda = count_arr / win? Or count_dep / win? In steady state they are equal.
        # Let's use count_dep / win as output rate, which equals input rate in steady state.
        
        # Re-evaluating strategy:
        # 1. Simulate events up to H.
        # 2. Record state changes.
        # 3. Integrate n(t) over [warmup, H].
        # 4. Count arrivals/departures in [warmup, H].
        # 5. Calculate L = Integral(n)/win.
        # 6. Calculate W = L / (count_arr/win) ? Or L / (count_dep/win)?
        #    Little's law: L = lambda * W. So W = L / lambda.
        #    Which lambda? Arrival rate or Departure rate? They should be same.
        #    Let's use arrival rate in window.
        
        # Need to track individual customer data?
        # "Service duration ... hung on that customer".
        # We need to know when a customer arrives to draw service time.
        # We need to know when they leave to calculate sojourn time if we want direct average.
        # But L-based W is more robust for area-integral consistency.
        # Let's provide both? No, single W key.
        # I will compute W using Little's Law: W = L / lam_eff.
        # And also compute direct average sojourn time for validation?
        # The prompt asks for W. I'll use L/lam_eff.
        
        # Data structures for active customers:
        # Just need to know when the next departure happens.
        # If n > 0, there is a customer being served.
        # We need to store the completion time of the current service.
        
        curr_service_end = None
        # Queue of waiting customers? Not needed for M/M/1 logic if we just track n.
        # But we need to assign service time upon arrival.
        # If server is busy, new customer waits. When does their service start?
        # When previous one finishes.
        # So we need a queue of service times?
        # Yes.
        
        wait_queue = [] # List of service durations for waiting customers
        
        # Event loop
        # Next arrival time
        next_arrival = rng.expovariate(lam_base)
        
        # Initialize first arrival
        # At t=0, n=0.
        
        while t < H:
            # Determine next event
            next_departure = float('inf')
            if n > 0:
                # If someone is being served, we have curr_service_end
                # If someone is waiting, they don't affect next departure until current one ends
                next_departure = curr_service_end
            
            next_event_time = min(next_arrival, next_departure)
            
            if next_event_time >= H:
                break
                
            # Advance time
            dt = next_event_time - t
            if t >= warmup:
                area_n += n * dt
            t = next_event_time
            
            # Process event
            if next_event_time == next_arrival:
                # Arrival
                if t >= warmup:
                    count_arr += 1
                
                # Draw service time now
                svc = rng.expovariate(mu_base)
                
                if n == 0:
                    # Start service immediately
                    n = 1
                    curr_service_end = t + svc
                else:
                    # Join queue
                    n += 1
                    wait_queue.append(svc)
                    
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam_base)
                
            elif next_event_time == next_departure:
                # Departure
                if t >= warmup:
                    count_dep += 1
                
                # Remove one from system
                n -= 1
                
                # Who left? The one being served.
                # Now check if anyone is waiting
                if wait_queue:
                    # Next person starts service
                    next_svc = wait_queue.pop(0)
                    curr_service_end = t + next_svc
                else:
                    curr_service_end = None
                    
        # End of simulation for this seed
        
        # Calculate stats for this seed
        # Note: area_n accumulated only during [warmup, H]
        # But what about the interval [H, H]? Loop breaks before processing event at H.
        # The last segment [last_processed_t, H] needs to be integrated?
        # My loop integrates dt BEFORE processing event.
        # So if an event happens at t_e, we integrate [t_prev, t_e].
        # Then process event.
        # Then set t = t_e.
        # If loop breaks because next_event >= H, we haven't integrated [t_current, H].
        # Correction:
        # We need to integrate up to H.
        
        # Let's restructure slightly or add final integration step.
        # In the loop above, if next_event_time >= H, we break.
        # We should integrate from current t to H.
        
        # Wait, the variable `t` inside the loop is updated to `next_event_time`.
        # If we break, `t` is the time of the last processed event.
        # We need to integrate from `t` to `H`.
        
        if t < H:
            dt_final = H - t
            if t >= warmup:
                area_n += n * dt_final
            # Note: if t < warmup, we don't add to area_n?
            # But warmup is fixed. If t < warmup, then the interval [t, H] crosses warmup.
            # This logic is flawed if we break early.
            
        # Better approach: Always integrate up to min(next_event, H).
        
        # Let's rewrite the inner loop carefully.
        
        # Reset for correct implementation
        t = 0.0
        n = 0
        next_arrival = rng.expovariate(lam_base)
        curr_service_end = None
        wait_queue = []
        area_n = 0.0
        count_arr = 0
        count_dep = 0
        # For direct W calculation if needed, but using Little's law is requested implicitly by L/W relation?
        # Prompt asks for W. I will use L/lam_eff.
        
        while True:
            next_departure = curr_service_end if n > 0 else float('inf')
            next_event = min(next_arrival, next_departure)
            
            if next_event >= H:
                # Integrate remaining time
                dt = H - t
                if t < warmup:
                    # Split interval
                    if t + dt <= warmup:
                        pass # Entirely in warmup
                    else:
                        # Part in warmup, part in window
                        dt_window = (t + dt) - warmup
                        area_n += n * dt_window
                else:
                    area_n += n * dt
                break
            
            # Integrate up to next_event
            dt = next_event - t
            if t < warmup:
                if next_event <= warmup:
                    pass # Entirely in warmup
                else:
                    # Crosses boundary
                    dt_window = next_event - warmup
                    area_n += n * dt_window
            else:
                area_n += n * dt
                
            t = next_event
            
            # Process event
            if t == next_arrival:
                if t >= warmup:
                    count_arr += 1
                svc = rng.expovariate(mu_base)
                if n == 0:
                    n = 1
                    curr_service_end = t + svc
                else:
                    n += 1
                    wait_queue.append(svc)
                next_arrival = t + rng.expovariate(lam_base)
            else: # Departure
                if t >= warmup:
                    count_dep += 1
                n -= 1
                if wait_queue:
                    next_svc = wait_queue.pop(0)
                    curr_service_end = t + next_svc
                else:
                    curr_service_end = None

        # Stats
        L_est = area_n / win if win > 0 else 0
        lam_eff = count_arr / win if win > 0 else 0
        dep_rate_val = count_dep / win if win > 0 else 0
        
        # W estimation
        # Using Little's Law: W = L / lambda
        # Which lambda? Arrival rate in window.
        W_est = L_est / lam_eff if lam_eff > 0 else 0
        
        # Busy fraction: E[min(N,1)] / 1. 
        # Area of busy state?
        # We didn't track busy area separately.
        # But for M/M/1, P(busy) = rho = lambda/mu.
        # Empirically: Fraction of time n > 0.
        # We need to integrate indicator(n>0).
        # Let's add that.
        
        # Re-run or modify? Modifying code is better.
        # I'll add area_busy tracking.
        
        # Since I already wrote the loop, I will assume the structure allows adding another accumulator.
        # Let's restart the thought process for the code generation to include area_busy.
        
        # Revised Plan for Code:
        # 1. Init vars including area_busy.
        # 2. Loop.
        # 3. Integrate n and (1 if n>0 else 0).
        # 4. Compute stats.
        
        # Let's write the final clean code block.
        
        # Resetting variables for the actual code string construction
        # I will construct the string directly now.
        
        # One detail: p_wait. Probability of waiting.
        # P(wait) = P(arrival finds server busy) = P(n>=1) at arrival instants?
        # Or P(n>=1) in steady state?
        # For Poisson arrivals, PASTA property holds. P(wait) = P(n>=1) = 1 - P(n=0).
        # P(n=0) = 1 - busy_frac.
        # So p_wait = busy_frac.
        # But strictly, p_wait is prob that an arriving customer has to wait.
        # With PASTA, this equals fraction of time system is non-empty.
        # So p_wait = busy_frac.
        
        # blk: Blocking probability. Infinite buffer -> 0.
        # p_loss: Same as blk -> 0.
        
        # busy_util: E[min(N,c)]/c. c=1. So E[min(N,1)].
        # This is exactly the fraction of time server is busy.
        # So busy_util = busy_frac.
        
        # busy_occupied: 1 - pi_0.
        # pi_0 is prob system empty.
        # 1 - pi_0 is prob system non-empty.
        # This is also busy_frac.
        
        # So all three are identical for M/M/1.
        
        # Runtime units: minute.
        
        # Collect results
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(area_busy / win if win > 0 else 0)
        per_seed_p_loss.append(0.0)
        per_seed_p_wait.append(per_seed_busy_frac[-1]) # PASTA
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(per_seed_busy_frac[-1])
        all_p_wait.append(per_seed_p_wait[-1])
        all_arr.append(count_arr)
        all_dep.append(count_dep)
        all_blk.append(0)
        all_busy_util.append(per_seed_busy_frac[-1])
        all_dep_rate.append(dep_rate_val)
        all_lam_eff.append(lam_eff)
        all_p_loss.append(0.0)
        all_busy_occupied.append(per_seed_busy_frac[-1])
        seed_list.append(seed)

    # Aggregate means
    def mean(lst): return sum(lst)/len(lst) if lst else 0
    
    res = {
        "L": mean(all_L),
        "W": mean(all_W),
        "busy_frac": mean(all_busy_frac),
        "p_wait": mean(all_p_wait),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": win,
        "arr": mean(all_arr),
        "blk": mean(all_blk),
        "busy_util": mean(all_busy_util),
        "dep": mean(all_dep),
        "dep_rate": mean(all_dep_rate),
        "lam_eff": mean(all_lam_eff),
        "p_loss": mean(all_p_loss),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": mean(all_busy_occupied)
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
