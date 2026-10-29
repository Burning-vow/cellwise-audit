import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=1000.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_h = 7.0
    mu_min = 6.0
    if args.pert == 'lam_up': lam_h *= 1.1
    elif args.pert == 'mu_up': mu_min /= 1.1
    
    time_unit = 'minute'
    horizon = args.horizon * 60.0 if time_unit == 'minute' else args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam_h / 60.0)
        queue = []
        service_times = {}
        busy_until = -1.0
        n_in_sys = 0
        
        area_L = 0.0
        area_busy = 0.0
        sum_W = 0.0
        count_dep = 0
        count_arr = 0
        count_blk = 0
        count_wait = 0
        
        last_event_time = 0.0
        
        while t < horizon:
            # Determine next event time
            arr_t = next_arr
            dep_t = busy_until if busy_until > t and not queue else float('inf')
            if queue:
                # If queue exists, departure is at busy_until (if server busy) or immediate? 
                # In M/M/1 with FCFS, if server busy, next dep is busy_until.
                # If server idle but queue non-empty (shouldn't happen in standard sim unless we process immediately), 
                # let's stick to: if server busy, dep_t = busy_until. Else inf.
                pass
            
            if arr_t <= dep_t:
                # Arrival
                t = arr_t
                if t >= win_start:
                    # Integrate before state change
                    dt = t - last_event_time
                    if last_event_time < win_start:
                        dt = t - max(last_event_time, win_start)
                    if dt > 0:
                        area_L += n_in_sys * dt
                        if busy_until > last_event_time: # Server was busy during interval
                            area_busy += dt
                    
                    count_arr += 1
                
                # Generate service time now
                svc = rng.expovariate(1.0 / mu_min)
                
                if n_in_sys == 0:
                    # Start service immediately
                    busy_until = t + svc
                    n_in_sys = 1
                    service_times[busy_until] = {'start': t, 'end': busy_until}
                else:
                    # Join queue
                    n_in_sys += 1
                    queue.append({'arrival': t, 'svc': svc})
                
                # Next arrival
                next_arr = t + rng.expovariate(lam_h / 60.0)
                last_event_time = t
                
            else:
                # Departure
                t = dep_t
                if t >= win_start:
                    dt = t - last_event_time
                    if last_event_time < win_start:
                        dt = t - max(last_event_time, win_start)
                    if dt > 0:
                        area_L += n_in_sys * dt
                        if busy_until > last_event_time:
                            area_busy += dt
                
                # Process departure
                # Find the customer leaving
                # The one who started service earlier
                # We need to track who is in service.
                # Simplified: pop from queue logic needs care.
                # Let's restructure slightly for clarity in single loop.
                
                # Actually, let's use a simpler approach:
                # State: server_status (idle/busy), end_time, queue list.
                # On arrival: if idle, start service. Else enqueue.
                # On departure: complete current service. If queue not empty, start next. Else idle.
                
                # Need to know arrival time of departing customer for W.
                # Store (arrival_time, service_duration) in a variable for current service.
                
                # Refactoring inner loop for correctness:
                break # Exit this block to rewrite properly below
        
        # Re-implementing simulation loop correctly
        t = 0.0
        next_arr = rng.expovariate(lam_h / 60.0)
        queue = [] # List of dicts: {'arr': t, 'svc': dur}
        curr_cust = None # Dict: {'arr': t, 'svc': dur, 'start': t, 'end': t}
        n_in_sys = 0
        
        area_L = 0.0
        area_busy = 0.0
        sum_W = 0.0
        count_dep = 0
        count_arr = 0
        count_blk = 0
        count_wait = 0
        last_evt = 0.0
        
        while t < horizon:
            arr_t = next_arr
            dep_t = curr_cust['end'] if curr_cust else float('inf')
            
            if arr_t <= dep_t:
                t = arr_t
                # Integrate
                dt = t - last_evt
                if last_evt < win_start:
                    dt = t - max(last_evt, win_start)
                if dt > 0:
                    area_L += n_in_sys * dt
                    if curr_cust:
                        area_busy += dt
                
                if t >= win_start:
                    count_arr += 1
                
                svc = rng.expovariate(1.0 / mu_min)
                
                if curr_cust is None:
                    curr_cust = {'arr': t, 'svc': svc, 'start': t, 'end': t + svc}
                    n_in_sys = 1
                else:
                    queue.append({'arr': t, 'svc': svc})
                    n_in_sys += 1
                
                next_arr = t + rng.expovariate(lam_h / 60.0)
                last_evt = t
                
            else:
                t = dep_t
                dt = t - last_evt
                if last_evt < win_start:
                    dt = t - max(last_evt, win_start)
                if dt > 0:
                    area_L += n_in_sys * dt
                    if curr_cust:
                        area_busy += dt
                
                # Complete service
                w = t - curr_cust['arr']
                if t >= win_start:
                    sum_W += w
                    count_dep += 1
                    if curr_cust['start'] > curr_cust['arr']:
                        count_wait += 1
                
                n_in_sys -= 1
                curr_cust = None
                
                if queue:
                    nxt = queue.pop(0)
                    curr_cust = {'arr': nxt['arr'], 'svc': nxt['svc'], 'start': t, 'end': t + nxt['svc']}
                    n_in_sys += 1 # Wait, n_in_sys decreased by 1, then increased by 1. Net 0 change in system count?
                    # No: Customer left system (-1). New customer enters service (+0 net change in system count relative to queue->service transition).
                    # System count includes those in queue AND in service.
                    # Before dep: 1 in service, K in queue. Total 1+K.
                    # After dep: 0 in service, K-1 in queue. Then start new: 1 in service, K-1 in queue. Total 1+(K-1) = K.
                    # So n_in_sys should decrease by 1.
                    # My code: n_in_sys -= 1 (now K). Then if queue: curr_cust set, n_in_sys += 1 (now K+1?? No.)
                    # Let's trace:
                    # Initial: n=1 (curr), q=[c2]. Total 2.
                    # Dep c1: n becomes 0. q=[c2].
                    # Start c2: curr=c2. n becomes 1. q=[]. Total 1. Correct.
                    # Code: n_in_sys -= 1 -> 0. Then if queue: n_in_sys += 1 -> 1. Correct.
                    pass
                
                last_evt = t
        
        # Final integration up to horizon
        dt = horizon - last_evt
        if last_evt < win_start:
            dt = horizon - max(last_evt, win_start)
        if dt > 0:
            area_L += n_in_sys * dt
            if curr_cust:
                area_busy += dt
        
        win_len = horizon - win_start
        L_est = area_L / win_len if win_len > 0 else 0
        W_est = sum_W / count_dep if count_dep > 0 else 0
        bf_est = area_busy / win_len if win_len > 0 else 0
        pl_est = 0.0 # No blocking in M/M/1 infinite buffer
        pw_est = count_wait / count_dep if count_dep > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        seed_list.append(s)
        
        total_arr += count_arr
        total_dep += count_dep
        total_blk += count_blk
    
    seeds_used = len(seed_list)
    avg_L = sum(per_seed_L) / seeds_used
    avg_W = sum(per_seed_W) / seeds_used
    avg_bf = sum(per_seed_busy_frac) / seeds_used
    avg_pl = sum(per_seed_p_loss) / seeds_used
    avg_pw = sum(per_seed_p_wait) / seeds_used
    
    avg_arr = total_arr / seeds_used
    avg_dep = total_dep / seeds_used
    avg_blk = total_blk / seeds_used
    
    dep_rate = (avg_dep / win_len) * 60.0 if win_len > 0 else 0
    lam_eff = dep_rate
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "p_wait": round(avg_pw, 4),
        "runtime_units": "minutes",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_pl, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
