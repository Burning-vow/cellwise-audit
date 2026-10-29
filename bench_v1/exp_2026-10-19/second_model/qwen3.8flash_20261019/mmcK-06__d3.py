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
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 10.0 # 6 min mean -> 1/0.1 hr
    c = 3
    K = 4 # capacity including service
    
    if pert == 'lam_up': lam = lam_base * 1.2
    elif pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif pert == 'c_up': c = 4; K = 5; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    win = H - 0.25 * H # Remove first 25% as warmup
    if win <= 0: win = H
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_blk = []
    per_seed_dep = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        num_in_system = 0
        servers_free = c
        
        # Accumulators for statistics (only after warmup)
        L_area = 0.0
        busy_time = 0.0
        wait_time_sum = 0.0
        arrivals_count = 0
        blocked_count = 0
        departures_count = 0
        waiting_customers_count = 0 # For p_wait calculation? No, p_wait usually prob of waiting upon arrival or fraction of time someone waits. 
        # Standard definition: P(wait) is probability an arriving customer has to wait.
        # We need to track how many arrived and had to wait vs total accepted.
        # Or simply: Fraction of time system is full? No, that's blocking.
        # Let's define p_wait as the probability that an arriving customer finds all servers busy (and thus waits).
        # Note: If system is full, they are blocked. Do we count them in denominator? Usually yes for loss systems, but here it's mixed.
        # Common metric: P(W>0) among those who enter.
        
        customers_in_queue = 0
        # To calculate W properly, we need to know when a customer started service.
        # Since service times are exponential and memoryless, we can just track completion times.
        # But we need individual wait times.
        # Approach: When a customer arrives, if server free, start immediately. Else join queue.
        # We need to store arrival time of queued customers to compute wait time when they start service.
        queue_arrival_times = []
        
        # Warmup threshold
        warmup_end = 0.25 * H
        
        while t < H:
            # Determine next event
            if next_arrival < next_departure:
                t_event = next_arrival
                event_type = 'arrival'
            else:
                t_event = next_departure
                event_type = 'departure'
            
            # Integrate area before updating state
            dt = t_event - t
            if t >= warmup_end:
                L_area += num_in_system * dt
                if num_in_system > 0:
                    busy_time += dt
            
            t = t_event
            
            if event_type == 'arrival':
                if t >= warmup_end:
                    arrivals_count += 1
                
                if num_in_system < K:
                    num_in_system += 1
                    if servers_free > 0:
                        servers_free -= 1
                        # Start service immediately
                        dur = rng.expovariate(mu)
                        # Schedule departure
                        # Need to manage multiple departures. Use a heap or list.
                        # Since only 3 servers, simple list is fine.
                        # We'll push (time, id) to a departure list.
                        # Actually, let's maintain a list of active service end times.
                        # But we already have next_departure variable. This logic needs refinement for multi-server.
                        
                        # Re-evaluating simulation loop structure for multi-server.
                        # Better approach: Event list priority queue.
                        pass
                    else:
                        # Join queue
                        queue_arrival_times.append(t)
                        if t >= warmup_end:
                            waiting_customers_count += 1 # Count arrivals that waited
                else:
                    if t >= warmup_end:
                        blocked_count += 1
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'departure':
                # One customer leaves
                num_in_system -= 1
                if t >= warmup_end:
                    departures_count += 1
                
                # Check if queue exists
                if queue_arrival_times:
                    # Next customer starts service
                    arr_t = queue_arrival_times.pop(0)
                    wait_dur = t - arr_t
                    if t >= warmup_end:
                        wait_time_sum += wait_dur
                    
                    # New service duration
                    dur = rng.expovariate(mu)
                    new_dep_t = t + dur
                    # Update next_departure
                    # We need to handle multiple concurrent services.
                    # The previous logic with single next_departure is flawed for c>1.
                    # Must use a heap.
                    pass
                else:
                    servers_free += 1
                
                # Recalculate next_departure from remaining active services
                # This requires maintaining a set of active service end times.
                # Let's restart the inner loop logic with a proper heap.
                break # Break to rewrite logic below

        # --- RESTARTING SIMULATION LOGIC WITH HEAP ---
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Heap of (departure_time, customer_id_or_dummy)
        import heapq
        dep_heap = []
        num_in_system = 0
        servers_free = c
        queue_arrival_times = []
        
        L_area = 0.0
        busy_time = 0.0
        wait_time_sum = 0.0
        arrivals_count = 0
        blocked_count = 0
        departures_count = 0
        waiting_arrivals_count = 0
        
        warmup_end = 0.25 * H
        
        while t < H:
            # Get next event time
            next_dep = dep_heap[0][0] if dep_heap else float('inf')
            
            if next_arrival < next_dep:
                t_event = next_arrival
                event_type = 'arrival'
            else:
                t_event = next_dep
                event_type = 'departure'
            
            dt = t_event - t
            if t >= warmup_end:
                L_area += num_in_system * dt
                if num_in_system > 0:
                    busy_time += dt
            
            t = t_event
            
            if event_type == 'arrival':
                if t >= warmup_end:
                    arrivals_count += 1
                
                if num_in_system < K:
                    num_in_system += 1
                    if servers_free > 0:
                        servers_free -= 1
                        dur = rng.expovariate(mu)
                        heapq.heappush(dep_heap, (t + dur, 0))
                    else:
                        queue_arrival_times.append(t)
                        if t >= warmup_end:
                            waiting_arrivals_count += 1
                else:
                    if t >= warmup_end:
                        blocked_count += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'departure':
                heapq.heappop(dep_heap)
                num_in_system -= 1
                if t >= warmup_end:
                    departures_count += 1
                
                if queue_arrival_times:
                    arr_t = queue_arrival_times.pop(0)
                    w = t - arr_t
                    if t >= warmup_end:
                        wait_time_sum += w
                    dur = rng.expovariate(mu)
                    heapq.heappush(dep_heap, (t + dur, 0))
                else:
                    servers_free += 1
        
        # Calculate stats for this seed
        if win > 0:
            avg_L = L_area / win
            avg_busy_frac = busy_time / win
            avg_W = wait_time_sum / departures_count if departures_count > 0 else 0.0
            p_loss = blocked_count / arrivals_count if arrivals_count > 0 else 0.0
            p_wait = waiting_arrivals_count / arrivals_count if arrivals_count > 0 else 0.0
            
            per_seed_L.append(avg_L)
            per_seed_W.append(avg_W)
            per_seed_busy_frac.append(avg_busy_frac)
            per_seed_p_loss.append(p_loss)
            per_seed_p_wait.append(p_wait)
            per_seed_arr.append(arrivals_count)
            per_seed_blk.append(blocked_count)
            per_seed_dep.append(departures_count)
        else:
            per_seed_L.append(0.0)
            per_seed_W.append(0.0)
            per_seed_busy_frac.append(0.0)
            per_seed_p_loss.append(0.0)
            per_seed_p_wait.append(0.0)
            per_seed_arr.append(0)
            per_seed_blk.append(0)
            per_seed_dep.append(0)

    # Aggregate results
    seeds_used = len(per_seed_L)
    if seeds_used == 0:
        print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_loss":0,"runtime_units":"hour","seed_list":[],"seeds_used":0,"time_unit":"hour","win":0,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_wait":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[],"busy_occupied":0}))
        return

    mean_L = sum(per_seed_L) / seeds_used
    mean_W = sum(per_seed_W) / seeds_used
    mean_busy_frac = sum(per_seed_busy_frac) / seeds_used
    mean_p_loss = sum(per_seed_p_loss) / seeds_used
    mean_p_wait = sum(per_seed_p_wait) / seeds_used
    
    total_arr = sum(per_seed_arr)
    total_blk = sum(per_seed_blk)
    total_dep = sum(per_seed_dep)
    
    mean_arr = total_arr / seeds_used
    mean_blk = total_blk / seeds_used
    mean_dep = total_dep / seeds_used
    
    # busy_util = E[min(N,c)]/c
    # Approximate by average number in service / c
    # Number in service = min(num_in_system, c)
    # We didn't track integral of min(N,c). 
    # However, busy_frac (1-pi0) is given. 
    # busy_util is typically utilization per server.
    # In M/M/c/K, utilization rho = lambda_eff / (c*mu).
    # Let's estimate busy_util via Little's Law on service part? 
    # Or simply: Average number in service = Total Service Time / Window.
    # We tracked busy_time (time at least one server busy). Not sum of server busy times.
    # Correction: busy_time accumulated dt if num_in_system > 0. This is time system non-empty.
    # To get busy_util, we need sum of server busy times.
    # Let's re-run quickly? No, code length constraint.
    # Alternative: busy_util approx = (mean_L - mean_queue_length)/c? Hard.
    # Let's assume standard definition: busy_util = lambda_eff / (c * mu).
    lam_eff = mean_dep / win if win > 0 else 0
    busy_util = lam_eff / (c * mu) if c * mu > 0 else 0
    
    dep_rate = mean_dep / win * 1.0 # Per hour since time_unit is hour
    
    result = {
        "L": round(mean_L, 4),
        "W": round(mean_W * 60, 4), # Convert hours to minutes
        "busy_frac": round(mean_busy_frac, 4),
        "p_loss": round(mean_p_loss, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win, 4),
        "arr": round(mean_arr, 4),
        "blk": round(mean_blk, 4),
        "busy_util": round(busy_util, 4),
        "dep": round(mean_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_wait": round(mean_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait],
        "busy_occupied": round(mean_busy_frac, 4)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
