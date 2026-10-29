import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 4.0 # per hour
    mu_base = 12.0 # per hour (5 min avg -> 60/5=12)
    
    if args.pert == 'lam_up': lam_base *= 1.1
    elif args.pert == 'mu_up': mu_base *= 1.1
    elif args.pert == 'c_up': pass # c is fixed at 1
    
    time_unit = "hour"
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
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
    total_customers_served = 0
    
    for i in range(args.seeds):
        seed_val = args.seed_start + i
        rng = random.Random(seed_val)
        t = 0.0
        next_arr_t = rng.expovariate(lam_base)
        
        # State: 0=idle, 1=busy
        state = 0 
        last_change_t = 0.0
        
        # Accumulators for this seed within window
        s_area_L = 0.0
        s_area_busy = 0.0
        s_arr_count = 0
        s_dep_count = 0
        s_blk_count = 0
        s_sum_W = 0.0
        s_sum_wait = 0.0
        s_cust_served = 0
        
        # Queue of (arrival_time, service_duration)
        queue = []
        
        while t < horizon:
            # Determine next event time
            next_dep_t = float('inf')
            if state == 1 and queue:
                # The customer currently being served has a known end time?
                # We need to track the current service completion time explicitly or derive it.
                # Let's store current_service_end_t when service starts.
                # But we don't have that variable initialized properly in loop structure above.
                # Refactor: Keep track of `current_service_end` if busy.
                pass
            
            # Better approach: Event-driven with explicit variables
            # Variables:
            # t: current time
            # next_arrival: time of next arrival
            # next_departure: time of next departure (if server busy), else inf
            # server_busy: bool
            # current_customer: dict {arr_t, svc_dur, start_t} or None
            
            # Resetting logic for clean implementation inside loop:
            
            # Initialize for seed run
            t = 0.0
            next_arrival = rng.expovariate(lam_base)
            next_departure = float('inf')
            server_busy = False
            current_cust = None # {arr_t, svc_dur, start_t}
            queue = [] # list of {arr_t, svc_dur}
            
            # Warmup handling: We simulate from 0 to horizon.
            # Statistics only collected after win_start.
            
            while t < horizon:
                # Find next event
                events = []
                if next_arrival <= horizon:
                    events.append(('arr', next_arrival))
                if next_departure <= horizon:
                    events.append(('dep', next_departure))
                
                if not events:
                    break
                
                ev_type, ev_time = min(events, key=lambda x: x[1])
                
                # Integrate area up to ev_time
                dt = ev_time - t
                if t >= win_start:
                    # L is number in system (queue + server)
                    n_in_sys = len(queue) + (1 if server_busy else 0)
                    s_area_L += n_in_sys * dt
                    if server_busy:
                        s_area_busy += dt
                
                t = ev_time
                
                if ev_type == 'arr':
                    # Generate service duration NOW
                    svc_dur = rng.expovariate(mu_base)
                    cust = {'arr_t': t, 'svc_dur': svc_dur}
                    
                    if t >= win_start:
                        s_arr_count += 1
                    
                    if not server_busy:
                        server_busy = True
                        current_cust = cust
                        next_departure = t + svc_dur
                    else:
                        # Check capacity? M/M/1 usually infinite queue unless specified.
                        # Problem says "stable", implies standard M/M/1. No blocking mentioned in base model.
                        # However, output requires blk/p_loss. For standard M/M/1, these are 0.
                        # If perturbation doesn't change structure, blk remains 0.
                        queue.append(cust)
                        
                elif ev_type == 'dep':
                    # Customer leaves
                    if t >= win_start:
                        s_dep_count += 1
                        w = t - current_cust['arr_t']
                        s_sum_W += w
                        s_cust_served += 1
                        # Wait time = W - Service Time
                        wait = w - current_cust['svc_dur']
                        s_sum_wait += wait
                        
                    # Next customer
                    if queue:
                        next_cust = queue.pop(0)
                        current_cust = next_cust
                        next_departure = t + next_cust['svc_dur']
                        # Server stays busy
                    else:
                        server_busy = False
                        current_cust = None
                        next_departure = float('inf')
                
                # Schedule next arrival
                if ev_type == 'arr':
                    next_arrival = t + rng.expovariate(lam_base)
            
            # End of simulation for this seed
            # Calculate stats for this seed
            if win_len > 0:
                l_est = s_area_L / win_len
                w_est = s_sum_W / s_cust_served if s_cust_served > 0 else 0.0
                bf_est = s_area_busy / win_len
                pl_est = s_blk_count / s_arr_count if s_arr_count > 0 else 0.0
                pw_est = s_sum_wait / s_cust_served if s_cust_served > 0 else 0.0 # Avg wait time? Or prob wait?
                # p_wait usually means probability of waiting (queueing).
                # In M/M/1, P(wait) = rho.
                # From sim: Count customers who had wait > 0?
                # Let's re-calculate p_wait as fraction of served customers who waited.
                # Need to track count of those with wait>0.
                pass

            # Re-running logic to capture p_wait correctly (prob of waiting)
            # I will integrate this into the main loop above by tracking counts.
            
            # Since I can't easily edit the loop structure now without rewriting, 
            # I will assume standard definitions:
            # p_wait = Probability an arriving customer waits.
            # In discrete sim: count(arrivals where server was busy) / total arrivals.
            
            # Let's restart the inner loop logic mentally to ensure correctness before writing final code.
            # Actually, I will write the code carefully in one go.
            
            seeds_used.append(seed_val)
            # Placeholder calculations, will be refined in actual code block below.
            # To save lines, I'll compute aggregates directly.
            
            # Aggregates
            total_arr += s_arr_count
            total_dep += s_dep_count
            total_blk += s_blk_count
            total_time_in_sys += s_sum_W
            total_busy_time += s_area_busy
            total_wait_time += s_sum_wait # This is sum of wait times, not count
            
            # Per seed estimates
            # Note: p_wait needs count of waiting customers.
            # I need to add `s_wait_count` to the loop.
            
            # Due to strict line limit and complexity, I will implement the full correct logic in the final output.
            
            # Quick fix for the draft above:
            # I need to track `s_wait_count` (number of customers who waited > 0).
            
            # Final Code Structure Plan:
            # 1. Parse args.
            # 2. Init global accumulators.
            # 3. Loop seeds.
            # 4. Inside seed loop: Simulate M/M/1.
            #    - Track: arr_count, dep_count, blk_count (always 0 for M/M/1), wait_count, sum_W, sum_wait_time, area_L, area_busy.
            #    - Only accumulate if t >= win_start.
            # 5. Compute per-seed metrics.
            # 6. Append to lists.
            # 7. Compute global averages.
            # 8. Print JSON.

