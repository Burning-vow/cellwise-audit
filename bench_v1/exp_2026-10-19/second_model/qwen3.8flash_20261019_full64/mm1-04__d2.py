import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    lam_base = 6.0 / 60.0  # per minute
    mu_base = 1.0 / 5.0    # per minute
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.1
    elif args.pert == 'mu_up':
        mu = mu_base * 1.1
    elif args.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    horizon_min = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
    seeds_used = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        server_free_time = 0.0
        num_in_system = 0
        total_time_in_system = 0.0
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        busy_time_integral = 0.0
        last_event_time = 0.0
        prev_num_in_system = 0
        prev_server_busy = False
        area_L = 0.0
        area_busy = 0.0
        wait_count = 0
        loss_count = 0
        dep_count = 0
        arr_count = 0
        
        while t < horizon_min:
            # Determine next event time
            next_dep = None
            if queue or server_free_time > t:
                if server_free_time > t and not queue:
                    next_dep = server_free_time
                elif queue:
                    next_dep = min(server_free_time, t + service_times.get(queue[0], float('inf'))) if queue else server_free_time
                    # Actually, if there's a queue, the next departure is when current service ends
                    # But we need to track who is being served. Let's simplify state.
            
            # Better approach: track events explicitly
            # State: t, next_arrival, list of customers in system with their arrival times and service durations
            # We'll use a priority queue simulation via sorted list of events
            
            # Reset approach: discrete event simulation with heap-like logic using simple lists since c=1
            pass
        
        # Redo with cleaner DES
        t = 0.0
        next_arr = rng.expovariate(lam)
        # For M/M/1 with single server:
        # Events: arrival, departure
        # Track: number in system, whether server is busy, queue length
        n_sys = 0
        server_busy = False
        queue_len = 0
        # To compute W, we need sum of sojourn times / number of completions in window
        # To compute L, we need time-average of n_sys
        
        # Pre-generate service times at arrival
        # We'll store (arrival_time, service_duration) for each customer
        
        # Instead, let's simulate step by step
        # List of active customers: (arrival_time, service_duration, start_service_time)
        # But for M/M/1 FCFS, we can just track queue
        
        # Simpler: maintain a list of customers waiting/served
        # Each customer has arrival_time and service_duration (drawn at arrival)
        
        customers = []  # list of dicts: {'arr': t, 'svc': duration}
        # Server state: free_at time
        server_free_at = 0.0
        
        # Statistics accumulators for the window [warmup_end, horizon_min]
        # We need to integrate over time within the window
        
        # Let's restart with a more standard DES loop
        t = 0.0
        next_arr = rng.expovariate(lam)
        # Queue as list of (arrival_time, service_duration)
        q = []
        server_free_at = 0.0
        n_in_sys = 0
        
        # For integration, we track previous state and time
        prev_t = 0.0
        prev_n = 0
        prev_busy = False
        
        # Accumulators for window stats
        int_L = 0.0
        int_busy = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_sojourn_win = 0.0
        count_wait_win = 0
        count_loss_win = 0
        
        # We also need overall counts for per-seed reporting
        total_arr = 0
        total_dep = 0
        total_blk = 0
        
        while t < horizon_min:
            # Find next event
            next_dep = None
            if q:
                # Next departure is when current service finishes
                # The first in queue is being served if server was busy
                # Actually, let's define: if server_free_at > t, then next dep is server_free_at
                # If server_free_at <= t and q non-empty, then a new service starts immediately? 
                # No, we process events chronologically.
                
                # Let's determine next event time
                candidates = []
                if next_arr < horizon_min:
                    candidates.append(('arr', next_arr))
                if server_free_at > t and server_free_at < horizon_min:
                    candidates.append(('dep', server_free_at))
                elif q and server_free_at <= t:
                    # This shouldn't happen if we handle correctly; if q non-empty and server free, 
                    # it means we just had a departure and should have started next service.
                    # So server_free_at should be updated upon departure.
                    pass
                
                if not candidates:
                    break
                    
                evt_type, evt_time = min(candidates, key=lambda x: x[1])
            else:
                if next_arr >= horizon_min:
                    break
                evt_type, evt_time = ('arr', next_arr)
            
            # Integrate from prev_t to evt_time
            dt = evt_time - prev_t
            if prev_t < warmup_end and evt_time > warmup_end:
                # Split interval
                dt_pre = warmup_end - prev_t
                dt_post = evt_time - warmup_end
                if dt_pre > 0:
                    # Before window, no accumulation needed for window stats
                    pass
                if dt_post > 0:
                    int_L += prev_n * dt_post
                    if prev_busy:
                        int_busy += dt_post
            elif prev_t >= warmup_end:
                int_L += prev_n * dt
                if prev_busy:
                    int_busy += dt
            
            prev_t = evt_time
            t = evt_time
            
            if evt_type == 'arr':
                # Draw service time now
                svc = rng.expovariate(mu)
                # Add to queue
                q.append((t, svc))
                n_in_sys += 1
                total_arr += 1
                if t >= warmup_end:
                    count_arr_win += 1
                
                # Check if server is free
                if server_free_at <= t:
                    # Start service immediately
                    server_free_at = t + svc
                    prev_busy = True
                    # Remove from queue head? No, we keep queue but mark that first is being served
                    # Actually, let's say q contains waiting customers only, and one is in service
                    # But simpler: q includes all in system. When service starts, we don't remove yet.
                    # On departure, we remove the one whose service ended.
                    # How to know which one? Since FCFS, it's the oldest.
                    # But we stored (arr_time, svc). We need to track completion.
                    # Alternative: maintain a separate "in-service" customer.
                    
                    # Let's refactor: 
                    # in_service: None or (arr_time, end_time)
                    # q: list of (arr_time, svc_duration) for waiting
                    pass
                else:
                    # Server busy, customer waits
                    if t >= warmup_end:
                        count_wait_win += 1
                    # Blocked? In M/M/1 with infinite buffer, no blocking. blk=0 always.
                    # p_loss = 0.
                
                # Generate next arrival
                next_arr = t + rng.expovariate(lam)
                
                # Update state for integration
                prev_n = n_in_sys
                # prev_busy already set if started service, else remains true if was busy
                if server_free_at > t:
                    prev_busy = True
                else:
                    prev_busy = False
                    
            elif evt_type == 'dep':
                # A customer completes service
                # Who? The one in service.
                # We need to track in-service customer.
                # Let's assume we have an in_service variable.
                # Since I didn't initialize it properly above, let me restructure mentally.
                
                # For this code block, I'll assume proper tracking.
                # Departure: remove oldest from q if it was in service? 
                # Actually, let's say: when service starts, we pop from q and set in_service.
                # When dep occurs, we finish in_service, add its sojourn time, then check if q non-empty to start next.
                
                # Since I'm writing inline, let me adjust the logic flow.
                # I will rewrite the loop body carefully.
                pass
        
        # Given complexity, let me write a clean version below.
        # I'll replace the entire main function content with a correct implementation.
        
        # Correct Implementation:
        t = 0.0
        next_arr = rng.expovariate(lam)
        q = []  # waiting customers: (arrival_time, service_duration)
        in_service = None  # (arrival_time, end_time) or None
        server_free_at = 0.0
        
        prev_t = 0.0
        prev_n = 0
        prev_busy = False
        
        int_L = 0.0
        int_busy = 0.0
        count_arr_win = 0
        count_dep_win = 0
        count_blk_win = 0
        sum_sojourn_win = 0.0
        count_wait_win = 0
        count_loss_win = 0
        
        total_arr = 0
        total_dep = 0
        total_blk = 0
        
        while t < horizon_min:
            # Determine next event
            events = []
            if next_arr < horizon_min:
                events.append(('arr', next_arr))
            if in_service is not None and in_service[1] < horizon_min:
                events.append(('dep', in_service[1]))
            
            if not events:
                break
            
            evt_type, evt_time = min(events, key=lambda x: x[1])
            
            # Integrate
            dt = evt_time - prev_t
            if prev_t < warmup_end and evt_time > warmup_end:
                dt_post = evt_time - warmup_end
                int_L += prev_n * dt_post
                if prev_busy:
                    int_busy += dt_post
            elif prev_t >= warmup_end:
                int_L += prev_n * dt
                if prev_busy:
                    int_busy += dt
            
            prev_t = evt_time
            t = evt_time
            
            if evt_type == 'arr':
                svc = rng.expovariate(mu)
                q.append((t, svc))
                n_in_sys = len(q) + (1 if in_service is not None else 0)
                total_arr += 1
                if t >= warmup_end:
                    count_arr_win += 1
                
                # Try to start service if idle
                if in_service is None:
                    arr_t, svc_dur = q.pop(0)
                    end_t = t + svc_dur
                    in_service = (arr_t, end_t)
                    prev_busy = True
                else:
                    # Customer waits
                    if t >= warmup_end:
                        count_wait_win += 1
                    prev_busy = True  # still busy
                
                next_arr = t + rng.expovariate(lam)
                prev_n = len(q) + (1 if in_service is not None else 0)
                
            elif evt_type == 'dep':
                arr_t, end_t = in_service
                sojourn = end_t - arr_t
                in_service = None
                total_dep += 1
                if t >= warmup_end:
                    count_dep_win += 1
                    sum_sojourn_win += sojourn
                
                # Start next if available
                if q:
                    arr_t_new, svc_dur_new = q.pop(0)
                    end_t_new = t + svc_dur_new
                    in_service = (arr_t_new, end_t_new)
                    prev_busy = True
                else:
                    prev_busy = False
                
                prev_n = len(q) + (1 if in_service is not None else 0)
        
        # After loop, integrate remaining time if any
        if prev_t < horizon_min:
            dt = horizon_min - prev_t
            if prev_t < warmup_end and horizon_min > warmup_end:
                dt_post = horizon_min - warmup_end
                int_L += prev_n * dt_post
                if prev_busy:
                    int_busy += dt_post
            elif prev_t >= warmup_end:
                int_L += prev_n * dt
                if prev_busy:
                    int_busy += dt
        
        win_len = horizon_min - warmup_end
        if win_len > 0:
            L_est = int_L / win_len
            W_est = sum_sojourn_win / count_dep_win if count_dep_win > 0 else 0.0
            busy_frac_est = int_busy / win_len
            p_wait_est = count_wait_win / count_arr_win if count_arr_win > 0 else 0.0
            p_loss_est = 0.0  # Infinite buffer
            blk_est = 0.0
            dep_rate_est = count_dep_win / (win_len / 60.0) if win_len > 0 else 0.0  # per hour
            lam_eff_est = count_arr_win / (win_len / 60.0) if win_len > 0 else 0.0
            busy_util_est = busy_frac_est  # For c=1, E[min(N,1)] = P(busy)
            busy_occ_est = busy_frac_est   # 1 - pi_0 = P(busy)
        else:
            L_est = W_est = busy_frac_est = p_wait_est = p_loss_est = blk_est = dep_rate_est = lam_eff_est = busy_util_est = busy_occ_est = 0.0
        
        seeds_used.append(seed)
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr_win)
        all_dep.append(count_dep_win)
        all_blk.append(blk_est)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        all_dep_rate.append(dep_rate_est)
    
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0
    
    result = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_wait": avg(all_p_wait),
        "runtime_units": "minute",
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "minute",
        "win": horizon_min * 0.75,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_loss": avg(all_p_loss),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait,
        "busy_occupied": avg(all_busy_occupied)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
