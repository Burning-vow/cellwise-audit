import sys, json, random, math
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 10; horizon = 100.0; seed_start = 42; pert = "none"
    i = 0
    while i < len(args):
        if args[i] == "--seeds": seeds_n = int(args[i+1]); i += 2
        elif args[i] == "--horizon": horizon = float(args[i+1]); i += 2
        elif args[i] == "--seed-start": seed_start = int(args[i+1]); i += 2
        elif args[i] == "--pert": pert = args[i+1]; i += 2
        else: i += 1
    
    lam_base = 4.0 # per hour
    mu_base = 10.0 # per hour (6 min mean)
    
    if pert == "lam_up": lam = lam_base * 1.1
    elif pert == "mu_up": mu = mu_base * 1.1
    elif pert == "c_up": lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    time_unit = "hour"
    win = horizon * 0.75
    warmup_end = horizon * 0.25
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_wait = []; all_p_loss = []
    all_arr = []; all_dep = []; all_blk = []; all_busy_util = []; all_dep_rate = []
    all_lam_eff = []; all_busy_occupied = []
    
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []; per_seed_p_loss = []; per_seed_p_wait = []
    seed_list = []
    
    for s_idx in range(seeds_n):
        seed_val = seed_start + s_idx
        rng = random.Random(seed_val)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = deque()
        server_free_time = -1.0
        n_in_sys = 0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        area_L = 0.0
        area_busy = 0.0
        area_wait = 0.0
        total_stay_time = 0.0
        count_stay = 0
        
        last_event_t = 0.0
        
        events = []
        # Pre-generate arrivals and services? No, standard DES loop.
        # We need to track state changes for integration.
        
        # Initial state
        # If we start at t=0 with empty system, first arrival is next_arr.
        
        while True:
            # Determine next event time
            t_arr = next_arr
            t_dep = server_free_time if server_free_time > t else float('inf')
            
            if not queue:
                t_dep = float('inf')
                
            t_next = min(t_arr, t_dep)
            
            if t_next >= horizon:
                break
            
            dt = t_next - last_event_t
            if last_event_t >= warmup_end:
                area_L += n_in_sys * dt
                area_busy += (1 if n_in_sys > 0 else 0) * dt
                # Wait area: number of people waiting (queue length)
                q_len = max(0, n_in_sys - 1)
                area_wait += q_len * dt
                
            t = t_next
            last_event_t = t
            
            if t == t_arr:
                # Arrival
                service_time = rng.expovariate(mu)
                customer = {'arrival': t, 'service': service_time}
                
                if t >= warmup_end:
                    arr_count_win += 1
                
                if n_in_sys == 0:
                    # Start service immediately
                    server_free_time = t + service_time
                    n_in_sys = 1
                else:
                    # Join queue
                    queue.append(customer)
                    n_in_sys += 1
                    
                next_arr = t + rng.expovariate(lam)
                
            elif t == t_dep:
                # Departure
                if queue:
                    next_cust = queue.popleft()
                    server_free_time = t + next_cust['service']
                    n_in_sys -= 1
                else:
                    server_free_time = float('inf')
                    n_in_sys -= 1
                
                if t >= warmup_end:
                    dep_count_win += 1
                    # Calculate stay time for the departing customer
                    # The one who just finished was the head of queue or single server user
                    # We need to know who it was. 
                    # In M/M/1, FIFO. The one leaving is the one that started service at server_free_time - service_duration?
                    # Better: store departure info or calculate from arrival.
                    # Since we popped from queue or used server directly, we lost the specific object reference for the one leaving if we didn't save it.
                    # Let's fix logic: when starting service, we know the customer. When ending, we know the customer.
                    pass 

        # Re-run with better tracking for W calculation inside loop is complex without storing history.
        # Alternative: Track sum of stay times for those who depart within window.
        # But we need to associate arrival time with departure.
        
        # Let's restart the simulation loop with proper bookkeeping for W.
        
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = deque()
        server_free_time = -1.0
        n_in_sys = 0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        area_L = 0.0
        area_busy = 0.0
        area_wait = 0.0
        sum_stay = 0.0
        count_stay = 0
        
        last_event_t = 0.0
        
        # To handle infinite horizon properly, we stop when t >= horizon
        # But we must process events up to horizon.
        
        while True:
            t_arr = next_arr
            t_dep = server_free_time if server_free_time > t else float('inf')
            if not queue and server_free_time <= t: t_dep = float('inf')
            
            t_next = min(t_arr, t_dep)
            
            if t_next >= horizon:
                # Integrate remaining time until horizon
                dt = horizon - last_event_t
                if last_event_t >= warmup_end:
                    area_L += n_in_sys * dt
                    area_busy += (1 if n_in_sys > 0 else 0) * dt
                    q_len = max(0, n_in_sys - 1)
                    area_wait += q_len * dt
                break
            
            dt = t_next - last_event_t
            if last_event_t >= warmup_end:
                area_L += n_in_sys * dt
                area_busy += (1 if n_in_sys > 0 else 0) * dt
                q_len = max(0, n_in_sys - 1)
                area_wait += q_len * dt
                
            t = t_next
            last_event_t = t
            
            if abs(t - t_arr) < 1e-9:
                service_time = rng.expovariate(mu)
                cust = {'arr': t, 'svc': service_time}
                
                if t >= warmup_end:
                    arr_count_win += 1
                
                if n_in_sys == 0:
                    server_free_time = t + service_time
                    n_in_sys = 1
                    # This customer starts service now. Will depart later.
                    # We don't add to queue.
                else:
                    queue.append(cust)
                    n_in_sys += 1
                    
                next_arr = t + rng.expovariate(lam)
                
            elif abs(t - t_dep) < 1e-9:
                # Who is departing?
                # If queue was empty before this event, the server was busy with someone who arrived earlier.
                # We need to track the current serving customer's arrival time.
                # Let's maintain a variable 'current_serving_arr'
                pass

        # Need to refactor to track current serving customer arrival time.
        
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = deque()
        server_free_time = -1.0
        current_serving_arr = None
        n_in_sys = 0
        
        arr_count_win = 0
        dep_count_win = 0
        blk_count_win = 0
        
        area_L = 0.0
        area_busy = 0.0
        area_wait = 0.0
        sum_stay = 0.0
        count_stay = 0
        
        last_event_t = 0.0
        
        while True:
            t_arr = next_arr
            t_dep = server_free_time if server_free_time > t else float('inf')
            if n_in_sys == 0: t_dep = float('inf')
            
            t_next = min(t_arr, t_dep)
            
            if t_next >= horizon:
                dt = horizon - last_event_t
                if last_event_t >= warmup_end:
                    area_L += n_in_sys * dt
                    area_busy += (1 if n_in_sys > 0 else 0) * dt
                    q_len = max(0, n_in_sys - 1)
                    area_wait += q_len * dt
                break
            
            dt = t_next - last_event_t
            if last_event_t >= warmup_end:
                area_L += n_in_sys * dt
                area_busy += (1 if n_in_sys > 0 else 0) * dt
                q_len = max(0, n_in_sys - 1)
                area_wait += q_len * dt
                
            t = t_next
            last_event_t = t
            
            if abs(t - t_arr) < 1e-9:
                service_time = rng.expovariate(mu)
                cust = {'arr': t, 'svc': service_time}
                
                if t >= warmup_end:
                    arr_count_win += 1
                
                if n_in_sys == 0:
                    server_free_time = t + service_time
                    current_serving_arr = t
                    n_in_sys = 1
                else:
                    queue.append(cust)
                    n_in_sys += 1
                    
                next_arr = t + rng.expovariate(lam)
                
            elif abs(t - t_dep) < 1e-9:
                # Departure
                if t >= warmup_end:
                    dep_count_win += 1
                    if current_serving_arr is not None:
                        stay = t - current_serving_arr
                        sum_stay += stay
                        count_stay += 1
                
                if queue:
                    next_cust = queue.popleft()
                    server_free_time = t + next_cust['svc']
                    current_serving_arr = next_cust['arr']
                    n_in_sys -= 1
                else:
                    server_free_time = float('inf')
                    current_serving_arr = None
                    n_in_sys -= 1

        L_est = area_L / win if win > 0 else 0
        W_est = sum_stay / count_stay if count_stay > 0 else 0
        busy_frac_est = area_busy / win if win > 0 else 0
        p_wait_est = area_wait / win if win > 0 else 0 # Fraction of time someone is waiting? Or prob of wait?
        # p_wait usually means probability an arriving customer waits.
        # In M/M/1, P(wait) = rho.
        # Empirical: Count arrivals where n_in_sys > 0 at arrival time.
        
        # Recalculate p_wait empirically
        # We missed counting arrivals that waited.
        # Let's do a quick re-sim or modify above. Modifying above is cleaner but I'm running out of lines.
        # I will assume p_wait = busy_frac for M/M/1 approximation or recalculate.
        # Actually, let's just use the formula derived from counts if possible, or re-run.
        # Given constraints, I'll estimate p_wait as fraction of arrivals that found server busy.
        
        # Re-running for p_wait count
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = deque()
        server_free_time = -1.0
        n_in_sys = 0
        wait_count = 0
        arr_total_win = 0
        
        while True:
            t_arr = next_arr
            t_dep = server_free_time if server_free_time > t else float('inf')
            if n_in_sys == 0: t_dep = float('inf')
            t_next = min(t_arr, t_dep)
            if t_next >= horizon: break
            t = t_next
            
            if abs(t - t_arr) < 1e-9:
                service_time = rng.expovariate(mu)
                if t >= warmup_end:
                    arr_total_win += 1
                    if n_in_sys > 0:
                        wait_count += 1
                
                if n_in_sys == 0:
                    server_free_time = t + service_time
                    n_in_sys = 1
                else:
                    queue.append({'svc': service_time})
                    n_in_sys += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if queue:
                    nc = queue.popleft()
                    server_free_time = t + nc['svc']
                    n_in_sys -= 1
                else:
                    server_free_time = float('inf')
                    n_in_sys -= 1
        
        p_wait_emp = wait_count / arr_total_win if arr_total_win > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_wait.append(p_wait_emp)
        per_seed_p_loss.append(0.0) # No loss in M/M/1
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_emp)
        all_p_loss.append(0.0)
        all_arr.append(arr_count_win)
        all_dep.append(dep_count_win)
        all_blk.append(0)
        all_busy_util.append(busy_frac_est)
        all_dep_rate.append(dep_count_win / win if win > 0 else 0)
        all_lam_eff.append(arr_count_win / win if win > 0 else 0)
        all_busy_occupied.append(busy_frac_est)
        seed_list.append(seed_val)

    avg_L = sum(all_L)/len(all_L)
    avg_W = sum(all_W)/len(all_W)
    avg_busy = sum(all_busy_frac)/len(all_busy_frac)
    avg_p_wait = sum(all_p_wait)/len(all_p_wait)
    avg_p_loss = sum(all_p_loss)/len(all_p_loss)
    avg_arr = sum(all_arr)/len(all_arr)
    avg_dep = sum(all_dep)/len(all_dep)
    avg_blk = sum(all_blk)/len(all_blk)
    avg_busy_util = sum(all_busy_util)/len(all_busy_util)
    avg_dep_rate = sum(all_dep_rate)/len(all_dep_rate)
    avg_lam_eff = sum(all_lam_eff)/len(all_lam_eff)
    avg_busy_occ = sum(all_busy_occupied)/len(all_busy_occupied)

    res = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "count",
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait],
        "busy_occupied": round(avg_busy_occ, 4)
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
