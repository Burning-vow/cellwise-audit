import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    
    lam_base = 5.0 / 60.0
    mu_base = 1.0 / 6.0
    cv = 3.0
    
    if a.pert == "lam_up": lam_base *= 1.2
    elif a.pert == "mu_up": mu_base *= 1.2
    elif a.pert == "c_up": pass
    
    time_unit = "minute"
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
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
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        current_service_start = None
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        sys_time_sum = 0.0
        busy_time_sum = 0.0
        last_event_t = 0.0
        state_N = 0
        
        events = []
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
            
        add_event(next_arr, 'arr')
        
        while t < horizon:
            if not events: break
            events.sort(key=lambda x: x[0])
            ev_time, ev_type, ev_data = events.pop(0)
            dt = ev_time - t
            if dt > 0:
                if t >= win_start:
                    busy_time_sum += min(state_N, 1) * dt
                    sys_time_sum += state_N * dt
                t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                dur = rng.expovariate(mu_base)
                if len(queue) == 0 and service_end is None:
                    service_end = t + dur
                    current_service_start = t
                    state_N = 1
                    add_event(service_end, 'dep', (t, dur))
                else:
                    queue.append((t, dur))
                    state_N += 1
                next_arr = t + rng.expovariate(lam_base)
                add_event(next_arr, 'arr')
                
            elif ev_type == 'dep':
                dep_count += 1
                arr_t, dur = ev_data
                wait_t = arr_t
                sys_dur = t - arr_t
                if t >= win_start:
                    wait_sum += max(0, t - arr_t - dur) 
                    # Actually W usually includes service? Or just waiting?
                    # Standard Little's Law L = lambda * W where W is time in system.
                    # Let's stick to Time In System for W.
                    pass
                
                if queue:
                    next_cust = queue.pop(0)
                    n_arr_t, n_dur = next_cust
                    service_end = t + n_dur
                    current_service_start = t
                    state_N -= 1 # One left, one enters service immediately, net change 0? No.
                    # State N was including the one being served.
                    # When dep happens, that customer leaves. If queue has someone, they start service.
                    # So N decreases by 1 (the departed one). The new one starts service but was already in N (in queue).
                    # Wait, my state_N logic above:
                    # On Arr: if idle, N becomes 1. If busy, N increases.
                    # On Dep: if queue empty, N becomes 0. If queue non-empty, N stays same?
                    # Let's trace:
                    # Idle: N=0. Arr -> N=1.
                    # Busy: N=1. Arr -> N=2.
                    # Dep with N=2: One leaves. Queue has 1. That 1 starts service. N should become 1.
                    # So on Dep: state_N -= 1.
                    state_N -= 1
                    add_event(service_end, 'dep', (n_arr_t, n_dur))
                else:
                    service_end = None
                    current_service_start = None
                    state_N -= 1
                    
        # Recalculate stats for this seed properly using integration during loop is hard without storing history.
        # Better approach: Store intervals or re-calculate from event log?
        # Simpler: Track cumulative integrals directly in the loop as done above.
        
        # Fixing the integral calculation inside the loop requires careful handling of state changes.
        # Let's restart the simulation logic slightly cleaner for accumulation.
        
        # Re-run logic for this seed to ensure correct accumulation
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        state_N = 0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        cum_sys_time = 0.0
        cum_busy_time = 0.0
        cum_wait_time = 0.0 # Sum of (departure_time - arrival_time - service_duration)? No, W is usually E[T].
        # Problem asks for Average Processing Time W. Usually means Time in System.
        # And L is Avg Number in System.
        # Little's Law: L = lambda_eff * W.
        
        customers_in_window = []
        
        events = [(next_arr, 'arr')]
        
        while t < horizon:
            if not events: break
            events.sort(key=lambda x: x[0])
            ev_time, ev_type = events.pop(0)
            dt = ev_time - t
            if dt > 0:
                if t >= win_start:
                    cum_busy_time += min(state_N, 1) * dt
                    cum_sys_time += state_N * dt
                t = ev_time
            
            if ev_type == 'arr':
                arr_count += 1
                dur = rng.expovariate(mu_base)
                if service_end is None:
                    service_end = t + dur
                    state_N = 1
                    events.append((service_end, 'dep'))
                    # Record arrival for wait calc later?
                    # We need to know when it departs to calculate its specific time in system if we want exact average.
                    # But area method gives us sum of times in system directly via integration.
                    # L = (Integral of N(t) dt) / T_win
                    # W = L / lambda_eff
                    # This avoids tracking individual customer times.
                else:
                    queue.append(dur)
                    state_N += 1
                next_arr = t + rng.expovariate(lam_base)
                events.append((next_arr, 'arr'))
                
            elif ev_type == 'dep':
                dep_count += 1
                if queue:
                    dur = queue.pop(0)
                    service_end = t + dur
                    state_N -= 1
                    events.append((service_end, 'dep'))
                else:
                    service_end = None
                    state_N -= 1
        
        # Calculate metrics for this seed
        if win_len > 0:
            l_val = cum_sys_time / win_len
            busy_val = cum_busy_time / win_len
            # Effective arrival rate in window
            # Need count of arrivals IN WINDOW
            # My previous loop counted all arrivals. Need to filter.
            pass
            
    # The single-pass integration above didn't separate window counts easily.
    # Let's do a more robust simulation recording events.
    
    final_results = {}
    
    # Reset accumulators
    sum_L = 0.0
    sum_W = 0.0
    sum_busy = 0.0
    sum_pl = 0.0
    sum_pw = 0.0
    sum_arr_w = 0
    sum_dep_w = 0
    sum_blk_w = 0
    sum_time_sys_w = 0.0
    sum_time_busy_w = 0.0
    sum_time_wait_w = 0.0 # Not used for W if using Little's law
    
    valid_seeds = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        service_end = None
        state_N = 0
        
        # For window statistics
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_sys_int = 0.0
        w_busy_int = 0.0
        
        # To compute W exactly via Little's Law: W = L / lambda_eff
        # lambda_eff = w_arr / win_len (assuming no blocking loss? M/M/1/K? No, infinite queue here?)
        # "Call center... 1 agent". Usually implies infinite capacity unless specified.
        # If infinite capacity, blk=0.
        # Perturbations don't mention capacity limit. Assume infinite queue.
        # So blk always 0.
        
        events = [(next_arr, 'arr')]
        
        while t < horizon:
            if not events: break
            events.sort(key=lambda x: x[0])
            ev_time, ev_type = events.pop(0)
            dt = ev_time - t
            if dt > 0:
                if t >= win_start:
                    w_busy_int += min(state_N, 1) * dt
                    w_sys_int += state_N * dt
                t = ev_time
            
            if ev_type == 'arr':
                if t >= win_start:
                    w_arr += 1
                dur = rng.expovariate(mu_base)
                if service_end is None:
                    service_end = t + dur
                    state_N = 1
                    events.append((service_end, 'dep'))
                else:
                    queue.append(dur)
                    state_N += 1
                next_arr = t + rng.expovariate(lam_base)
                events.append((next_arr, 'arr'))
                
            elif ev_type == 'dep':
                if t >= win_start:
                    w_dep += 1
                if queue:
                    dur = queue.pop(0)
                    service_end = t + dur
                    state_N -= 1
                    events.append((service_end, 'dep'))
                else:
                    service_end = None
                    state_N -= 1
        
        if win_len <= 0: continue
        
        L_est = w_sys_int / win_len
        busy_est = w_busy_int / win_len
        lam_eff_est = w_arr / win_len
        
        if lam_eff_est > 0:
            W_est = L_est / lam_eff_est
        else:
            W_est = 0.0
            
        # P_wait: Probability an arriving customer waits?
        # In M/M/1, P_wait = rho.
        # Empirical: Fraction of arrivals that found server busy.
        # We didn't track this explicitly.
        # Approximation: busy_util is fraction of time busy.
        # For Poisson arrivals, PASTA property holds. P(arrival finds busy) = P(busy) = busy_util.
        # So p_wait ~ busy_est.
        # p_loss = 0 for infinite queue.
        
        p_loss_est = 0.0
        p_wait_est = busy_est
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        sum_L += L_est
        sum_W += W_est
        sum_busy += busy_est
        sum_pl += p_loss_est
        sum_pw += p_wait_est
        sum_arr_w += w_arr
        sum_dep_w += w_dep
        sum_blk_w += w_blk
        sum_time_sys_w += w_sys_int
        sum_time_busy_w += w_busy_int
        
        valid_seeds += 1

    if valid_seeds == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum_L / valid_seeds
    avg_W = sum_W / valid_seeds
    avg_busy = sum_busy / valid_seeds
    avg_pl = sum_pl / valid_seeds
    avg_pw = sum_pw / valid_seeds
    
    avg_arr_per_seed = sum_arr_w / valid_seeds
    avg_dep_per_seed = sum_dep_w / valid_seeds
    avg_blk_per_seed = sum_blk_w / valid_seeds
    
    dep_rate = (avg_dep_per_seed / win_len) * 60.0 # per hour
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy, 4),
        "runtime_units": "minutes",
        "seed_list": seeds_used[:valid_seeds],
        "seeds_used": valid_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr_per_seed, 4),
        "blk": round(avg_blk_per_seed, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep_per_seed, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(avg_arr_per_seed / win_len, 4),
        "p_loss": round(avg_pl, 4),
        "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
