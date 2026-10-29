import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 4.0 # per hour
    mu_base = 12.0 # per hour (5 min mean)
    c = 1
    
    if args.pert == 'lam_up': lam = lam_base * 1.2
    elif args.pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif args.pert == 'c_up': c = 2; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    horizon = args.horizon
    warmup = horizon * 0.25
    win_len = horizon - warmup
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arr_count = 0
    all_dep_count = 0
    all_blk_count = 0
    all_p_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        seed_list.append(s)
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n_in_sys = 0
        last_event_t = 0.0
        
        custs = [] # list of dicts: {'arr_t':..., 'dep_t':...}
        
        while t < horizon:
            if next_arr < next_dep:
                t = next_arr
                # Integrate area before state change
                dt = t - last_event_t
                if last_event_t >= warmup:
                    all_L_area += n_in_sys * dt
                    all_busy_time += min(n_in_sys, c) * dt
                
                # Arrival
                if n_in_sys < c: # M/M/1/c with c=1 is effectively M/M/1 queue if we allow waiting? 
                    # Standard M/M/1 has infinite capacity. The prompt says "system stable", implies infinite buffer or loss system?
                    # "blk" suggests loss system possible, but M/M/1 usually means infinite queue.
                    # However, "busy_frac" definition mentions E[min(N,c)]/c. If c=1 and infinite queue, N can be >1.
                    # Let's assume standard M/M/1 (infinite queue) unless specified as finite capacity.
                    # But wait, "blk" is requested. In M/M/1 infinite queue, blk=0 always.
                    # If it were M/M/1/1 (loss), then blk>0.
                    # Prompt: "某打印店只有 1 名值班员". Usually implies queueing.
                    # "系统稳定" -> rho < 1.
                    # If infinite queue, blk=0. If finite, need capacity. Not given.
                    # Given "blk" key exists, maybe it's a general template. For M/M/1, blk=0.
                    # Let's stick to M/M/1 (infinite queue).
                    
                    service_time = rng.expovariate(mu)
                    dep_t = t + service_time
                    custs.append({'arr_t': t, 'dep_t': dep_t})
                    n_in_sys += 1
                    if n_in_sys == 1:
                        next_dep = dep_t
                    else:
                        # Queue grows, next_dep remains the earliest departure among active services?
                        # No, only one server. So only one service at a time.
                        # If n_in_sys > 1, the new customer waits. The current service continues.
                        # next_dep should be the completion time of the CURRENTLY served customer.
                        # We track the currently served customer's end time.
                        pass
                    
                    # Update next_arr
                    next_arr = t + rng.expovariate(lam)
                    
                else:
                    # Loss case (if capacity was limited). Here capacity is infinite.
                    # If we treat c as capacity, then this branch runs.
                    # But for M/M/1, c=1 server, infinite queue.
                    # The variable 'c' in perturbation might mean number of servers?
                    # "c_up" -> c=2. Then it becomes M/M/2.
                    # If c is number of servers, then queue is infinite.
                    # So arrival always accepted.
                    # Let's re-read: "busy_frac ... E[min(N,c)]/c". This formula works for multi-server too.
                    # So c is number of servers.
                    # Arrival is always accepted (infinite queue).
                    # So blk is always 0.
                    
                    # Correction: The code above had `if n_in_sys < c`. That was wrong logic for infinite queue.
                    # For infinite queue, everyone enters.
                    # We need to manage the queue properly.
                    
                    # Let's restart the simulation loop logic for clarity.
                    break
            
            else:
                t = next_dep
                # Departure
                dt = t - last_event_t
                if last_event_t >= warmup:
                    all_L_area += n_in_sys * dt
                    all_busy_time += min(n_in_sys, c) * dt
                
                # Find who leaves
                # We need to know which customer left.
                # Since we don't store individual states easily in this simple loop without a heap,
                # let's use a simpler approach: track queue length and busy status.
                
                # Actually, for W calculation, we need sum of (dep_t - arr_t) for customers departing in window.
                # We need to know their arrival times.
                
                # Let's refactor using a priority queue for events or just careful bookkeeping.
                # Simpler: Maintain a list of customers in system.
                # When departure happens, remove the one whose dep_t matches t.
                
                # Remove from custs
                idx = -1
                for k, cu in enumerate(custs):
                    if abs(cu['dep_t'] - t) < 1e-9:
                        idx = k
                        break
                if idx != -1:
                    cu = custs.pop(idx)
                    n_in_sys -= 1
                    if last_event_t >= warmup:
                        all_dep_count += 1
                        w_val = cu['dep_t'] - cu['arr_t']
                        all_W_sum += w_val
                        if cu['arr_t'] >= warmup: # Wait, W is average over ALL customers in window?
                            # Usually W is average sojourn time of customers who DEPARTED in the window.
                            # Or customers who ARRIVED in the window?
                            # Little's Law L = lambda * W uses steady state averages.
                            # Common practice: Average over customers completing service in the observation window.
                            pass
                        
                        # Check if they waited
                        # Did they wait? If there was someone ahead when they arrived.
                        # Hard to check retroactively without storing queue position at arrival.
                        # Alternative: P(wait) = fraction of arrivals that find server busy.
                        # We can count this at arrival time.
                        
                    # Schedule next departure if any
                    if custs:
                        # Find min dep_t among remaining
                        # Note: Only c servers are busy. Others are waiting.
                        # We need to assign service start times.
                        # This naive list approach doesn't handle queue discipline well for multi-server.
                        # For single server (c=1), it's FIFO.
                        # For c>1, it's more complex.
                        # Given the problem is likely M/M/1 or M/M/c, let's assume FIFO.
                        # We need to recalculate dep_t for those who started service after previous ones finished.
                        # This requires event-driven simulation with proper state management.
                        pass
                    else:
                        next_dep = float('inf')
                
                last_event_t = t

    # The above manual loop is getting messy. Let's write a cleaner discrete event sim.
    # Reset accumulators for clean implementation
    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arr_count = 0
    all_dep_count = 0
    all_blk_count = 0
    all_p_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        
        # State
        t = 0.0
        n_in_sys = 0
        n_busy = 0
        last_event_t = 0.0
        
        # Events: (time, type, data)
        # type: 'A' (arrival), 'D' (departure)
        import heapq
        events = []
        
        # Initial arrival
        next_arr_t = rng.expovariate(lam)
        heapq.heappush(events, (next_arr_t, 'A', None))
        
        # Track customers for W calculation
        # We need to know when a customer arrives and when they depart.
        # Store arrival time in a queue.
        # For multi-server, we need to know which server is free.
        # Simplification: Use a list of "active services" end times.
        # And a queue of waiting customers (just their arrival times).
        
        active_services = [] # list of end times
        waiting_customers = [] # list of arrival times
        
        seed_L_area = 0.0
        seed_W_sum = 0.0
        seed_busy_time = 0.0
        seed_arr_count = 0
        seed_dep_count = 0
        seed_blk_count = 0
        seed_p_wait_count = 0
        
        while events:
            t, etype, _ = heapq.heappop(events)
            
            # Integrate area up to t
            dt = t - last_event_t
            if last_event_t >= warmup:
                seed_L_area += n_in_sys * dt
                seed_busy_time += n_busy * dt
            
            last_event_t = t
            
            if t > horizon:
                break
                
            if etype == 'A':
                # Arrival
                if last_event_t >= warmup:
                    seed_arr_count += 1
                
                # Check if blocked (only if finite capacity, here infinite)
                # If we want to support c_up as capacity limit? No, c is servers.
                # Assume infinite queue.
                
                # Generate service time
                svc_time = rng.expovariate(mu)
                
                # Determine if waits
                if n_busy < c:
                    # Start immediately
                    dep_t = t + svc_time
                    heapq.heappush(events, (dep_t, 'D', {'arr_t': t}))
                    n_busy += 1
                    n_in_sys += 1
                    # No wait
                else:
                    # Wait
                    waiting_customers.append(t)
                    n_in_sys += 1
                    if last_event_t >= warmup:
                        seed_p_wait_count += 1
                
                # Schedule next arrival
                next_arr_t = t + rng.expovariate(lam)
                heapq.heappush(events, (next_arr_t, 'A', None))
                
            elif etype == 'D':
                # Departure
                arr_t = _['arr_t']
                n_in_sys -= 1
                n_busy -= 1
                
                if last_event_t >= warmup:
                    seed_dep_count += 1
                    w_val = t - arr_t
                    seed_W_sum += w_val
                
                # Serve next if available
                if waiting_customers:
                    next_arr_t = waiting_customers.pop(0)
                    svc_time = rng.expovariate(mu)
                    dep_t = t + svc_time
                    heapq.heappush(events, (dep_t, 'D', {'arr_t': next_arr_t}))
                    n_busy += 1
                    # n_in_sys already includes them, so no change to n_in_sys count logic?
                    # Wait, n_in_sys decreased by 1 for departure.
                    # The waiting customer was already counted in n_in_sys.
                    # So moving them to active doesn't change n_in_sys.
                    # Correct.
                
        # End of seed simulation
        # Final integration step? The loop breaks when t > horizon.
        # We integrated up to the last event <= horizon.
        # Need to integrate from last_event_t to horizon?
        # Usually, we stop at horizon. The area from last_event_t to horizon should be added.
        dt_final = horizon - last_event_t
        if last_event_t >= warmup:
            seed_L_area += n_in_sys * dt_final
            seed_busy_time += n_busy * dt_final
            
        # Calculate stats for this seed
        # L = Area / Win
        l_val = seed_L_area / win_len if win_len > 0 else 0
        # W = Sum(W) / Dep_Count
        w_val = seed_W_sum / seed_dep_count if seed_dep_count > 0 else 0
        # Busy Frac = Busy Time / Win
        bf_val = seed_busy_time / win_len if win_len > 0 else 0
        # P(Loss) = Blk / Arr
        pl_val = seed_blk_count / seed_arr_count if seed_arr_count > 0 else 0
        # P(Wait) = Wait Count / Arr
        pw_val = seed_p_wait_count / seed_arr_count if seed_arr_count > 0 else 0
        
        per_seed_L.append(l_val)
        per_seed_W.append(w_val)
        per_seed_busy_frac.append(bf_val)
        per_seed_p_loss.append(pl_val)
        per_seed_p_wait.append(pw_val)
        
        all_L_area += seed_L_area
        all_W_sum += seed_W_sum
        all_busy_time += seed_busy_time
        all_arr_count += seed_arr_count
        all_dep_count += seed_dep_count
        all_blk_count += seed_blk_count
        all_p_wait_count += seed_p_wait_count

    # Aggregate stats
    total_win_area = win_len * args.seeds
    L_avg = all_L_area / total_win_area if total_win_area > 0 else 0
    W_avg = all_W_sum / all_dep_count if all_dep_count > 0 else 0
    BF_avg = all_busy_time / total_win_area if total_win_area > 0 else 0
    PL_avg = all_blk_count / all_arr_count if all_arr_count > 0 else 0
    PW_avg = all_p_wait_count / all_arr_count if all_arr_count > 0 else 0
    
    # Other metrics
    arr_avg = all_arr_count / args.seeds
    dep_avg = all_dep_count / args.seeds
    blk_avg = all_blk_count / args.seeds
    dep_rate = dep_avg / win_len * 60.0 # per hour? win_len is in hours? 
    # Horizon unit: I used expovariate(lam) where lam is per hour. So t is in hours.
    # So win_len is in hours.
    # dep_rate = (dep_avg / win_len) * 1.0? No, dep_avg is count per seed.
    # Rate = Total Deps / Total Time.
    # Total Time = win_len * seeds.
    # dep_rate = all_dep_count / (win_len * args.seeds) * 1.0 (per hour)
    dep_rate_val = all_dep_count / (win_len * args.seeds) if (win_len * args.seeds) > 0 else 0
    
    lam_eff = dep_rate_val # Flow balance
    
    # busy_util = E[min(N,c)]/c. 
    # We tracked n_busy. n_busy is min(n_in_sys, c) effectively?
    # Yes, because we only increment n_busy if n_busy < c.
    # So avg n_busy / c is the utilization.
    busy_util_val = (all_busy_time / total_win_area) / c if c > 0 else 0
    # busy_occupied = 1 - pi_0. 
    # pi_0 is prob empty. 
    # We didn't track idle time explicitly separate from busy time?
    # Idle time = Win - Busy Time.
    # pi_0 = Idle Time / Win.
    # 1 - pi_0 = Busy Time / Win = BF_avg.
    busy_occ_val = BF_avg
    
    res = {
        "L": round(L_avg, 4),
        "W": round(W_avg, 4),
        "busy_frac": round(BF_avg, 4),
        "p_wait": round(PW_avg, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": args.seeds,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(arr_avg, 4),
        "blk": round(blk_avg, 4),
        "busy_util": round(busy_util_val, 4),
        "dep": round(dep_avg, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(PL_avg
