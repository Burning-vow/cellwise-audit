import argparse, json, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 10.0
    mu_base = 6.0
    c = 2
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.2
    elif a.pert == 'mu_up':
        mu = mu_base * 1.2
    else:
        lam = lam_base
        mu = mu_base
        
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
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        servers_free_at = [0.0] * c
        n_in_sys = 0
        area_n = 0.0
        last_event_time = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        service_sum = 0.0
        busy_min_sum = 0.0
        p_wait_hits = 0
        p_wait_total = 0
        
        while True:
            # Determine next event time
            min_server_free = min(servers_free_at) if any(f > t for f in servers_free_at) else float('inf')
            next_dep = min_server_free if min_server_free > t else float('inf')
            
            next_ev = min(next_arr, next_dep)
            if next_ev > horizon:
                break
                
            dt = next_ev - t
            if t >= win_start:
                area_n += n_in_sys * dt
                # Calculate busy fraction contribution over interval
                active_servers = sum(1 for f in servers_free_at if f > t)
                busy_min_sum += min(active_servers, c) * dt
            
            t = next_ev
            
            if abs(t - next_arr) < 1e-9:
                # Arrival
                arr_count += 1
                if t >= win_start:
                    p_wait_total += 1
                    if len(queue) > 0 or any(f > t for f in servers_free_at):
                        p_wait_hits += 1
                
                # Check capacity (infinite queue assumed as standard M/M/c/K with K->inf, but problem says "bank branch", usually infinite queue unless specified loss system. However, output asks for p_loss and blk. Standard M/M/c has no loss. Let's assume finite capacity? No, "waiting" implies queue. But p_loss is requested. If it's pure M/M/c, p_loss=0. Let's stick to M/M/c with infinite queue, so blk=0, p_loss=0.)
                # Actually, the prompt mentions "blk" and "p_loss". In M/M/c, these are 0.
                
                # Generate service time now
                svc_time = rng.expovariate(mu)
                
                # Find free server
                free_idx = -1
                for j in range(c):
                    if servers_free_at[j] <= t:
                        free_idx = j
                        break
                
                if free_idx != -1:
                    servers_free_at[free_idx] = t + svc_time
                    n_in_sys += 1
                    wait_sum += 0.0
                    service_sum += svc_time
                else:
                    queue.append((t, svc_time))
                    n_in_sys += 1
                    # Wait time will be calculated upon departure from queue start of service? 
                    # W is waiting + service. We accumulate total time in system per customer.
                    # Easier: track entry time and exit time.
                    # Let's change strategy: store arrival time in queue. When service starts, we know wait.
                    # But we need total time in system.
                    # Let's just record arrival time. When they leave, add (leave_time - arrival_time) to sum.
                    pass
                
                next_arr = t + rng.expovariate(lam)
                
            elif abs(t - next_dep) < 1e-9:
                # Departure
                dep_count += 1
                # Find which server finished
                finished_idx = -1
                for j in range(c):
                    if abs(servers_free_at[j] - t) < 1e-9:
                        finished_idx = j
                        break
                
                if finished_idx != -1:
                    # Customer leaves
                    # Need to know who left. The one at that server.
                    # We didn't store ID. We stored svc_time in queue only if waiting.
                    # This implementation is getting messy because I didn't link customers to servers properly.
                    
                    # Refactor logic slightly within loop constraints:
                    # Queue stores (arrival_time, service_time).
                    # Servers store (start_time, end_time) implicitly via free_at.
                    # When a server becomes free, if queue is not empty, pop front, set new free_at.
                    # The customer leaving is the one whose service ended.
                    
                    # How to calculate W? Sum of (departure_time - arrival_time) for all customers.
                    # We need to associate arrival time with the service completion.
                    
                    # Let's restart the inner loop logic mentally to ensure correctness without classes.
                    # State:
                    # t: current time
                    # queue: list of (arrival_time, service_duration)
                    # servers: list of end_times (float). If inf, idle.
                    # stats accumulators.
                    
                    # Event: Departure at time t.
                    # Identify server j with end_time == t.
                    # Who was served there? We don't have their arrival time stored on the server.
                    # Fix: Store (arrival_time, service_duration) on the server when starting service.
                    # Or simpler: When a customer enters service, we know their arrival time.
                    # Let's use a parallel array for server state: server_cust_info[j] = (arrival_time, service_duration) or None.
                    
                    # Since I can't refactor easily mid-thought, let's rewrite the simulation part carefully.
                    pass

        # Re-implementing the simulation loop correctly inside the seed loop
        
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] # List of (arrival_time, service_duration)
        servers = [None] * c # Each element is (arrival_time, service_duration, end_time) or None
        # Actually, just storing end_time is enough for scheduling, but we need arrival_time for W.
        # So servers[j] = (arrival_time, end_time) if busy, else None.
        
        n_in_sys = 0
        area_n = 0.0
        last_t = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        total_time_in_sys = 0.0
        busy_min_sum = 0.0
        p_wait_hits = 0
        p_wait_total = 0
        
        # Initialize servers as idle
        for j in range(c):
            servers[j] = None
            
        while True:
            # Next arrival
            na = next_arr
            # Next departure
            nd = float('inf')
            for j in range(c):
                if servers[j] is not None:
                    if servers[j][1] < nd:
                        nd = servers[j][1]
            
            ne = min(na, nd)
            if ne > horizon:
                # Process remaining time up to horizon
                dt = horizon - t
                if t >= win_start:
                    area_n += n_in_sys * dt
                    active = sum(1 for s in servers if s is not None)
                    busy_min_sum += min(active, c) * dt
                t = horizon
                break
            
            dt = ne - t
            if t >= win_start:
                area_n += n_in_sys * dt
                active = sum(1 for s in servers if s is not None)
                busy_min_sum += min(active, c) * dt
            
            t = ne
            
            if abs(t - na) < 1e-9:
                # Arrival
                arr_count += 1
                if t >= win_start:
                    p_wait_total += 1
                    # Check if wait needed: queue non-empty OR all servers busy
                    if len(queue) > 0 or all(s is not None for s in servers):
                        p_wait_hits += 1
                
                svc_dur = rng.expovariate(mu)
                
                # Try to assign to free server
                assigned = False
                for j in range(c):
                    if servers[j] is None:
                        servers[j] = (t, t + svc_dur) # arrival_time, end_time
                        n_in_sys += 1
                        assigned = True
                        break
                
                if not assigned:
                    queue.append((t, svc_dur))
                    n_in_sys += 1
                
                next_arr = t + rng.expovariate(lam)
                
            elif abs(t - nd) < 1e-9:
                # Departure
                dep_count += 1
                # Find server finishing
                fin_j = -1
                for j in range(c):
                    if servers[j] is not None and abs(servers[j][1] - t) < 1e-9:
                        fin_j = j
                        break
                
                if fin_j != -1:
                    arr_t, _ = servers[fin_j]
                    total_time_in_sys += (t - arr_t)
                    servers[fin_j] = None
                    n_in_sys -= 1
                    
                    # Start next from queue if available
                    if queue:
                        q_arr_t, q_svc_dur = queue.pop(0)
                        servers[fin_j] = (q_arr_t, t + q_svc_dur)
                        n_in_sys += 1 # Still in system, just moved from queue to service
        
        L = area_n / win_len if win_len > 0 else 0
        W = total_time_in_sys / dep_count if dep_count > 0 else 0
        bf = busy_min_sum / (win_len * c) if win_len > 0 else 0
        pl = blk_count / arr_count if arr_count > 0 else 0
        pw = p_wait_hits / p_wait_total if p_wait_total > 0 else 0
        
        seeds_used.append(seed)
        per_seed_L.append(L)
        per_seed_W.append(W)
        per_seed_busy_frac.append(bf)
        per_seed_p_loss.append(pl)
        per_seed_p_wait.append(pw)
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count

    avg_L = sum(per_seed_L) / len(per_seed_L) if per_seed_L else 0
    avg_W = sum(per_seed_W) / len(per_seed_W) if per_seed_W else 0
    avg_bf = sum(per_seed_busy_frac) / len(per_seed_busy_frac) if per_seed_busy_frac else 0
    avg_pl = sum(per_seed_p_loss) / len(per_seed_p_loss) if per_seed_p_loss else 0
    avg_pw = sum(per_seed_p_wait) / len(per_seed_p_wait) if per_seed_p_wait else 0
    
    avg_arr = total_arr / len(seeds_used) if seeds_used else 0
    avg_dep = total_dep / len(seeds_used) if seeds_used else 0
    avg_blk = total_blk / len(seeds_used) if seeds_used else 0
    
    dep_rate = avg_dep / win_len * 60 if win_len > 0 else 0 # Per hour? Horizon unit is hour? 
    # Prompt: "average 10 people per hour", "service 10 minutes".
    # I used lam=10/hr, mu=6/hr. Time unit is HOURS.
    # So win_len is in hours.
    # dep_rate should be "per hour".
    # avg_dep is count. win_len is hours. rate = count/hours.
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    
    lam_eff = dep_rate # Conservation flow
    
    res = {
        "L": round(avg_L, 4),
        "W": round(avg_W * 60, 4), # Convert hours to minutes
        "busy_frac": round(avg_bf, 4),
        "p_wait": round(avg_pw, 4),
        "runtime_units": "hour",
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_pl, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
