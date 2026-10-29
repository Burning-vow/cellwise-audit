import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base = 4.0, 12.0
    if a.pert == "lam_up": lam_base *= 1.1
    elif a.pert == "mu_up": mu_base *= 1.1
    elif a.pert == "c_up": pass
    seeds_used = []
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0.0, 0.0, 0.0
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        t = 0.0; H = a.horizon; warmup = 0.25 * H
        n_in_sys = 0; busy_time = 0.0; last_event_t = 0.0
        arr_count = 0; dep_count = 0; blk_count = 0
        wait_sum = 0.0; sys_time_sum = 0.0
        next_arr = rng.expovariate(lam_base)
        customers = []
        while True:
            next_dep = None
            if customers:
                next_dep = customers[0][1]
            ev_t = min(next_arr, next_dep if next_dep is not None else float('inf'))
            if ev_t > H: break
            dt = ev_t - last_event_t
            if t >= warmup:
                busy_time += dt * (1 if n_in_sys > 0 else 0)
                sys_time_sum += dt * n_in_sys
            t = ev_t; last_event_t = t
            if abs(t - next_arr) < 1e-9:
                svc = rng.expovariate(mu_base)
                if n_in_sys == 0:
                    start_t = t; end_t = t + svc
                    customers.append((start_t, end_t))
                    n_in_sys += 1
                else:
                    start_t = t + sum(c[1]-c[0] for c in customers) # Simplified queue logic for single server
                    # Correct M/M/1 queueing: just append to list, service starts when previous ends
                    # Actually simpler: maintain queue of arrival times and service durations
                    # Let's restart the simulation loop with a cleaner state machine
                    pass 
                # The above inline logic is getting messy. Let's rewrite the core loop cleanly inside this function scope.
                # Since I cannot define classes or refactor into multiple functions easily under constraints, 
                # I will implement a standard event-driven loop here.
                
                # Resetting approach for clarity within one block:
                # State: queue (list of (arrival_time, service_duration)), current_service_end_time
                # This requires re-initializing variables properly.
                
                # Re-implementing the inner loop correctly:
                break # Break out to use a fresh clean implementation below
            elif next_dep is not None and abs(t - next_dep) < 1e-9:
                pass
        
    # Clean Implementation Start
    results = {"L":0,"W":0,"busy_frac":0,"p_wait":0,"runtime_units":"hour","seed_list":[],"seeds_used":0,"time_unit":"hour","win":a.horizon}
    
    all_L, all_W, all_bf, all_pl, all_pw = [], [], [], [], []
    all_arr, all_dep, all_blk = [], [], []
    
    for i in range(a.seeds):
        seed_val = a.seed_start + i
        rng = random.Random(seed_val)
        horizon = a.horizon
        warmup = 0.25 * horizon
        
        # Simulation State
        t = 0.0
        queue = [] # List of (arrival_time, service_duration)
        service_end_time = 0.0
        is_server_busy = False
        
        # Statistics accumulators (for area integration)
        area_n = 0.0
        area_busy = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0 # Total waiting time (queue time)
        sum_s = 0.0 # Total system time (wait + service)
        
        # Event generation
        next_arrival = rng.expovariate(lam_base)
        
        last_stat_t = 0.0
        
        while t < horizon:
            # Determine next event time
            next_departure = service_end_time if is_server_busy else float('inf')
            next_event = min(next_arrival, next_departure)
            
            if next_event > horizon:
                next_event = horizon
                
            dt = next_event - t
            
            # Integrate statistics if past warmup
            if t >= warmup:
                n_current = len(queue) + (1 if is_server_busy else 0)
                area_n += dt * n_current
                if is_server_busy:
                    area_busy += dt
            
            t = next_event
            
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                svc_dur = rng.expovariate(mu_base)
                if t >= warmup:
                    count_arr += 1
                
                if not is_server_busy:
                    is_server_busy = True
                    service_end_time = t + svc_dur
                    # Wait time is 0
                    if t >= warmup:
                        sum_w += 0
                        sum_s += svc_dur
                else:
                    queue.append((t, svc_dur))
                    # Wait time calculated upon departure
                next_arrival = t + rng.expovariate(lam_base)
                
            elif abs(t - next_departure) < 1e-9:
                # Departure
                if t >= warmup:
                    count_dep += 1
                
                if queue:
                    arr_t, svc_dur = queue.pop(0)
                    wait_time = t - arr_t
                    sys_time = wait_time + svc_dur
                    if t >= warmup:
                        sum_w += wait_time
                        sum_s += sys_time
                    service_end_time = t + svc_dur
                    # Server remains busy
                else:
                    is_server_busy = False
                    service_end_time = 0.0
                    
        # Calculate metrics for this seed
        win_len = horizon - warmup
        if win_len <= 0: win_len = 1e-9
        
        L_est = area_n / win_len
        W_est = sum_s / count_dep if count_dep > 0 else 0
        bf_est = area_busy / win_len
        pl_est = 0.0 # No blocking in infinite buffer M/M/1
        pw_est = sum_w / count_dep if count_dep > 0 else 0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_bf.append(bf_est)
        all_pl.append(pl_est)
        all_pw.append(pw_est)
        all_arr.append(count_arr)
        all_dep.append(count_dep)
        all_blk.append(count_blk)
        
    seeds_used = a.seeds
    avg_L = sum(all_L)/seeds_used
    avg_W = sum(all_W)/seeds_used
    avg_bf = sum(all_bf)/seeds_used
    avg_pl = sum(all_pl)/seeds_used
    avg_pw = sum(all_pw)/seeds_used
    avg_arr = sum(all_arr)/seeds_used
    avg_dep = sum(all_dep)/seeds_used
    avg_blk = sum(all_blk)/seeds_used
    
    dep_rate = avg_dep / (a.horizon - 0.25*a.horizon) * 60.0 # Convert hours to minutes? No, time_unit is hour. Rate per hour.
    # Wait, dep_rate is "个/每小时". Horizon is in hours. Window is in hours.
    # So dep_rate = avg_dep / window_length_hours
    
    window_len = a.horizon * 0.75
    dep_rate_val = avg_dep / window_len if window_len > 0 else 0
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "hour",
        "seed_list": [a.seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(window_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bf, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate_val, 6),
        "lam_eff": round(avg_arr / window_len, 6) if window_len > 0 else 0,
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_bf],
        "per_seed_p_loss": [round(x, 6) for x in all_pl],
        "per_seed_p_wait": [round(x, 6) for x in all_pw]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
