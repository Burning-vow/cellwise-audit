import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    N = a.seeds; H = a.horizon; S = a.seed_start; pert = a.pert
    lam_base = 7.0; mu_base = 10.0 # per hour
    if pert == "lam_up": lam_base *= 1.2
    elif pert == "mu_up": mu_base *= 1.2
    elif pert == "c_up": pass
    
    time_unit = "hour"
    win = H * 0.75
    warmup = H * 0.25
    
    all_L = []; all_W = []; all_busy_frac = []; all_p_wait = []
    all_arr = []; all_dep = []; all_blk = []; all_p_loss = []
    all_busy_util = []; all_busy_occupied = []
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        n_in_sys = 0
        busy = False
        
        # For area integration
        last_event_time = 0.0
        area_n = 0.0
        area_busy = 0.0
        
        # Stats within window
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0 # total waiting time (queueing time) for those who waited? No, W is system time.
        # We need sum of system times for customers that departed in the window.
        # But standard DES accumulates area for L. For W, we can use Little's Law or track individual times.
        # Let's track individual departure times and arrival times to compute exact W for departures in window.
        # However, area method for L is robust. For W, let's accumulate sum of (dep - arr) for each customer departing in window.
        
        cust_times = [] # list of (arr_t, dep_t) for customers fully inside window? 
        # Better: just accumulate sum_w and count_w for departures in window.
        sum_w_window = 0.0
        count_w_window = 0
        
        # To handle warmup correctly for area-based stats:
        # We integrate from warmup to H.
        
        events = []
        # Generate initial events
        if next_arr < H: events.append((next_arr, 'A'))
        if next_dep < H: events.append((next_dep, 'D'))
        
        # We need a priority queue or sorted list. Since it's M/M/1, we can simulate step by step.
        # Simpler loop:
        while True:
            # Find next event
            min_t = float('inf')
            ev_type = None
            
            if next_arr < min_t:
                min_t = next_arr
                ev_type = 'A'
            if next_dep < min_t:
                min_t = next_dep
                ev_type = 'D'
                
            if min_t > H: break
            
            # Integrate areas up to min_t
            dt = min_t - last_event_time
            if last_event_time >= warmup:
                # Only integrate if the interval overlaps with [warmup, H]
                start_int = max(last_event_time, warmup)
                end_int = min(min_t, H)
                if end_int > start_int:
                    int_dt = end_int - start_int
                    area_n += n_in_sys * int_dt
                    if busy: area_busy += int_dt
            
            last_event_time = min_t
            
            if ev_type == 'A':
                # Arrival
                if n_in_sys == 0:
                    # Start service immediately
                    svc_time = rng.expovariate(mu_base)
                    next_dep = min_t + svc_time
                    busy = True
                    n_in_sys = 1
                    # Store arrival time for this customer
                    # We need to know when they leave to add to sum_w.
                    # Use a simple queue for arrival times
                    q_arr = [min_t]
                else:
                    # Join queue
                    n_in_sys += 1
                    q_arr.append(min_t)
                
                # Schedule next arrival
                next_arr = min_t + rng.expovariate(lam_base)
                
                # Check if this arrival is in window for counting
                if min_t >= warmup:
                    arr_count += 1
                    
            elif ev_type == 'D':
                # Departure
                # The customer leaving is the one at front of queue
                arr_t = q_arr.pop(0)
                w_time = min_t - arr_t
                
                if min_t >= warmup:
                    dep_count += 1
                    sum_w_window += w_time
                    count_w_window += 1
                
                if len(q_arr) > 0:
                    # Next customer starts service
                    svc_time = rng.expovariate(mu_base)
                    next_dep = min_t + svc_time
                    n_in_sys -= 1
                    # Busy remains true
                else:
                    # System empty
                    n_in_sys = 0
                    busy = False
                    next_dep = float('inf')
            
            # Update next event candidates
            # Re-evaluate min_t logic in next iteration
            
        # End simulation for this seed
        
        # Calculate metrics for this seed
        # L = Area / Window Length
        L_seed = area_n / win if win > 0 else 0.0
        # W = Sum(W_i) / Count(Departures in window)
        W_seed = sum_w_window / count_w_window if count_w_window > 0 else 0.0
        # Busy Fraction = Area Busy / Window Length
        busy_frac_seed = area_busy / win if win > 0 else 0.0
        # P(wait) : Probability an arriving customer has to wait.
        # In M/M/1, P(wait) = rho. But empirically:
        # Count arrivals in window where n_in_sys > 0 at arrival instant.
        # We didn't track this explicitly during loop easily without extra var.
        # Let's re-run or track properly. 
        # Actually, simpler: P_wait = fraction of arrivals in window that found server busy.
        # We need to count arrivals in window where n_in_sys_before_arrival > 0.
        # Let's modify loop to track this.
        
        # Refactoring loop slightly for p_wait tracking
        # I will rewrite the inner loop part in my head to ensure correctness.
        # ...
        # Given constraints, I'll implement a cleaner version below.

    # Clean implementation follows
    results = []
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        next_dep = float('inf')
        n_in_sys = 0
        busy = False
        q_arr = []
        
        last_ev_t = 0.0
        area_n = 0.0
        area_busy = 0.0
        
        arr_win = 0
        dep_win = 0
        blk_win = 0 # M/M/1 no blocking usually, unless finite capacity. Problem says stable, infinite buffer implied.
        sum_w_win = 0.0
        cnt_w_win = 0
        wait_arr_win = 0 # Arrivals that had to wait
        
        while True:
            min_t = float('inf')
            ev = None
            if next_arr < min_t: min_t = next_arr; ev = 'A'
            if next_dep < min_t: min_t = next_dep; ev = 'D'
            if min_t > H: break
            
            dt = min_t - last_ev_t
            s_int = max(last_ev_t, warmup)
            e_int = min(min_t, H)
            if e_int > s_int:
                d_int = e_int - s_int
                area_n += n_in_sys * d_int
                if busy: area_busy += d_int
            
            last_ev_t = min_t
            
            if ev == 'A':
                if n_in_sys == 0:
                    st = rng.expovariate(mu_base)
                    next_dep = min_t + st
                    busy = True
                    n_in_sys = 1
                    q_arr = [min_t]
                else:
                    n_in_sys += 1
                    q_arr.append(min_t)
                    if min_t >= warmup:
                        wait_arr_win += 1
                
                next_arr = min_t + rng.expovariate(lam_base)
                if min_t >= warmup:
                    arr_win += 1
                    
            elif ev == 'D':
                at = q_arr.pop(0)
                wt = min_t - at
                if min_t >= warmup:
                    dep_win += 1
                    sum_w_win += wt
                    cnt_w_win += 1
                
                if q_arr:
                    st = rng.expovariate(mu_base)
                    next_dep = min_t + st
                    n_in_sys -= 1
                else:
                    n_in_sys = 0
                    busy = False
                    next_dep = float('inf')
                    
        L_s = area_n / win
        W_s = sum_w_win / cnt_w_win if cnt_w_win else 0.0
        bf_s = area_busy / win
        pw_s = wait_arr_win / arr_win if arr_win else 0.0
        pl_s = 0.0 # No loss
        
        results.append({
            'L': L_s, 'W': W_s, 'busy_frac': bf_s, 'p_wait': pw_s,
            'arr': arr_win, 'dep': dep_win, 'blk': blk_win, 'p_loss': pl_s,
            'busy_util': bf_s, 'busy_occupied': bf_s # E[min(N,1)]/1 is same as 1-pi0 for c=1
        })
        
    avg_L = sum(r['L'] for r in results)/N
    avg_W = sum(r['W'] for r in results)/N
    avg_bf = sum(r['busy_frac'] for r in results)/N
    avg_pw = sum(r['p_wait'] for r in results)/N
    avg_arr = sum(r['arr'] for r in results)/N
    avg_dep = sum(r['dep'] for r in results)/N
    avg_blk = sum(r['blk'] for r in results)/N
    avg_pl = sum(r['p_loss'] for r in results)/N
    avg_bu = sum(r['busy_util'] for r in results)/N
    avg_bo = sum(r['busy_occupied'] for r in results)/N
    
    dep_rate = avg_dep / win * 60.0 # per hour? Wait, time_unit is hour. So dep/win is per hour.
    # If time_unit is hour, rate is already per hour.
    dep_rate_val = avg_dep / win 
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_bf, 4),
        "p_wait": round(avg_pw, 4),
        "runtime_units": "hour",
        "seed_list": [S+i for i in range(N)],
        "seeds_used": N,
        "time_unit": "hour",
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_bu, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate_val, 4),
        "lam_eff": round(avg_arr / win, 4),
        "p_loss": round(avg_pl, 4),
        "per_seed_L": [round(r['L'], 4) for r in results],
        "per_seed_W": [round(r['W'], 4) for r in results],
        "per_seed_busy_frac": [round(r['busy_frac'], 4) for r in results],
        "per_seed_p_loss": [round(r['p_loss'], 4) for r in results],
        "per_seed_p_wait": [round(r['p_wait'], 4) for r in results]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
