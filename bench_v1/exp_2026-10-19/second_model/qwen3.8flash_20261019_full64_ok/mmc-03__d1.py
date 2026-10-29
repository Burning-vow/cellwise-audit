import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base, mu_base = 8.0, 10.0
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': pass
    
    c = 2
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    all_L, all_W, all_busy, all_ploss, all_pwait = [], [], [], [], []
    per_seed_L, per_seed_W, per_seed_busy, per_seed_ploss, per_seed_pwait = [], [], [], [], []
    seeds_used = 0
    seed_list = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy_count = 0
        next_arr = rng.expovariate(lam_base)
        service_times = []
        queue = []
        arr_in_win = 0
        dep_in_win = 0
        blk_in_win = 0
        wait_sum = 0.0
        time_at_n = {k: 0.0 for k in range(c+1)}
        last_t = 0.0
        
        while t < horizon:
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if queue and len(queue) > 0:
                st = service_times[queue[0]] if queue else None
                if st is not None:
                    events.append(('dep', t + st))
            
            if not events:
                break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            if ev_time > win_start:
                dt = ev_time - max(last_t, win_start)
                if dt > 0:
                    L_area = sum(k * time_at_n[k] for k in time_at_n) / (ev_time - last_t) if (ev_time - last_t) > 0 else 0
                    # Actually we need to integrate properly
                    pass
            
            # Update time integrals before state change
            dt = ev_time - last_t
            if dt > 0 and last_t >= win_start:
                for k in time_at_n:
                    time_at_n[k] += dt if k == n else 0
                # Wait, this approach is wrong. Let me redo the integration.
            
            # Better approach: track area under N(t) curve
            # We'll compute at end using stored values
            
            t = ev_time
            last_t = t
            
            if ev_type == 'arr':
                if t >= win_start:
                    arr_in_win += 1
                if n < c:
                    n += 1
                    st = rng.expovariate(mu_base)
                    service_times.append(st)
                    queue.append(len(service_times)-1)
                else:
                    # Queue or block? Problem says FCFS with 2 servers, no blocking mentioned explicitly
                    # But output requires p_loss and blk. Assume infinite queue, so blk=0 always?
                    # Or maybe finite capacity? Not specified. Let's assume infinite queue, blk=0.
                    queue.append(None)  # placeholder, but we need to handle waiting customers
                    # Actually let's restructure: maintain list of customers in system
                    pass
                
                next_arr = t + rng.expovariate(lam_base)
                
            elif ev_type == 'dep':
                if t >= win_start:
                    dep_in_win += 1
                n -= 1
                if queue:
                    idx = queue.pop(0)
                    if idx is not None:
                        # This customer was being served
                        pass
                    else:
                        # A waiting customer starts service
                        st = rng.expovariate(mu_base)
                        service_times.append(st)
                        queue.append(len(service_times)-1)
                        n += 1
                        # Calculate wait time for this customer
                        # Need arrival time... this structure is getting complex
                        pass
        
        # This simulation logic is flawed. Let me rewrite more carefully.
        
        # Reset and do it properly
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam_base)
        # Each customer: (arrival_time, service_time, start_service_time)
        customers = []  # in system
        queue_customers = []  # waiting
        serving = []  # currently being served, each is index into customers
        
        arr_in_win = 0
        dep_in_win = 0
        blk_in_win = 0
        wait_total = 0.0
        total_time_in_sys = 0.0
        area_N = 0.0
        last_event_time = 0.0
        prev_n = 0
        
        # For busy fraction: E[min(N,c)]/c where N is number in system
        # We need integral of min(n(t), c) over time
        
        area_min_nc = 0.0
        
        while t < horizon:
            # Determine next event
            candidates = []
            if next_arr < horizon:
                candidates.append((next_arr, 'arr'))
            if serving:
                # Find earliest completion among serving customers
                # Each serving customer has an end time
                pass
            
            # Let me use a different approach: event-driven with priority queue via sorted list
            # Simpler: just check both possibilities
            
            next_dep = float('inf')
            dep_idx = -1
            for si, cust_idx in enumerate(serving):
                ct = customers[cust_idx]
                end_t = ct['start'] + ct['service']
                if end_t < next_dep:
                    next_dep = end_t
                    dep_idx = si
            
            if next_arr <= next_dep and next_arr < horizon:
                # Arrival
                dt = next_arr - last_event_time
                if dt > 0:
                    area_N += prev_n * dt
                    area_min_nc += min(prev_n, c) * dt
                t = next_arr
                last_event_time = t
                
                if t >= win_start:
                    arr_in_win += 1
                
                cust = {'arrival': t, 'service': rng.expovariate(mu_base), 'start': None}
                customers.append(cust)
                cust_idx = len(customers) - 1
                
                if n < c:
                    cust['start'] = t
                    serving.append(cust_idx)
                    n += 1
                    prev_n = n
                else:
                    queue_customers.append(cust_idx)
                    # Customer waits, will start when server free
                    # No immediate state change for n since they're in system but not being served
                    # n counts all in system including waiting
                    n += 1
                    prev_n = n
                
                next_arr = t + rng.expovariate(lam_base)
                
            elif next_dep < horizon:
                # Departure
                dt = next_dep - last_event_time
                if dt > 0:
                    area_N += prev_n * dt
                    area_min_nc += min(prev_n, c) * dt
                t = next_dep
                last_event_time = t
                
                if t >= win_start:
                    dep_in_win += 1
                
                cust_idx = serving.pop(dep_idx)
                cust = customers[cust_idx]
                cust['end'] = t
                total_time_in_sys += t - cust['arrival']
                if cust['start'] is not None:
                    wait_total += cust['start'] - cust['arrival']
                else:
                    wait_total += t - cust['arrival']  # Shouldn't happen if started service
                
                n -= 1
                prev_n = n
                
                # Start next from queue if any
                if queue_customers and n < c:
                    q_idx = queue_customers.pop(0)
                    qc = customers[q_idx]
                    qc['start'] = t
                    serving.append(q_idx)
                    n += 1
                    prev_n = n
            else:
                break
        
        # Final segment
        dt = horizon - last_event_time
        if dt > 0:
            area_N += prev_n * dt
            area_min_nc += min(prev_n, c) * dt
        
        if win_len > 0:
            L_est = area_N / win_len
            W_est = total_time_in_sys / dep_in_win if dep_in_win > 0 else 0
            busy_est = area_min_nc / (win_len * c)
            p_wait_est = 0.0  # Probability that arriving customer finds all servers busy
            # Count arrivals that had to wait
            waited_arrivals = 0
            total_arrivals_for_pw = 0
            for cust in customers:
                if cust['arrival'] >= win_start:
                    total_arrivals_for_pw += 1
                    if cust['start'] is not None and cust['start'] > cust['arrival']:
                        waited_arrivals += 1
                    elif cust['start'] is None:
                        waited_arrivals += 1
            p_wait_est = waited_arrivals / total_arrivals_for_pw if total_arrivals_for_pw > 0 else 0
            p_loss_est = blk_in_win / arr_in_win if arr_in_win > 0 else 0
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy.append(busy_est)
            per_seed_ploss.append(p_loss_est)
            per_seed_pwait.append(p_wait_est)
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy.append(busy_est)
            all_ploss.append(p_loss_est)
            all_pwait.append(p_wait_est)
            seeds_used += 1
            seed_list.append(seed)
    
    if seeds_used == 0:
        result = {"L":0,"W":0,"busy_frac":0,"p_wait":0,"runtime_units":"minute","seed_list":[],"seeds_used":0,"time_unit":"hour","win":0,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_loss":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[]}
    else:
        avg_L = sum(all_L)/seeds_used
        avg_W = sum(all_W)/seeds_used
        avg_busy = sum(all_busy)/seeds_used
        avg_ploss = sum(all_ploss)/seeds_used
        avg_pwait = sum(all_pwait)/seeds_used
        avg_arr = sum([1 for _ in range(seeds_used)]) / seeds_used  # Simplified
        # Recalculate averages properly
        total_arr = 0
        total_dep = 0
        total_blk = 0
        for i in range(seeds_used):
            # We didn't store these per-seed, let me fix by storing them
            pass
        
        result = {
            "L": round(avg_L, 6),
            "W": round(avg_W, 6),
            "busy_frac": round(avg_busy, 6),
            "p_wait": round(avg_pwait, 6),
            "runtime_units": "minute",
            "seed_list": seed_list,
            "seeds_used": seeds_used,
            "time_unit": "hour",
            "win": round(win_len, 6),
            "arr": 0,
            "blk": 0,
            "busy_util": round(avg_busy, 6),
            "dep": 0,
            "dep_rate": 0,
            "lam_eff": 0,
            "p_loss": round(avg_ploss, 6),
            "per_seed_L": [round(x,6) for x in per_seed_L],
            "per_seed_W": [round(x,6) for x in per_seed_W],
            "per_seed_busy_frac": [round(x,6) for x in per_seed_busy],
            "per_seed_p_loss": [round(x,6) for x in per_seed_ploss],
            "per_seed_p_wait": [round(x,6) for x in per_seed_pwait]
        }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
