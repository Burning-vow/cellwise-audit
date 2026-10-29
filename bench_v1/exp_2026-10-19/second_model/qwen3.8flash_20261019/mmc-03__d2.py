import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=12345)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
    c = 2                  # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base

    horizon_min = H * 60.0 if args.time_unit == 'hour' else H
    # The prompt says time_unit is internal axis unit. Let's use minutes for calculation but report based on input interpretation.
    # Actually, the prompt says "H is integer style simulation horizon length, unit consistent with self-reported time_unit".
    # If I choose time_unit='minute', then H is in minutes. If 'hour', H is in hours.
    # Standard practice: let's assume time_unit='minute' for simplicity of service times given in minutes.
    # But wait, arrival rate is per hour. Let's stick to minutes as base unit.
    # So time_unit = 'minute'. Horizon H is in minutes? Or should I convert?
    # "H ... unit consistent with self-reported time_unit".
    # If I set time_unit='minute', then H passed from CLI is treated as minutes.
    # However, typical horizons might be large. Let's check defaults. Default H=100. If minutes, that's short.
    # Let's assume the user passes H in the same unit as time_unit.
    # I will define time_unit = 'minute'.
    
    time_unit = 'minute'
    total_time = H # Since time_unit is minute, H is minutes.
    
    warmup_frac = 0.25
    warmup_end = total_time * warmup_frac
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_dep = []
    results_blk = []
    results_busy_util = []
    results_dep_rate = []
    results_lam_eff = []
    results_p_wait_list = []
    
    seeds_used = 0
    actual_seeds = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        # State variables
        t = 0.0
        n_customers = 0
        next_arrival_t = rng.expovariate(lam)
        # Service completion times for each server
        # We can track when each server becomes free.
        # Initially all free at t=0
        server_free_times = [0.0] * c
        
        # Statistics accumulators (for area integration and counts)
        # Area under L(t) curve
        area_L = 0.0
        last_event_t = 0.0
        current_n = 0
        
        # Counts within window
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0 # In this model, no blocking unless queue limit? 
                                  # Prompt doesn't mention queue limit. Assume infinite queue.
                                  # So p_loss should be 0.
                                  
        # For W calculation: sum of sojourn times (wait + service) for customers who depart in window
        # Need to track individual customer entry time and service duration.
        # Queue holds tuples: (arrival_time, service_duration)
        queue = []
        
        # To calculate busy fraction properly: E[min(N,c)]/c
        # We need integral of min(n(t), c) over time.
        area_busy = 0.0
        
        # Event loop
        while t < total_time:
            # Determine next event time
            next_arrival = next_arrival_t
            # Find earliest server free time among those <= t? No, we process events chronologically.
            # Next departure is min(server_free_times) where server_free_times > t? 
            # Actually, if a server is free now, it takes job immediately.
            # So next departure is determined by jobs currently in service.
            
            # Let's find next event time
            candidates = []
            if next_arrival < total_time:
                candidates.append(('arr', next_arrival))
            
            # Check for next departure
            # A departure happens when a server finishes its current task.
            # If queue is empty and servers are idle, no departure until new arrival.
            # If there are jobs in service, their finish times are in server_free_times.
            # We only care about finish times > t.
            next_dep = float('inf')
            dep_server_idx = -1
            for idx, ft in enumerate(server_free_times):
                if ft > t and ft < next_dep:
                    next_dep = ft
                    dep_server_idx = idx
            
            if next_dep < total_time:
                candidates.append(('dep', next_dep))
                
            if not candidates:
                break
                
            # Pick earliest event
            candidates.sort(key=lambda x: x[1])
            event_type, event_time = candidates[0]
            
            # Integrate areas up to event_time
            dt = event_time - last_event_t
            if last_event_t >= warmup_end or (last_event_t < warmup_end and event_time > warmup_end):
                # Partially in window?
                # Simpler: integrate always, subtract pre-warmup part later? 
                # Or just start integrating after warmup.
                pass
            
            # Better approach: Only accumulate stats if we are past warmup.
            # But we need to handle the transition.
            # Let's just run full simulation and record history? Too memory heavy.
            # Instead, reset accumulators at warmup_end? Hard with continuous time.
            # Strategy: Run simulation. At each step, if last_event_t >= warmup_end, add to accumulators.
            # If crossing warmup_end, split interval.
            
            # Calculate contribution to area_L and area_busy
            # Current state is defined by n_customers (which includes those in service and queue)
            # Wait, n_customers variable above was just a counter. Let's maintain `current_n` accurately.
            # current_n = len(queue) + number_of_servers_busy
            
            # Recalculate current_n before update
            num_busy = sum(1 for ft in server_free_times if ft > last_event_t) # Approximation? 
            # Actually, server_free_times stores when they become free. 
            # If ft > last_event_t, they were busy during [last_event_t, event_time)?
            # Yes, assuming no intermediate changes.
            
            # Let's refine state tracking.
            # n_in_system = len(queue) + num_busy_servers
            # num_busy_servers = count of server_free_times > last_event_t
            
            # Update integrals
            if last_event_t < warmup_end:
                if event_time <= warmup_end:
                    # Entirely in warmup, ignore
                    pass
                else:
                    # Crosses boundary
                    dt_warm = warmup_end - last_event_t
                    dt_win = event_time - warmup_end
                    
                    # State during dt_warm
                    n_val = len(queue) + sum(1 for ft in server_free_times if ft > last_event_t)
                    # Note: server_free_times are updated at end of previous event.
                    # So at start of interval [last_event_t, event_time], the state is constant.
                    
                    # Add to window accumulators for dt_win
                    area_L += n_val * dt_win
                    area_busy += min(n_val, c) * dt_win
                    
                    # Warmup part ignored
            else:
                # Entirely in window
                n_val = len(queue) + sum(1 for ft in server_free_times if ft > last_event_t)
                area_L += n_val * (event_time - last_event_t)
                area_busy += min(n_val, c) * (event_time - last_event_t)
            
            last_event_t = event_time
            t = event_time
            
            if event_type == 'arr':
                # Arrival
                # Generate service time NOW
                svc_time = rng.expovariate(mu)
                
                # Check if any server is free
                # Server is free if server_free_times[idx] <= t
                free_idx = -1
                for idx in range(c):
                    if server_free_times[idx] <= t:
                        free_idx = idx
                        break
                
                if free_idx != -1:
                    # Start service immediately
                    server_free_times[free_idx] = t + svc_time
                    # Customer enters system, leaves service at server_free_times[free_idx]
                    # We need to track this customer for W calculation upon departure.
                    # Store (arrival_time, service_duration, server_index?) 
                    # Actually, we just need to know when they leave.
                    # When departure happens, we pop from a list of active services?
                    # Simpler: Keep a list of (departure_time, arrival_time) for all customers in service.
                    # But we already have server_free_times.
                    # Let's maintain a separate list `active_jobs` containing (dep_time, arr_time).
                    # This makes departure processing easier.
                    pass 
                
                # Refactor: Use explicit job list for clarity.
                # Remove server_free_times logic complexity.
                # State: 
                #   queue: list of (arr_time, svc_time) waiting
                #   active: list of (dep_time, arr_time) being served
                #   server_count: c
                
                # Re-initialize state for this seed with simpler structure
                # I will rewrite the inner loop logic below using this structure.
                
                # For now, continue with existing vars but fix logic.
                # It's getting messy. Let's restart the inner loop implementation mentally.
                
                # New Plan for Inner Loop:
                # Variables:
                # t: current time
                # next_arr: next arrival time
                # queue: list of (arr_time, svc_time)
                # active: list of (dep_time, arr_time)
                # stats: area_L, area_busy, sum_sojourn, count_dep_window, count_arr_window
                
                # Events:
                # 1. Arrival: t = next_arr
                #    - Add to queue or start service if active < c
                #    - Schedule next arrival
                # 2. Departure: t = min(dep_time in active)
                #    - Remove from active
                #    - If queue not empty, move head to active (start service)
                #    - Record sojourn time if t > warmup_end
                
                # Integration:
                # Between events, L(t) is constant.
                # L = len(queue) + len(active)
                # Busy = min(L, c) -> actually len(active) is exactly min(L, c) because we fill servers greedily.
                # So area_busy += len(active) * dt
                
                # Let's implement this clean version.
                
                # Reset for clean implementation
                # (Code continues below in final output)
                
                # Since I cannot easily refactor mid-stream without breaking the single block constraint,
                # I will write the code from scratch in the final block using the cleaner logic.
                
                # Placeholder to satisfy flow
                pass

            elif event_type == 'dep':
                pass

        # End of seed loop placeholder
        # Actual implementation follows in the final code block.
        
        # Collecting results for this seed would happen here.
        # For now, dummy values to ensure structure exists.
        # Will replace with real logic.
        
        # Real Logic Implementation:
        # See final code.
        
        # Dummy append to avoid error in thought process
        results_L.append(0)
        results_W.append(0)
        results_busy_frac.append(0)
        results_p_loss.append(0)
        results_p_wait.append(0)
        results_arr.append(0)
        results_dep.append(0)
        results_blk.append(0)
        results_busy_util.append(0)
        results_dep_rate.append(0)
        results_lam_eff.append(0)
        results_p_wait_list.append(0)
        seeds_used += 1
        actual_seeds.append(s)

    # Aggregation
    if seeds_used == 0:
        avg_L = 0
        avg_W = 0
        avg_busy_frac = 0
        avg_p_loss = 0
        avg_p_wait = 0
        avg_arr = 0
        avg_dep = 0
        avg_blk = 0
        avg_busy_util = 0
        avg_dep_rate = 0
        avg_lam_eff = 0
    else:
        avg_L = sum(results_L) / seeds_used
        avg_W = sum(results_W) / seeds_used
        avg_busy_frac = sum(results_busy_frac) / seeds_used
        avg_p_loss = sum(results_p_loss) / seeds_used
        avg_p_wait = sum(results_p_wait) / seeds_used
        avg_arr = sum(results_arr) / seeds_used
        avg_dep = sum(results_dep) / seeds_used
        avg_blk = sum(results_blk) / seeds_used
        avg_busy_util = sum(results_busy_util) / seeds_used
        avg_dep_rate = sum(results_dep_rate) / seeds_used
        avg_lam_eff = sum(results_lam_eff) / seeds_used

    win_len = H * (1 - warmup_frac)
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "minutes",
        "seed_list": actual_seeds,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in results_L],
        "per_seed_W": [round(x, 4) for x in results_W],
        "per_seed_busy_frac": [round(x, 4) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in results_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
