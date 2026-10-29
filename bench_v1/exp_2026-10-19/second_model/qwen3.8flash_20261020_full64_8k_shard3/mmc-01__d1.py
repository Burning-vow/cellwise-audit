import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 5.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 3
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = 'hour'
    win = H * 0.75
    warmup_end = H * 0.25
    
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
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {}
        queue = []
        servers_free_at = [0.0] * c
        
        total_time_in_system = 0.0
        num_completed = 0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked = 0
        
        area_N = 0.0
        area_minNC = 0.0
        last_event_time = 0.0
        current_N = 0
        
        events = []
        
        def add_event(time, etype, data=None):
            events.append((time, etype, data))
        
        add_event(next_arrival, 'arrival')
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            ev_time, ev_type, ev_data = events.pop(0)
            
            if ev_time > H:
                break
            
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                area_N += current_N * dt
                area_minNC += min(current_N, c) * dt
            last_event_time = ev_time
            
            if ev_type == 'arrival':
                if ev_time >= warmup_end:
                    num_arrivals_window += 1
                
                if len(queue) < 10000:
                    st = rng.expovariate(mu)
                    queue.append((ev_time, st))
                    current_N += 1
                    
                    free_idx = -1
                    for j in range(c):
                        if servers_free_at[j] <= ev_time:
                            free_idx = j
                            break
                    
                    if free_idx != -1:
                        arr_t, svc_t = queue.pop(0)
                        dep_t = ev_time + svc_t
                        servers_free_at[free_idx] = dep_t
                        add_event(dep_t, 'departure', (arr_t, svc_t))
                        current_N -= 1
                    else:
                        pass
                else:
                    num_blocked += 1
                
                next_arrival = ev_time + rng.expovariate(lam)
                add_event(next_arrival, 'arrival')
                
            elif ev_type == 'departure':
                arr_t, svc_t = ev_data
                if ev_time >= warmup_end:
                    num_departures_window += 1
                    total_time_in_system += (ev_time - arr_t)
                    num_completed += 1
                
                if queue:
                    arr_t2, svc_t2 = queue.pop(0)
                    dep_t2 = ev_time + svc_t2
                    free_idx = -1
                    for j in range(c):
                        if servers_free_at[j] <= ev_time:
                            free_idx = j
                            break
                    if free_idx != -1:
                        servers_free_at[free_idx] = dep_t2
                        add_event(dep_t2, 'departure', (arr_t2, svc_t2))
                    else:
                        queue.insert(0, (arr_t2, svc_t2))
                
                current_N = len(queue) + sum(1 for s in servers_free_at if s > ev_time)
        
        if last_event_time < H and last_event_time >= warmup_end:
            dt = H - last_event_time
            area_N += current_N * dt
            area_minNC += min(current_N, c) * dt
        
        L_est = area_N / win if win > 0 else 0
        W_est = (total_time_in_system / num_completed * 60) if num_completed > 0 else 0
        busy_frac_est = area_minNC / (win * c) if win > 0 and c > 0 else 0
        p_wait_est = 0.0
        if num_arrivals_window > 0:
            p_wait_est = 0.0
        
        # Recalculate p_wait properly during simulation would be better but we approximate via Little's law or direct count
        # Let's do a simpler approach: track arrivals that found all servers busy
        # We need to re-run or track it. Since we didn't track it directly, let's use the fact that 
        # p_wait is probability an arrival finds all servers busy.
        # In our loop, when an arrival happens, if no server is free at that instant, they wait.
        # We can infer from queue length before adding? No, FCFS with immediate service if free.
        # If len(queue)==0 and all servers busy -> wait. But we pop immediately if free.
        # Actually, if after checking free_idx == -1, then they go to queue. That means they waited.
        # So count arrivals where free_idx was -1.
        
        # Re-simulate quickly just for p_wait tracking or modify above logic.
        # Given constraints, let's assume standard M/M/c formula approximation isn't allowed, must simulate.
        # I will adjust the simulation loop slightly in my head: 
        # When arrival occurs, check if any server is free AT THAT TIME.
        # If yes, start service immediately (wait=0).
        # If no, join queue (wait>0).
        # Count such cases.
        
        # Since I cannot easily edit the loop now without rewriting, I'll use a proxy:
        # For M/M/c, P(wait) = Erlang C. But we must simulate.
        # Let's restart the inner loop logic mentally to ensure correctness.
        # The previous code had a flaw in counting waits.
        
        # Corrected simulation logic for this specific run:
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue = []
        servers_free_at = [0.0] * c
        total_time_in_system = 0.0
        num_completed = 0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked = 0
        num_waited = 0
        area_N = 0.0
        area_minNC = 0.0
        last_event_time = 0.0
        current_N = 0
        events = []
        
        def add_event(time, etype, data=None):
            events.append((time, etype, data))
        
        add_event(next_arrival, 'arrival')
        
        while events:
            events.sort(key=lambda x: x[0])
            ev_time, ev_type, ev_data = events.pop(0)
            if ev_time > H: break
            
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                area_N += current_N * dt
                area_minNC += min(current_N, c) * dt
            last_event_time = ev_time
            
            if ev_type == 'arrival':
                if ev_time >= warmup_end:
                    num_arrivals_window += 1
                
                st = rng.expovariate(mu)
                # Check if any server is free
                free_idx = -1
                for j in range(c):
                    if servers_free_at[j] <= ev_time:
                        free_idx = j
                        break
                
                if free_idx != -1:
                    dep_t = ev_time + st
                    servers_free_at[free_idx] = dep_t
                    add_event(dep_t, 'departure', (ev_time, st))
                    # Wait time is 0
                else:
                    queue.append((ev_time, st))
                    if ev_time >= warmup_end:
                        num_waited += 1
                
                current_N = len(queue) + sum(1 for s in servers_free_at if s > ev_time)
                next_arrival = ev_time + rng.expovariate(lam)
                add_event(next_arrival, 'arrival')
                
            elif ev_type == 'departure':
                arr_t, svc_t = ev_data
                if ev_time >= warmup_end:
                    num_departures_window += 1
                    total_time_in_system += (ev_time - arr_t)
                    num_completed += 1
                
                if queue:
                    arr_t2, svc_t2 = queue.pop(0)
                    dep_t2 = ev_time + svc_t2
                    # Find which server became free? It's the one that just finished.
                    # We don't know exactly which index, but we can update the earliest free one.
                    # Actually, we should track server indices.
                    # Simplification: Just pick the first server that has free_at <= ev_time (which is true for the one that just departed)
                    # But multiple might be free. We need to assign correctly.
                    # Let's find the server that was busy until ev_time.
                    # This is getting complex. Let's stick to a simpler state representation.
                    # State: list of completion times for each server.
                    # On departure, we know one server is free.
                    # We can just set the minimum completion time to infinity? No.
                    
                    # Better approach: Track server states explicitly.
                    # But given the complexity, let's rely on the fact that we popped from queue.
                    # We need to know WHICH server freed up.
                    # In the previous step, we assigned dep_t to a specific free_idx.
                    # Here, we don't have that info.
                    
                    # Let's refactor: Store (server_index, arr_time, svc_time) in event data.
                    pass 

        # Due to complexity of refactoring mid-thought, I will provide a robust single-pass implementation below.
        # The key is to track server indices.
        
        # Reset and implement correctly
        rng = random.Random(seed)
        next_arrival = rng.expovariate(lam)
        queue = [] # list of (arrival_time, service_time)
        servers = [0.0] * c # next free time for each server
        total_time_in_system = 0.0
        num_completed = 0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked = 0
        num_waited = 0
        area_N = 0.0
        area_minNC = 0.0
        last_event_time = 0.0
        current_N = 0
        events = []
        
        def add_event(time, etype, data=None):
            events.append((time, etype, data))
        
        add_event(next_arrival, 'arrival')
        
        while events:
            events.sort(key=lambda x: x[0])
            ev_time, ev_type, ev_data = events.pop(0)
            if ev_time > H: break
            
            dt = ev_time - last_event_time
            if last_event_time >= warmup_end:
                area_N += current_N * dt
                area_minNC += min(current_N, c) * dt
            last_event_time = ev_time
            
            if ev_type == 'arrival':
                if ev_time >= warmup_end:
                    num_arrivals_window += 1
                
                st = rng.expovariate(mu)
                
                # Find a free server
                free_idx = -1
                for j in range(c):
                    if servers[j] <= ev_time:
                        free_idx = j
                        break
                
                if free_idx != -1:
                    dep_t = ev_time + st
                    servers[free_idx] = dep_t
                    add_event(dep_t, 'departure', (free_idx, ev_time, st))
                else:
                    queue.append((ev_time, st))
                    if ev_time >= warmup_end:
                        num_waited += 1
                
                current_N = len(queue) + sum(1 for s in servers if s > ev_time)
                next_arrival = ev_time + rng.expovariate(lam)
                add_event(next_arrival, 'arrival')
                
            elif ev_type == 'departure':
                srv_idx, arr_t, svc_t = ev_data
                if ev_time >= warmup_end:
                    num_departures_window += 1
                    total_time_in_system += (ev_time - arr_t)
                    num_completed += 1
                
                # Server becomes free
                servers[srv_idx] = 0.0 # Mark as free, but actually we should set it to current time? 
                # No, if we set to 0, next arrival checks <= ev_time.
                # But we need to handle queue immediately.
                
                if queue:
                    arr_t2, svc_t2 = queue.pop(0)
                    dep_t2 = ev_time + svc_t2
                    servers[srv_idx] = dep_t2
                    add_event(dep_t2, 'departure', (srv_idx, arr_t2, svc_t2))
                else:
                    servers[srv_idx] = 0.0 # Or keep it as ev_time? 
                    # If we set to 0, it's always free.
                    # If we set to ev_time, it's free at ev_time.
                    # Let's set to ev_time to be safe for "busy" calculation?
                    # Actually, for finding free server, we check servers[j] <= current_time.
                    # If we set to ev_time, and next event is later, it works.
                    # If we set to 0, it also works.
                    # Let's set to ev_time.
                    servers[srv_idx] = ev_time
                
                current_N = len(queue) + sum(1 for s in servers if s > ev_time)
        
        if last_event_time < H and last_event_time >= warmup_end:
            dt = H - last_event_time
            area_N += current_N * dt
            area_minNC += min(current_N, c) * dt
        
        L_est = area_N / win if win > 0 else 0
        W_est = (total_time_in_system / num_completed * 60) if num_completed > 0 else 0
        busy_frac_est = area_minNC / (win * c) if win > 0 and c > 0 else 0
        p_wait_est = num_waited / num_arrivals_window if num_arrivals_window > 0 else 0
        p_loss_est = num_blocked / num_arrivals_window if num_arrivals_window > 0 else 0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seeds_used_list.append(seed)
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(num_arrivals_window)
        all_dep.append(num_departures_window)
        all_blk.append(num_blocked)
        all_busy_util.append(busy_frac_est)
        all_dep_rate.append(num_departures_window / win if win > 0 else 0)
        all_lam_eff.append(num_arrivals_window / win if win > 0 else 0)
        all_p_loss.append(p_loss_est)
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
