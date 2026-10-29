import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=0)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    N_seeds = a.seeds
    H = a.horizon
    S_start = a.seed_start
    pert = a.pert
    
    # Parameters in hours and minutes
    # Arrival rate: 6 veh/hour -> lambda = 6 per hour
    # Service time: mean 6 min -> mu = 10 per hour (since 60/6 = 10)
    # Capacity K = 4 (including service)
    # Servers c = 3
    
    lam_base = 6.0
    mu_base = 10.0
    c = 3
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 4 # Perturbation changes structure? Prompt says "only change parameters not structure". 
              # But c is a parameter. Let's assume c increases to 4 or similar. 
              # However, standard queueing perturbations usually keep c fixed unless specified.
              # "c_up" likely means capacity or servers. Given context of toll booths, maybe servers.
              # Let's stick to changing rates for lam/mu. For c_up, let's increase servers to 4.
              # Wait, prompt says "perturbation only changes parameters not structure". 
              # If I change c from 3 to 4, is that structure? Usually yes. 
              # Maybe c_up refers to cost? No cost mentioned. 
              # Let's assume c_up increases the number of servers to 4 for this simulation run.
              # Or perhaps it increases the capacity K? 
              # Let's look at options: none/lam_up/mu_up/c_up.
              # Commonly c is server count. Let's set c=4 for c_up.
              pass
    else:
        lam = lam_base
        mu = mu_base
        
    if pert == 'c_up':
        c = 4
        # Re-evaluate if K should change? Usually K is total system capacity. 
        # If c increases, K might stay same or increase. 
        # Problem says "total can hold 4 cars". This is K. 
        # If c becomes 4, then K must be >= c. So K becomes 4? It was already 4.
        # If c=4 and K=4, no waiting room.
        pass

    # Time unit: Hour
    time_unit = "hour"
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_blk = []
    results_dep = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Events: (time, type, data)
        # type: 'A' arrival, 'D' departure
        events = []
        
        # State variables
        n_in_system = 0 # Number of cars currently in system (waiting + serving)
        busy_servers = 0 # Number of servers currently occupied
        # We need to track which servers are free? 
        # Since service times are exponential and memoryless, we just need count of busy servers.
        # But we need to know when a specific car leaves.
        # We store departure events in the event list.
        
        # Statistics accumulators (for area integration)
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * H
        stat_start_time = warmup_end
        
        # Area under curve for L (number in system)
        area_L = 0.0
        last_stat_time = stat_start_time
        
        # Counts for probabilities
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        count_waits = 0 # Cars that had to wait (arrived when all servers busy but space available)
        
        # To calculate W properly, we need sum of sojourn times for completed services within window.
        # But standard Little's Law uses average L and effective arrival rate.
        # The prompt asks for W. Usually W = L / lambda_eff.
        # Or we can compute average time directly.
        # Let's compute average time by tracking entry/exit times for cars that exit after warmup.
        # However, cars entering before warmup might exit after. 
        # Standard approach: Discard transient period. 
        # We will accumulate area for L. 
        # For W, we can use Little's Law: W = L_avg / lambda_eff_avg.
        # lambda_eff = (count_arrivals - count_blocks) / duration_window.
        # L_avg = area_L / duration_window.
        # So W = area_L / (count_arrivals - count_blocks).
        # This avoids complex bookkeeping of individual times across boundaries.
        
        # Busy fraction: proportion of time station is not empty (n_in_system > 0)
        # Note: Prompt defines busy_frac as 1 - pi_0, i.e., P(N>0).
        # busy_util is E[min(N,c)]/c.
        
        area_busy = 0.0 # Area where n_in_system > 0
        area_min_nc = 0.0 # Area where min(n_in_system, c)
        
        # Event loop
        while t < H:
            # Determine next event time
            if not events:
                # Only arrivals possible if no departures pending? 
                # Actually, if events is empty, next event is next_arrival
                t_next = next_arrival
                ev_type = 'A'
            else:
                # Peek at top of heap? We aren't using heapq, just list. 
                # Need to find min time in events and compare with next_arrival.
                # Optimization: Keep events sorted or use heap. 
                # For simplicity in small sims, linear scan or heap.
                # Let's use a simple list and sort/min each step? Too slow for large H.
                # Use heapq.
                import heapq
                # Refactor: Initialize events as heap
                pass
            
        # Restarting logic with heapq for correctness and efficiency
        
        events = []
        heapq.heappush(events, (next_arrival, 'A', None))
        
        # Reset stats for this seed
        area_L = 0.0
        area_busy = 0.0
        area_min_nc = 0.0
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        count_waits = 0
        
        last_stat_time = stat_start_time
        t = 0.0
        
        # Helper to update areas
        def update_areas(current_t, prev_t, n_sys, busy_cnt):
            nonlocal area_L, area_busy, area_min_nc
            dt = current_t - prev_t
            if dt <= 0: return
            # Only integrate if interval overlaps with [stat_start_time, H]
            start_int = max(prev_t, stat_start_time)
            end_int = min(current_t, H)
            if start_int < end_int:
                dur = end_int - start_int
                area_L += n_sys * dur
                if n_sys > 0:
                    area_busy += dur
                m = min(n_sys, c)
                area_min_nc += m * dur

        while events:
            t_ev, ev_type, data = heapq.heappop(events)
            
            if t_ev > H:
                break
                
            # Update areas up to this event time
            update_areas(t_ev, t, n_in_system, busy_servers)
            t = t_ev
            
            if ev_type == 'A':
                count_arrivals += 1
                if n_in_system < K:
                    # Accept
                    n_in_system += 1
                    if busy_servers < c:
                        # Start service immediately
                        busy_servers += 1
                        serv_time = rng.expovariate(mu)
                        heapq.heappush(events, (t + serv_time, 'D', None))
                    else:
                        # Must wait
                        count_waits += 1
                        # Car joins queue. No immediate departure event generated yet.
                        # When a server frees up, it will pick up this car.
                        # How do we handle queue? 
                        # In M/M/c/K, when a departure happens, if queue > 0, one moves to service.
                        # We don't need explicit queue objects if we just track counts.
                        # But we need to generate departure times for queued cars when they enter service.
                        # Strategy: On Departure, if n_in_system > busy_servers (meaning someone is waiting),
                        # increment busy_servers and push new departure event.
                else:
                    # Blocked
                    count_blocks += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                heapq.heappush(events, (next_arrival, 'A', None))
                
            elif ev_type == 'D':
                # A car finishes service and leaves
                count_departures += 1
                n_in_system -= 1
                busy_servers -= 1
                
                # Check if there are waiting cars
                # Waiting cars exist if n_in_system > busy_servers
                if n_in_system > busy_servers:
                    # One waiting car enters service
                    busy_servers += 1
                    serv_time = rng.expovariate(mu)
                    heapq.heappush(events, (t + serv_time, 'D', None))
                    
        # Final update for area up to H
        update_areas(H, t, n_in_system, busy_servers)
        
        # Calculate metrics for this seed
        win_len = H - stat_start_time
        if win_len <= 0:
            continue
            
        avg_L = area_L / win_len
        avg_busy_frac = area_busy / win_len
        avg_min_nc = area_min_nc / win_len
        
        # Effective arrival rate in window
        eff_arrivals = count_arrivals - count_blocks
        if eff_arrivals > 0:
            avg_W = avg_L / (eff_arrivals / win_len) # Little's Law: L = lambda_eff * W => W = L / lambda_eff
            # Alternatively W = Total Time / Count. 
            # Using Little's law on averages is consistent with area-based L.
        else:
            avg_W = 0.0
            
        p_loss = count_blocks / count_arrivals if count_arrivals > 0 else 0.0
        p_wait = count_waits / count_arrivals if count_arrivals > 0 else 0.0
        
        # Store per-seed results
        results_L.append(avg_L)
        results_W.append(avg_W)
        results_busy_frac.append(avg_busy_frac)
        results_p_loss.append(p_loss)
        results_p_wait.append(p_wait)
        results_arr.append(count_arrivals)
        results_blk.append(count_blocks)
        results_dep.append(count_departures)
        
        seeds_used += 1
        seed_list.append(seed)

    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    # Aggregate statistics
    final_L = sum(results_L) / seeds_used
    final_W = sum(results_W) / seeds_used
    final_busy_frac = sum(results_busy_frac) / seeds_used
    final_p_loss = sum(results_p_loss) / seeds_used
    final_p_wait = sum(results_p_wait) / seeds_used
    
    total_arr = sum(results_arr)
    total_blk = sum(results_blk)
    total_dep = sum(results_dep)
    
    avg_arr = total_arr / seeds_used
    avg_blk = total_blk / seeds_used
    avg_dep = total_dep / seeds_used
    
    # dep_rate: departures per hour in window
    # Total departures in window across all seeds / (seeds * window_length)
    # Or average per seed divided by window length
    win_len = H - 0.25 * H
    dep_rate = (avg_dep / win_len) if win_len > 0 else 0.0
    
    # lam_eff: effective arrival rate per hour
    lam_eff = ((avg_arr - avg_blk) / win_len) if win_len > 0 else 0.0
    
    # busy_util: E[min(N,c)]/c
    # We calculated avg_min_nc as area_min_nc/win_len which is E[min(N,c)]
    final_busy_util = (sum([area_min_nc for _ in range(1)]) / seeds_used) # Wait, I didn't store area_min_nc per seed in list.
    # Let's re-calculate or store it.
    # I'll add a list for util.
    
    # Correction: I need to store avg_min_nc per seed to average them.
    # Let's modify the loop slightly in mind, but since I can't edit previous code block easily without rewriting whole thing...
    # I will rewrite the main function completely to ensure correctness.

    # RE-WRITING MAIN FOR CLEANLINESS AND CORRECTNESS
    
    # ... (Previous imports)
    
    # Let's just output the JSON based on what I have, assuming I fix the missing util storage.
    # Actually, I must provide the full code. I will regenerate the code block below.

if __name__ == "__main__":
    main()
