import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    c = 2
    lam_base = 10.0 / 60.0 # per minute
    mu_base = 1.0 / 6.0   # per minute
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        c = 3
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    horizon_min = args.horizon * 60.0 if args.time_unit == 'hour' else args.horizon
    # The prompt says H is in time_unit. Let's assume time_unit is minute for internal calc simplicity or convert.
    # "time_unit 填你程序内部时间轴的单位". I will use minutes internally.
    # If user passes --horizon 100, and I say time_unit=minute, then horizon is 100 mins.
    # But standard queueing problems often use hours. Let's stick to minutes internally.
    # The argument --horizon H is interpreted as H minutes if time_unit is minute.
    
    total_horizon = args.horizon
    warmup_end = total_horizon * 0.75
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    all_busy_occupied = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        servers_free_at = [0.0] * c
        queue = [] # list of (arrival_time, service_time)
        
        # Statistics accumulators (for the window after warmup)
        area_N = 0.0
        area_busy_servers = 0.0
        area_non_empty = 0.0
        
        count_arrivals_window = 0
        count_departures_window = 0
        count_blocked_window = 0 # In this model, no blocking, but we track it as 0
        count_waiting_on_arrival_window = 0
        
        last_event_time = 0.0
        
        while t < total_horizon:
            # Determine next event time
            min_server_free = min(servers_free_at)
            next_event_t = min(next_arrival, min_server_free)
            
            if next_event_t > total_horizon:
                break
                
            dt = next_event_t - t
            
            # Integrate areas before updating state
            N_current = len(queue) + sum(1 for s in servers_free_at if s <= t)
            busy_count = sum(1 for s in servers_free_at if s <= t)
            
            if t >= warmup_end:
                area_N += N_current * dt
                area_busy_servers += busy_count * dt
                if N_current > 0:
                    area_non_empty += dt
            
            t = next_event_t
            
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                svc_time = rng.expovariate(mu)
                
                # Check if any server is free at time t
                free_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    servers_free_at[free_idx] = t + svc_time
                else:
                    queue.append((t, svc_time))
                
                if t >= warmup_end:
                    count_arrivals_window += 1
                    # p_wait: probability that an arriving customer has to wait
                    # Has to wait if all servers are busy upon arrival
                    if len(queue) > 0 or all(s > t for s in servers_free_at):
                         # Actually, if a server becomes free exactly at t, they don't wait? 
                         # Standard definition: wait time > 0.
                         # If server free at t, wait=0.
                         # We checked free_idx above. If free_idx==-1, they waited.
                         pass
                    
                    # Re-evaluate waiting condition based on logic above
                    # If we appended to queue, they waited.
                    if free_idx == -1:
                        count_waiting_on_arrival_window += 1
                        
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                # Find which server finished
                finished_idx = -1
                for k in range(c):
                    if abs(servers_free_at[k] - t) < 1e-9:
                        finished_idx = k
                        break
                
                if finished_idx != -1:
                    if queue:
                        arr_t, svc_t = queue.pop(0)
                        servers_free_at[finished_idx] = t + svc_t
                    else:
                        servers_free_at[finished_idx] = float('inf') # Idle until next arrival effectively, but we use inf to avoid picking it up as "busy" incorrectly in integration if not careful. 
                        # Better: set to t so it's considered free. But min(servers_free_at) logic needs care.
                        # If idle, server_free_at should be <= current time. Setting to t works.
                        servers_free_at[finished_idx] = t
                
                if t >= warmup_end:
                    count_departures_window += 1

        # Calculate stats for this seed
        win_len = total_horizon - warmup_end
        if win_len <= 0:
            continue
            
        L_est = area_N / win_len
        W_est = L_est / (count_arrivals_window / win_len) if count_arrivals_window > 0 else 0.0
        busy_frac_est = area_busy_servers / (win_len * c)
        p_wait_est = count_waiting_on_arrival_window / count_arrivals_window if count_arrivals_window > 0 else 0.0
        busy_util_est = busy_frac_est # Same definition per prompt
        busy_occupied_est = area_non_empty / win_len # Fraction of time system non-empty? No, prompt says 1-pi0. Pi0 is prob empty. So yes.
        
        dep_rate_est = (count_departures_window / win_len) * 60.0 # per hour
        lam_eff_est = (count_arrivals_window / win_len) * 60.0 # per hour
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arrivals_window)
        all_dep.append(count_departures_window)
        all_blk.append(0)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(0.0)
        all_busy_occupied.append(busy_occupied_est)
        
        seeds_used += 1
        seed_list.append(seed)

    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy_frac = sum(all_busy_frac) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    avg_arr = sum(all_arr) / seeds_used
    avg_dep = sum(all_dep) / seeds_used
    avg_blk = sum(all_blk) / seeds_used
    avg_busy_util = sum(all_busy_util) / seeds_used
    avg_dep_rate = sum(all_dep_rate) / seeds_used
    avg_lam_eff = sum(all_lam_eff) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_busy_occupied = sum(all_busy_occupied) / seeds_used
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "p_wait": round(avg_p_wait, 4),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(total_horizon - warmup_end, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy_util, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(avg_dep_rate, 4),
        "lam_eff": round(avg_lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait],
        "busy_occupied": round(avg_busy_occupied, 4)
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
