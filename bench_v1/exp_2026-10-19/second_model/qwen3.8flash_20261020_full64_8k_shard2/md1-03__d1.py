import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    lam_base = 6.0
    mu_base = 10.0
    c_base = 1

    if pert == "lam_up":
        lam = lam_base * 1.1
    elif pert == "mu_up":
        mu = mu_base * 1.1
    elif pert == "c_up":
        c = c_base + 1
    else:
        lam = lam_base
        mu = mu_base
        c = c_base

    time_unit = "hour"
    win_frac = 0.75
    warmup_len = H * (1 - win_frac)
    stat_win_len = H * win_frac

    all_L = []
    all_W = []
    all_busy_frac = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_p_loss = []
    all_p_wait = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []

    for i in range(N_seeds):
        seed_val = S_start + i
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = rng.expovariate(lam)
        service_times = {}
        queue = []
        servers_free_at = [0.0] * c
        n_in_system = 0
        total_time_in_system = 0.0
        arrivals_in_stat = 0
        departures_in_stat = 0
        blocked_in_stat = 0
        busy_time_sum = 0.0
        last_event_time = 0.0
        prev_n = 0
        area_L = 0.0
        area_busy = 0.0
        events = []
        
        def add_event(ev_type, ev_time, data=None):
            events.append((ev_time, ev_type, data))
            events.sort(key=lambda x: x[0])

        add_event("arr", next_arr, None)
        
        while t < H:
            if not events:
                break
            ev_time, ev_type, data = events.pop(0)
            dt = ev_time - t
            if t >= warmup_len:
                area_L += prev_n * dt
                area_busy += min(prev_n, c) * dt
            t = ev_time
            
            if ev_type == "arr":
                if t >= warmup_len:
                    arrivals_in_stat += 1
                if len(queue) + sum(1 for s in servers_free_at if s <= t) < c:
                    pass
                
                free_servers = [idx for idx, s in enumerate(servers_free_at) if s <= t]
                if free_servers:
                    srv_idx = free_servers[0]
                    st = rng.expovariate(mu)
                    dep_t = t + st
                    service_times[dep_t] = {"start": t, "end": dep_t}
                    servers_free_at[srv_idx] = dep_t
                    add_event("dep", dep_t, dep_t)
                    n_in_system += 1
                else:
                    if len(queue) < 1000:
                        queue.append(t)
                        n_in_system += 1
                    else:
                        if t >= warmup_len:
                            blocked_in_stat += 1
                prev_n = n_in_system
                next_arr = t + rng.expovariate(lam)
                add_event("arr", next_arr, None)
                
            elif ev_type == "dep":
                dep_key = data
                if dep_key in service_times:
                    start_t = service_times[dep_key]["start"]
                    del service_times[dep_key]
                    n_in_system -= 1
                    if t >= warmup_len:
                        departures_in_stat += 1
                        total_time_in_system += (t - start_t)
                    
                    if queue:
                        arr_t = queue.pop(0)
                        st = rng.expovariate(mu)
                        new_dep_t = t + st
                        service_times[new_dep_t] = {"start": t, "end": new_dep_t}
                        servers_free_at[min(range(c), key=lambda k: servers_free_at[k])] = new_dep_t
                        add_event("dep", new_dep_t, new_dep_t)
                        n_in_system += 1
                    else:
                        for idx in range(c):
                            if servers_free_at[idx] == t:
                                servers_free_at[idx] = float('inf')
                                break
                    prev_n = n_in_system

        if stat_win_len > 0:
            L_est = area_L / stat_win_len
            W_est = total_time_in_system / departures_in_stat if departures_in_stat > 0 else 0.0
            busy_frac_est = area_busy / stat_win_len
            p_loss_est = blocked_in_stat / arrivals_in_stat if arrivals_in_stat > 0 else 0.0
            p_wait_est = 0.0 
            # Approximate wait prob: fraction of arrivals that had to wait? 
            # In M/M/1 with FCFS, P(wait) = rho. But here we track actuals.
            # Let's compute based on observed waits if possible, or use Little's law consistency check later.
            # For now, simple estimate: if server was busy at arrival, they waited.
            # We didn't track that explicitly in the loop above efficiently.
            # Re-evaluating: The prompt asks for p_wait. Usually probability an arriving customer waits.
            # Since we don't have a flag for "waited" stored per customer easily without more structuring,
            # and we are constrained to no classes/refactoring, let's approximate or skip precise tracking if hard.
            # However, standard DES usually tracks this. Let's assume p_wait is derived from system state or just report 0 if not tracked.
            # Actually, let's look at the constraints again. "Service duration must be drawn at arrival".
            # I did that.
            # To get p_wait accurately, I'd need to know if the server was busy when they arrived.
            # I can infer it: if they were queued immediately, they waited. If they went straight to service, they didn't.
            # In my code: if free_servers exists -> no wait. Else -> wait (queued).
            
            # Let's re-run logic mentally:
            # I need to count how many arrivals in stat window had to wait.
            # I'll add a counter for that.
            
            # Wait, I already wrote the loop. I can't go back and edit the loop structure easily without rewriting the whole block.
            # Let's rewrite the inner loop part slightly to include wait counting.
            
            # Resetting variables for this seed to ensure correctness in final output generation
            # This is getting messy. Let's restart the seed loop body construction carefully.
            pass
        
        # Due to complexity of inline editing, I will regenerate the core simulation loop properly below.
        # The previous attempt had flaws in tracking p_wait.
        
        # --- Corrected Simulation Loop ---
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = rng.expovariate(lam)
        # State: list of departure times for each server
        servers = [float('inf')] * c
        queue = [] # List of arrival times
        n_sys = 0
        area_L = 0.0
        area_busy = 0.0
        last_t = 0.0
        prev_n = 0
        prev_busy = 0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        total_w_time = 0.0
        
        # Pre-draw service times? No, draw at arrival.
        # We need to store service time associated with the customer currently being served or in queue?
        # Requirement: "Service duration must be drawn at arrival and attached to customer".
        # So when a customer arrives, we draw ST.
        # If they enter service, their end time is t + ST.
        # If they queue, we store (arrival_time, service_duration).
        
        pending_customers = [] # (arrival_time, service_duration)
        
        events = []
        def push_ev(time, typ, payload):
            events.append((time, typ, payload))
            events.sort(key=lambda x: x[0])
            
        push_ev(next_arr, 'A', None)
        
        while t < H:
            if not events: break
            et, typ, pay = events.pop(0)
            dt = et - t
            if t >= warmup_len:
                area_L += prev_n * dt
                area_busy += prev_busy * dt
            t = et
            
            if typ == 'A':
                if t >= warmup_len:
                    arr_count += 1
                
                # Draw service time NOW
                st = rng.expovariate(mu)
                
                # Find free server
                free_idx = -1
                for i in range(c):
                    if servers[i] <= t:
                        free_idx = i
                        break
                
                if free_idx != -1:
                    # Start service immediately
                    dep_t = t + st
                    servers[free_idx] = dep_t
                    push_ev(dep_t, 'D', {'start': t, 'st': st})
                    n_sys += 1
                    prev_n = n_sys
                    prev_busy = min(n_sys, c)
                    # Did not wait
                else:
                    # Must wait
                    if t >= warmup_len:
                        wait_count += 1
                    # Queue them
                    pending_customers.append({'arr': t, 'st': st})
                    n_sys += 1
                    prev_n = n_sys
                    prev_busy = min(n_sys, c)
                    
                next_arr = t + rng.expovariate(lam)
                push_ev(next_arr, 'A', None)
                
            elif typ == 'D':
                # Customer leaves
                n_sys -= 1
                if t >= warmup_len:
                    dep_count += 1
                    total_w_time += (t - pay['start'])
                
                # Check queue
                if pending_customers:
                    cust = pending_customers.pop(0)
                    # Start service for this customer
                    dep_t = t + cust['st']
                    # Find which server became free? It's the one that just finished.
                    # We need to identify the server index. 
                    # In our event payload, we didn't store server index.
                    # Let's fix: Store server index in D event.
                    # Re-running logic... this is too complex to patch mid-stream.
                    pass
                else:
                    # Server becomes idle
                    # Need to find which server.
                    pass
                    
                prev_n = n_sys
                prev_busy = min(n_sys, c)

        # The above logic is flawed because I lost server indices.
        # Let's write a clean version.
        
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = rng.expovariate(lam)
        servers = [float('inf')] * c
        queue = [] # (arrival_time, service_duration)
        n_sys = 0
        area_L = 0.0
        area_busy = 0.0
        last_t = 0.0
        prev_n = 0
        prev_busy = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_c = 0
        tot_w = 0.0
        
        heap = []
        import heapq
        heapq.heappush(heap, (next_arr, 'A', None))
        
        while t < H:
            if not heap: break
            et, typ, pay = heapq.heappop(heap)
            dt = et - t
            if t >= warmup_len:
                area_L += prev_n * dt
                area_busy += prev_busy * dt
            t = et
            
            if typ == 'A':
                if t >= warmup_len:
                    arr_c += 1
                st = rng.expovariate(mu)
                free_i = -1
                for i in range(c):
                    if servers[i] <= t:
                        free_i = i
                        break
                if free_i != -1:
                    dep_t = t + st
                    servers[free_i] = dep_t
                    heapq.heappush(heap, (dep_t, 'D', {'srv': free_i, 'start': t}))
                    n_sys += 1
                else:
                    if t >= warmup_len:
                        wait_c += 1
                    queue.append((t, st))
                    n_sys += 1
                prev_n = n_sys
                prev_busy = min(n_sys, c)
                na = t + rng.expovariate(lam)
                heapq.heappush(heap, (na, 'A', None))
                
            elif typ == 'D':
                srv_i = pay['srv']
                start_t = pay['start']
                n_sys -= 1
                if t >= warmup_len:
                    dep_c += 1
                    tot_w += (t - start_t)
                
                if queue:
                    arr_q, st_q = queue.pop(0)
                    dep_t = t + st_q
                    servers[srv_i] = dep_t
                    heapq.heappush(heap, (dep_t, 'D', {'srv': srv_i, 'start': t}))
                    n_sys += 1
                else:
                    servers[srv_i] = float('inf')
                prev_n = n_sys
                prev_busy = min(n_sys, c)

        if stat_win_len > 0 and dep_c > 0:
            L_s = area_L / stat_win_len
            W_s = tot_w / dep_c
            BF_s = area_busy / stat_win_len
            PL_s = blk_c / arr_c if arr_c > 0 else 0.0
            PW_s = wait_c / arr_c if arr_c > 0 else 0.0
        else:
            L_s = W_s = BF_s = PL_s = PW_s = 0.0
            
        per_seed_L.append(L_s)
        per_seed_W.append(W_s)
        per_seed_busy_frac.append(BF_s)
        per_seed_p_loss.append(PL_s)
        per_seed_p_wait.append(PW_s)
        all_L.append(L_s)
        all_W.append(W_s)
        all_busy_frac.append(BF_s)
        all_arr.append(arr_c)
        all_dep.append(dep_c)
        all_blk.append(blk_c)
        seeds_used_list.append(seed_val)

    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_BF = sum(all_busy_frac)/len(all_busy_frac) if all_busy_frac else 0
    avg_arr = sum(all_arr)/len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep)/len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk)/len(all_blk) if all_blk else 0
    
    dep_rate = avg_dep / stat_win_len * 3600 if stat_win_len > 0 else 0 # Per hour? Time unit is hour.
    # Wait, time_unit is hour. So dep_rate is dep/hour.
    # avg_dep is count in window. Window length is stat_win_len hours.
    # Rate = avg_dep / stat_win_len
    
    eff_dep_rate = avg_dep / stat_win_len if stat_win_len > 0 else 0
    lam_eff = eff_dep_rate
    
    p_loss_avg = avg_blk / avg_arr if avg_arr > 0 else 0
    p_wait_avg = sum(per_seed_p_wait)/len(per_seed_p_wait) if per_seed_p_wait else 0
    
    # busy_util = E[min(N,c)]/c. Here c=1. So same as busy_frac.
    busy_util = avg_BF / c if c > 0 else 0
    busy_occupied = avg_BF # 1 - pi0 approx
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_BF, 6),
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": time_unit,
        "win": round(stat_win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(eff_dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(p_loss_avg, 6),
        "p_wait": round(p_wait_avg, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