# The following is the actual executable code adhering to constraints.

import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam = 4.0
    mu = 12.0
    if args.pert == 'lam_up': lam *= 1.1
    elif args.pert == 'mu_up': mu *= 1.1
    
    time_unit = "hour"
    horizon = args.horizon
    win_start = horizon * 0.25
    win_len = horizon - win_start
    
    seeds_list = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    agg_arr = 0
    agg_dep = 0
    agg_blk = 0
    agg_sum_W = 0.0
    agg_sum_wait = 0.0
    agg_area_L = 0.0
    agg_area_busy = 0.0
    agg_wait_count = 0
    agg_served = 0
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        busy = False
        cur_svc_end = float('inf')
        cur_arr_t = 0.0
        cur_svc_dur = 0.0
        queue = [] # List of (arr_t, svc_dur)
        
        s_arr = 0
        s_dep = 0
        s_blk = 0
        s_sum_W = 0.0
        s_sum_wait = 0.0
        s_area_L = 0.0
        s_area_busy = 0.0
        s_wait_cnt = 0
        s_served = 0
        
        while t < horizon:
            events = []
            if next_arr <= horizon: events.append((next_arr, 'A'))
            if next_dep <= horizon: events.append((next_dep, 'D'))
            if not events: break
            
            ev_t, ev_type = min(events, key=lambda x: x[0])
            dt = ev_t - t
            
            if t >= win_start:
                n = len(queue) + (1 if busy else 0)
                s_area_L += n * dt
                if busy: s_area_busy += dt
            
            t = ev_t
            
            if ev_type == 'A':
                svc = rng.expovariate(mu)
                if t >= win_start: s_arr += 1
                if not busy:
                    busy = True
                    cur_arr_t = t
                    cur_svc_dur = svc
                    next_dep = t + svc
                else:
                    queue.append((t, svc))
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'D':
                if t >= win_start:
                    s_dep += 1
                    s_served += 1
                    w = t - cur_arr_t
                    s_sum_W += w
                    wait = w - cur_svc_dur
                    s_sum_wait += wait
                    if wait > 1e-9: s_wait_cnt += 1
                
                if queue:
                    nxt = queue.pop(0)
                    cur_arr_t, cur_svc_dur = nxt
                    next_dep = t + cur_svc_dur
                else:
                    busy = False
                    next_dep = float('inf')
        
        if win_len > 0 and s_served > 0:
            L = s_area_L / win_len
            W = s_sum_W / s_served
            BF = s_area_busy / win_len
            PL = s_blk / s_arr if s_arr > 0 else 0.0
            PW = s_wait_cnt / s_served if s_served > 0 else 0.0
            
            per_seed_L.append(L)
            per_seed_W.append(W)
            per_seed_busy_frac.append(BF)
            per_seed_p_loss.append(PL)
            per_seed_p_wait.append(PW)
            seeds_list.append(seed)
            
            agg_arr += s_arr
            agg_dep += s_dep
            agg_blk += s_blk
            agg_sum_W += s_sum_W
            agg_sum_wait += s_sum_wait
            agg_area_L += s_area_L
            agg_area_busy += s_area_busy
            agg_wait_count += s_wait_cnt
            agg_served += s_served

    if agg_served == 0 or win_len == 0:
        print(json.dumps({"error": "no data"}))
        return

    N_seeds = len(seeds_list)
    avg_L = agg_area_L / (N_seeds * win_len)
    avg_W = agg_sum_W / agg_served
    avg_BF = agg_area_busy / (N_seeds * win_len)
    avg_PL = agg_blk / agg_arr if agg_arr > 0 else 0.0
    avg_PW = agg_wait_count / agg_served if agg_served > 0 else 0.0
    
    # Convert W to minutes
    W_min = avg_W * 60.0
    
    # Dep rate per hour
    dep_rate = agg_dep / (N_seeds * win_len)
    lam_eff = dep_rate # Conservation law
    
    out = {
        "L": round(avg_L, 6),
        "W": round(W_min, 6),
        "busy_frac": round(avg_BF, 6),
        "p_wait": round(avg_PW, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(agg_arr / N_seeds, 6),
        "blk": round(agg_blk / N_seeds, 6),
        "busy_util": round(avg_BF, 6),
        "dep": round(agg_dep / N_seeds, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_PL, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x*60, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
