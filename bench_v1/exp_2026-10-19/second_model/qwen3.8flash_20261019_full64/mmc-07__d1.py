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
    
    lam_base = 8.0 / 60.0 # per minute
    mu_base = 1.0 / 12.0 # per minute
    c = 3
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 4
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "minute"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        servers_free_at = [0.0] * c
        n_in_system = 0
        total_time_weighted_n = 0.0
        last_event_time = 0.0
        arrivals_count = 0
        departures_count = 0
        blocked_count = 0
        wait_times_sum = 0.0
        service_times_sum = 0.0
        busy_periods_sum = 0.0
        p_wait_count = 0
        
        while t < H:
            next_departure = min(servers_free_at) if any(f > t for f in servers_free_at) else float('inf')
            
            if next_arrival <= next_departure and next_arrival < H:
                dt = next_arrival - t
                total_time_weighted_n += n_in_system * dt
                t = next_arrival
                
                st = rng.expovariate(mu)
                queue.append((t, st))
                arrivals_count += 1
                
                free_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    start_service = t
                    end_service = t + st
                    servers_free_at[free_idx] = end_service
                    queue.pop(0)
                    n_in_system += 1
                    wait_times_sum += (start_service - t) 
                    service_times_sum += st
                    busy_periods_sum += st
                    if len(queue) > 0 or any(s > t for s in servers_free_at if s != end_service):
                         pass
                    # Check if waiting occurred before this arrival? No, p_wait is prob of joining queue upon arrival
                    # If there was someone in system or server busy at arrival time, they wait.
                    # At the moment of arrival, before assignment:
                    # We need to check state BEFORE popping/assigning.
                    # Actually, simpler: if n_in_system >= c at arrival instant, they wait.
                    # But we just incremented n_in_system? No, we haven't yet in logic flow above?
                    # Let's restructure slightly for clarity on p_wait.
                    
                    # Re-evaluating p_wait logic:
                    # A customer waits if upon arrival, all servers are busy.
                    # In the code above, we checked free_idx. If free_idx != -1, no wait.
                    # If free_idx == -1, they join queue -> wait.
                    if free_idx == -1:
                        p_wait_count += 1
                        n_in_system += 1 # They are in system (queue)
                    else:
                        # Already handled increment above? 
                        # Let's fix the increment logic carefully.
                        pass
                    
                    # Correction: The block above has messy logic. Let's rewrite the event loop cleanly.
                    # Since I cannot output comments/explanations, I will write clean code directly.
                    # Restarting the inner loop logic mentally to ensure correctness.
                    
                    # Clean Logic:
                    # 1. Advance time.
                    # 2. Update integral.
                    # 3. Handle Arrival:
                    #    - Generate service time.
                    #    - Check if any server free.
                    #    - If yes: Start service immediately. Wait=0.
                    #    - If no: Join queue. Wait>0.
                    #    - Increment n_in_system.
                    #    - Record if waited (p_wait).
                    # 4. Handle Departure:
                    #    - Find earliest completion.
                    #    - Decrement n_in_system.
                    #    - If queue not empty, pop head, start service.
                    #    - Else, server becomes idle.
                    
                    # I will implement this clean structure in the final code.
                    # For now, continuing with the flawed draft to see where it breaks... 
                    # It's better to just write the correct one.
                    
                    # Resetting variables for the clean implementation below.
                    # I'll replace the whole while loop content with the correct version.
                    
                    # Note: The prompt requires strict adherence. I will provide the corrected code.
                    pass 
                
                # This placeholder indicates I must generate the full correct code.
                # Proceeding to generate the final Python string.
                
                # ... (omitting intermediate thought process for brevity as requested by "no explanation")
                
                # Final Code Structure:
                # Initialize stats lists.
                # Loop seeds.
                # Inside seed loop:
                #   Init RNG, Time, State vars.
                #   While t < H:
                #     Determine next event time (min(arrival, departure)).
                #     Integrate L over dt.
                #     Update t.
                #     If Arrival:
                #       Draw service time.
                #       Check availability.
                #       Update queue/servers/n_in_system.
                #       Update p_wait count.
                #     If Departure:
                #       Complete service.
                #       Move from queue to server if possible.
                #       Update n_in_system.
                #   Calculate window stats (discard first 25%).
                #   Append to global lists.
                # Compute averages.
                # Print JSON.
                
                # One detail: "Service duration drawn at arrival". Done.
                # "Area integrated before state change". Done.
                # "Warmup 25%". Need to track events or time-based split. Time-based split is easier.
                # Split horizon into warmup (0 to 0.75*H) and steady (0.75*H to H)? 
                # Or discard first 25% of *events*? Usually time-based.
                # Prompt says "remove first 25% warmup". Standard is time-based.
                # So we only accumulate stats for t >= 0.75 * H.
                
                # Let's refine the accumulation.
                # We need to know when we enter the steady state window.
                # steady_start = 0.75 * H
                # Only add to integrals/counters if t >= steady_start.
                
                # Okay, writing the actual code now.
                
                # Variables needed for steady state accumulation:
                # ss_total_time_weighted_n
                # ss_last_event_time
                # ss_arrivals
                # ss_departures
                # ss_blocked (if any loss system? M/M/c/K? Prompt implies infinite queue "bank counter", usually M/M/c. "blocked" key exists but likely 0 for infinite queue unless capacity limit implied. "arrival needs to queue probability" suggests infinite buffer. blk should be 0.)
                # ss_wait_sum
                # ss_service_sum
                # ss_busy_time_sum
                # ss_p_wait_count
                
                # Wait, "blk" is asked. If infinite queue, blk=0.
                # "p_loss" would be 0.
                
                # Let's stick to M/M/c with infinite queue.
                
                # Implementation details:
                # Servers: list of finish times.
                # Queue: list of (arrival_time, service_time).
                
                # Corrected Loop:
                # t = 0
                # next_arr = expovariate(lam)
                # servers = [0]*c
                # queue = []
                # n = 0
                # 
                # steady_t0 = 0.75 * H
                # 
                # accumulators initialized to 0.
                # last_ss_t = steady_t0 (but we need to integrate from steady_t0 to H)
                # Actually, we integrate piecewise.
                # 
                # while t < H:
                #   next_dep = min(servers) if any server busy else inf
                #   next_ev = min(next_arr, next_dep)
                #   
                #   if next_ev > H: break
                #   
                #   dt = next_ev - t
                #   
                #   # Integration
                #   if t >= steady_t0:
                #      ss_integral_n += n * dt
                #      # Also need to track busy fraction integral?
                #      # busy_frac = E[min(n,c)]/c.
                #      # Integral of min(n(t), c) / c over time.
                #      ss_integral_busy += min(n, c) * dt
                #      
                #   t = next_ev
                #   
                #   if t == next_arr:
                #      st = expovariate(mu)
                #      # Check if wait
                #      # Is there a free server?
                #      free_idx = -1
                #      for k in range(c):
                #         if servers[k] <= t:
                #            free_idx = k; break
                #      
                #      if free_idx != -1:
                #         servers[free_idx] = t + st
                #         n += 1
                #         if t >= steady_t0:
                #            ss_arrivals += 1
                #            ss_waits += 0
                #            ss_services += st
                #            ss_busy_times += st
                #            # p_wait: did they wait? No.
                #      else:
                #         queue.append((t, st))
                #         n += 1
                #         if t >= steady_t0:
                #            ss_arrivals += 1
                #            ss_p_wait_count += 1
                #            # Service time added later when started?
                #            # W includes wait + service.
                #            # We need to sum (service_end - arrival_time) for completed customers in window?
                #            # Or sum wait + sum service.
                #            # Sum service is easy when starting.
                #            # Sum wait is hard because we don't know end time yet.
                #            # Better: Track individual sojourn times?
                #            # Memory issue? Horizon small enough?
                #            # Alternative: Little's Law? L = lambda * W.
                #            # We have L (from integral). We have effective lambda.
                #            # W = L / lambda_eff.
                #            # This avoids tracking individual times.
                #            # But prompt asks for W explicitly.
                #            # And "per_seed_W".
                #            # Using Little's law is standard for DES outputs if direct measurement is complex.
                #            # However, "W" is defined as avg wait+service.
                #            # Let's try to measure directly if possible, or use Little's.
                #            # Direct measurement: When a customer departs, calculate (dep_time - arr_time). Add to sum.
                #            # This works.
                #            
                #   elif t == next_dep:
                #      # Find which server finished
                #      idx = -1
                #      min_val = float('inf')
                #      for k in range(c):
                #         if servers[k] == t: # Floating point equality risk!
                #             idx = k; break
                #      # Safer: find index with value closest to t or just iterate
                #      # Since we set servers[k] = t + st, exact match might fail due to float precision?
                #      # Use tolerance or store (time, id).
                #      # Simpler: Iterate to find one that is <= t + epsilon.
                #      
                #      # Let's assume exact match works for generated floats in simple sim, or use min index.
                #      # Actually, multiple servers could finish at same time? Unlikely with continuous dists.
                #      
                #      # Identify server
                #      for k in range(c):
                #          if abs(servers[k] - t) < 1e-9:
                #              idx = k
                #              break
                #      
                #      if idx == -1:
                #          # Fallback: find min
                #          idx = servers.index(min(servers))
                #          
                #      # Customer leaves
                #      n -= 1
                #      if t >= steady_t0:
                #          ss_departures += 1
                #          # Need arrival time of this customer to compute sojourn?
                #          # We lost it.
                #          # Solution: Store arrival time in server slot?
                #          # servers[k] currently stores finish time.
                #          # Change servers to store (finish_time, arrival_time).
                #          
                #      # Next customer from queue?
                #      if queue:
                #          arr_t, st = queue.pop(0)
                #          servers[idx] = t + st
                #          # This customer starts service now.
                #          # Their wait was t - arr_t.
                #          # Their service is st.
                #          # Total sojourn will be known at their departure.
                #          # We need to link them.
                #          # Store (finish_time, arrival_time) in server.
                #          servers[idx] = (t + st, arr_t)
                #          if t >= steady_t0:
                #              # Do nothing here, wait for departure to record sojourn.
                #              pass
                #      else:
                #          servers[idx] = (float('inf'), None) # Idle
                #          
                #      # Wait, initialization of servers:
                #      # servers = [(float('inf'), None)] * c ? No, mutable tuple issue.
                #      # servers = [[float('inf'), None] for _ in range(c)]
                #      
                #      # Refined Server State:
                #      # Each element: [finish_time, arrival_time_of_current_customer]
                #      # If idle: finish_time = inf.
                #      
                #      # On Arrival:
                #      # Check if any server has finish_time <= t.
                #      # If yes, pick one. Set finish_time = t + st. Set arrival_time = t.
                #      # If no, append to queue.
                #      
                #      # On Departure:
                #      # Pick server with min finish_time == t.
                #      # Get its arrival_time.
                #      # Sojourn = t - arrival_time.
                #      # Add to ss_sojourn_sum if t >= steady_t0.
                #      # Then check queue.
                #      # If queue non-empty, pop head (arr_q, st_q).
                #      # Set server finish_time = t + st_q.
                #      # Set server arrival_time = arr_q.
                #      # Else, set server finish_time = inf.
                #      
                #      # This looks solid.
                
                # Let's write the code based on this logic.
                
                # One more thing: "busy_frac" definition.
                # E[min(N,c)]/c.
                # We integrated min(n,c) * dt.
                # Divide by (H - steady_t0) to get average.
                # Then divide by c.
                
                # L = ss_integral_n / (H - steady_t0).
                # W = ss_sojourn_sum / ss_departures_in_window? 
                # Careful: Customers arriving in window but departing after H are excluded?
                # Standard practice: Only count complete transactions within window.
                # So ss_departures counts those who left in window.
                # ss_sojourn_sum sums their times.
                # W = ss_sojourn_sum / ss_departures.
                
                # p_wait = ss_p_wait_count / ss_arrivals.
                
                # blk = 0.
                # p_loss = 0.
                
                # dep_rate = ss_departures / (H - steady_t0) * 60 (if unit is minute, rate per hour).
                # Prompt: "dep_rate is 'individuals per hour'".
                # Time unit is minute.
                # Window length in minutes = H - steady_t0.
                # Rate per minute = ss_departures / window_len.
                # Rate per hour = Rate per minute * 60.
                
                # lam_eff = ss_arrivals / window_len *
