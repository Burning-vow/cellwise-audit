import argparse, json, random
def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=1);p.add_argument('--horizon',type=float,default=100.0);p.add_argument('--seed-start',type=int,default=0);p.add_argument('--pert',default='none')
    a=p.parse_args()
    lam=6.0; mu=1/6.0; c=1
    if a.pert=='lam_up': lam*=1.2
    elif a.pert=='mu_up': mu*=1.2
    elif a.pert=='c_up': c+=1
    
    seeds_used=[]; per_seed_L=[]; per_seed_W=[]; per_seed_busy_frac=[]; per_seed_p_loss=[]; per_seed_p_wait=[]
    total_arr=0; total_dep=0; total_blk=0; total_time=0.0; total_area_N=0.0; total_area_occupied=0.0; total_wait_sum=0.0; total_service_sum=0.0; total_customers_in_window=0
    
    for i in range(a.seeds):
        seed=a.seed_start+i
        rng=random.Random(seed)
        t=0.0; next_arr=rng.expovariate(lam); queue=[]; service_end=None; 
        # State variables for integration
        last_event_t=0.0
        area_N=0.0; area_occ=0.0
        arr_count=0; dep_count=0; blk_count=0
        
        # Warmup: 25% of horizon
        warmup_end = a.horizon * 0.25
        stats_start = warmup_end
        
        # We need to track customers that arrive after stats_start or are still present at stats_start
        # But standard DES usually runs full then filters. 
        # Requirement: "service duration must be drawn at arrival and attached".
        # Requirement: "statistics only accumulated in window after removing first 25% warmup".
        # Requirement: "area quantities must be integrated before state change".
        
        # To handle the window correctly with pre-drawn services:
        # We simulate until horizon.
        # We keep a list of events or just process step by step.
        # Since we need L (avg number in system) and W (avg time in system),
        # L is integral of N(t)/T_window.
        # W is sum(time_in_system for those who departed in window? Or all who were in system?)
        # Usually W is Little's Law related. Let's assume W is average sojourn time of customers departing in the window.
        # If a customer arrives before window but departs inside, they count.
        # If a customer arrives inside and departs inside, they count.
        # If a customer arrives inside but departs outside, they don't count for W (truncated)? 
        # Standard practice: Only complete cycles within window or use specific definitions.
        # Given "steady state", let's assume we measure W on departures occurring in [stats_start, horizon].
        # And L is time-average of N(t) over [stats_start, horizon].
        
        # Data structure for customers: (arrival_time, service_duration, departure_time_if_known_or_none)
        # Actually, simpler: Just track current N and occupied status.
        # For W, we need individual times.
        
        active_customers = [] # List of dicts: {'arr':t, 'svc':dur, 'dep':None}
        
        while t < a.horizon:
            # Determine next event time
            next_ev = float('inf')
            ev_type = None
            
            if next_arr < a.horizon:
                next_ev = min(next_ev, next_arr)
                if next_arr == next_ev: ev_type = 'arr'
            
            if service_end is not None and service_end < a.horizon:
                if service_end < next_ev:
                    next_ev = service_end
                    ev_type = 'dep'
                elif service_end == next_ev:
                    # Tie-breaking: usually dep before arr or vice versa. Let's do dep first to free slot.
                    if ev_type != 'arr': # If arr was already set as inf or larger, this sets it. If equal, we prioritize dep?
                        # Actually if both are same, order matters for N(t). 
                        # Let's say Dep happens at t, Arr happens at t.
                        # If we process Dep first, N decreases then increases.
                        # If we process Arr first, N increases then decreases.
                        # In M/M/1, probability of tie is 0. But here deterministic service.
                        # Let's stick to processing Dep first if times match exactly to avoid blocking new arrivals unnecessarily?
                        # Or Arr first? Standard is often Arr then Dep or vice versa depending on convention.
                        # Let's pick Dep first to clear space.
                        ev_type = 'dep'

            if next_ev == float('inf'): break
            
            dt = next_ev - t
            # Integrate areas BEFORE changing state
            if t >= stats_start:
                n_curr = len(active_customers) + (1 if service_end is not None else 0)
                occ_curr = 1 if service_end is not None else 0
                area_N += n_curr * dt
                area_occ += occ_curr * dt
            
            t = next_ev
            
            if ev_type == 'arr':
                # Draw service time now
                svc_dur = 6.0 # Fixed 6 mins
                # Check capacity
                # System has active_customers (waiting) + server (if busy)
                # Capacity c. Server takes one. Queue holds rest.
                # Total spots = c.
                # Current occupants = len(active_customers) + (1 if service_end else 0)
                curr_occ = len(active_customers) + (1 if service_end is not None else 0)
                
                if curr_occ < c:
                    # Start service immediately if server free
                    if service_end is None:
                        service_end = t + svc_dur
                        # This customer is being served, not in waiting queue list yet?
                        # Let's define active_customers as WAITING ONLY.
                        # Served customer is tracked separately via service_end.
                        # But for W calculation, we need to know when they leave.
                        # So we store info about the person in service too.
                        # Let's change structure:
                        # `in_service` : dict or None. Contains {'arr':t, 'svc':dur, 'end':time}
                        # `queue`: list of dicts {'arr':t, 'svc':dur}
                        pass
                    else:
                        # Add to queue
                        active_customers.append({'arr':t, 'svc':svc_dur})
                else:
                    # Blocked/Lost
                    blk_count += 1
                
                # Generate next arrival
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                # Customer leaves
                # Who left? The one in service.
                # We need their arrival time to calculate wait/sojourn.
                # We didn't store it in `service_end`.
                # Refactor: Keep `current_cust` object.
                # Let's restart loop logic slightly cleaner.
                pass

        # The above inline logic is getting messy due to missing state storage for the person in service.
        # Let's rewrite the simulation loop properly.
        
        # Reset for proper implementation
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] # Waiting customers: list of (arrival_time, service_duration)
        cust_in_svc = None # (arrival_time, service_duration, end_time)
        
        area_N = 0.0
        area_occ = 0.0
        arr_w = 0; dep_w = 0; blk_w = 0
        wait_sum_w = 0.0 # Sum of sojourn times for departures in window
        
        warmup = a.horizon * 0.25
        
        while t < a.horizon:
            # Find next event
            candidates = []
            if next_arr <= a.horizon: candidates.append((next_arr, 'A'))
            if cust_in_svc is not None and cust_in_svc[2] <= a.horizon: candidates.append((cust_in_svc[2], 'D'))
            
            if not candidates: break
            
            next_ev, ev_type = min(candidates, key=lambda x: x[0])
            
            # Integrate
            dt = next_ev - t
            if t >= warmup:
                n_curr = len(queue) + (1 if cust_in_svc else 0)
                occ_curr = 1 if cust_in_svc else 0
                area_N += n_curr * dt
                area_occ += occ_curr * dt
            
            t = next_ev
            
            if ev_type == 'A':
                svc_dur = 6.0
                # Check if can enter
                # Capacity c. 
                # Occupants = len(queue) + (1 if cust_in_svc else 0)
                if len(queue) + (1 if cust_in_svc else 0) < c:
                    if cust_in_svc is None:
                        cust_in_svc = (t, svc_dur, t + svc_dur)
                    else:
                        queue.append((t, svc_dur))
                else:
                    if t >= warmup: blk_w += 1
                
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'D':
                # Departure
                arr_t, svc_dur, end_t = cust_in_svc
                if t >= warmup:
                    dep_w += 1
                    wait_sum_w += (t - arr_t)
                
                # Move next from queue to service if exists
                if queue:
                    nxt_arr, nxt_svc = queue.pop(0)
                    cust_in_svc = (nxt_arr, nxt_svc, t + nxt_svc)
                else:
                    cust_in_svc = None
                    
        # End of sim for this seed
        win_len = a.horizon - warmup
        if win_len > 0:
            l_val = area_N / win_len
            w_val = wait_sum_w / dep_w if dep_w > 0 else 0.0
            bf_val = area_occ / win_len
            pl_val = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0 # Note: arr_w needs counting too
            pw_val = 0.0 # Probability of waiting? P(N>0) or similar? 
                          # Usually p_wait is fraction of arrivals that had to wait.
                          # We didn't track that explicitly in window easily without storing more.
                          # Let's approximate or recalculate.
                          # For M/M/1/c, p_wait is prob an arriving customer finds server busy.
                          # We can track: if arrived and found cust_in_svc not None -> waited.
                          # Need to add this counter.
            
            # Re-run quickly to get p_wait? No, modify loop.
            # I will modify the loop above in my head to include `waited_w`.
            # Since I cannot edit previous code block, I will assume standard definitions.
            # Let's output dummy values for complex ones if not tracked, but better to track.
            # I'll rewrite the whole function body cleanly below.
            pass

    # Clean Rewrite
    import argparse, json, random
    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--seeds', type=int, default=1)
        parser.add_argument('--horizon', type=float, default=100.0)
        parser.add_argument('--seed-start', type=int, default=0)
        parser.add_argument('--pert', type=str, default='none')
        args = parser.parse_args()
        
        lam = 6.0
        mu = 1/6.0
        c = 1
        if args.pert == 'lam_up': lam *= 1.2
        elif args.pert == 'mu_up': mu *= 1.2
        elif args.pert == 'c_up': c += 1
        
        H = args.horizon
        warmup = H * 0.25
        win_len = H - warmup
        
        res_L = []
        res_W = []
        res_bf = []
        res_pl = []
        res_pw = []
        res_arr = []
        res_dep = []
        res_blk = []
        res_waited = []
        
        for i in range(args.seeds):
            seed = args.seed_start + i
            rng = random.Random(seed)
            t = 0.0
            next_arr = rng.expovariate(lam)
            queue = [] # (arrival_time, service_duration)
            cust_in_svc = None # (arrival_time, service_duration, end_time)
            
            area_N = 0.0
            area_occ = 0.0
            arr_w = 0
            dep_w = 0
            blk_w = 0
            waited_w = 0
            wait_sum_w = 0.0
            
            while t < H:
                candidates = []
                if next_arr <= H: candidates.append((next_arr, 'A'))
                if cust_in_svc is not None and cust_in_svc[2] <= H: candidates.append((cust_in_svc[2], 'D'))
                
                if not candidates: break
                
                next_ev, ev_type = min(candidates, key=lambda x: x[0])
                
                dt = next_ev - t
                if t >= warmup:
                    n_curr = len(queue) + (1 if cust_in_svc else 0)
                    occ_curr = 1 if cust_in_svc else 0
                    area_N += n_curr * dt
                    area_occ += occ_curr * dt
                
                t = next_ev
                
                if ev_type == 'A':
                    svc_dur = 6.0
                    curr_occ = len(queue) + (1 if cust_in_svc else 0)
                    
                    if curr_occ < c:
                        if cust_in_svc is None:
                            cust_in_svc = (t, svc_dur, t + svc_dur)
                            if t >= warmup:
                                arr_w += 1
                                # Did not wait
                        else:
                            queue.append((t, svc_dur))
                            if t >= warmup:
                                arr_w += 1
                                waited_w += 1
                    else:
                        if t >= warmup:
                            blk_w += 1
                            
                    next_arr = t + rng.expovariate(lam)
                    
                elif ev_type == 'D':
                    arr_t, svc_dur, end_t = cust_in_svc
                    if t >= warmup:
                        dep_w += 1
                        wait_sum_w += (t - arr_t)
                        
                    if queue:
                        nxt_arr, nxt_svc = queue.pop(0)
                        cust_in_svc = (nxt_arr, nxt_svc, t + nxt_svc)
                    else:
                        cust_in_svc = None
                        
            if win_len > 0:
                L = area_N / win_len
                W = wait_sum_w / dep_w if dep_w > 0 else 0.0
                BF = area_occ / win_len
                PL = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
                PW = waited_w / arr_w if arr_w > 0 else 0.0
                
                res_L.append(L)
                res_W.append(W)
                res_bf.append(BF)
                res_pl.append(PL)
                res_pw.append(PW)
                res_arr.append(arr_w)
                res_dep.append(dep_w)
                res_blk.append(blk_w)
                res_waited.append(waited_w)
            else:
                res_L.append(0.0); res_W.append(0.0); res_bf.append(0.0); res_pl.append(0.0); res_pw.append(0.0)
                res_arr.append(0); res_dep.append(0); res_blk.append(0); res_waited.append(0)
                
        avg_L = sum(res_L)/len(res_L) if res_L else 0
        avg_W = sum(res_W)/len(res_W) if res_W else 0
        avg_bf = sum(res_bf)/len(res_bf) if res_bf else 0
        avg_pl = sum(res_pl)/len(res_pl) if res_pl else 0
        avg_pw = sum(res_pw)/len(res_pw) if res_pw else 0
        avg_arr = sum(res_arr)/len(res_arr) if res_arr else 0
        avg_dep = sum(res_dep)/len(res_dep) if res_dep else 0
        avg_blk = sum(res_blk)/len(res_blk) if res_blk else 0
        
        # Busy util E[min(N,c)]/c vs Busy occupied 1-pi0
        # In single server, these are same.
        # pi0 approx 1 - avg_bf? No, avg_bf is time avg occupancy.
        # busy_util = avg_bf / c
        # busy_occupied = avg_bf (since c=1, occ is 0 or 1)
        
        out = {
            "L": round(avg_L, 4),
            "W": round(avg_W, 4),
            "busy_frac": round(avg_bf, 4),
            "runtime_units": "minute",
            "seed_list": [args.seed_start + i for i in range(args.seeds)],
            "seeds_used": args.seeds,
            "time_unit": "minute",
            "win": round(win_len, 4),
            "arr": round(avg_arr, 4),
            "blk": round(avg_blk, 4),
            "busy_util": round(avg_bf / c
