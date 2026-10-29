import sys, json, random, argparse
from collections import deque

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed-start
    pert = args.pert

    # Parameters in hours
    base_lam = 8.0
    base_mu = 5.0 # 60/12 = 5 per hour
    c = 2
    K = 4 # capacity including service

    if pert == 'lam_up': lam = base_lam * 1.2
    elif pert == 'mu_up': mu = base_mu * 1.2; lam = base_lam
    elif pert == 'c_up': c = 3; K = 5; lam = base_lam; mu = base_mu
    else: lam = base_lam; mu = base_mu
    
    if pert == 'mu_up': mu = base_mu * 1.2
    elif pert != 'c_up': mu = base_mu

    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0
        servers_free = [True] * c
        queue = deque() # Stores arrival times of waiting cars
        
        # Event list: (time, type, data)
        # type: 0=arrival, 1=departure
        events = []
        
        # Generate first arrival
        next_arr_time = rng.expovariate(lam)
        events.append((next_arr_time, 0, None))
        
        # Statistics accumulators (for area integration and counts)
        # We need to discard the first 25% as warmup
        warmup_end = 0.25 * H
        stat_start_time = warmup_end
        
        # Area accumulators
        area_n = 0.0
        area_busy = 0.0 # Time where at least one server is busy? No, busy_frac defined as station not empty (1-pi0). 
                        # So we integrate indicator(n > 0).
        area_min_nc = 0.0 # For busy_util = E[min(N,c)]/c
        
        # Counts
        count_arr = 0
        count_blk = 0
        count_dep = 0
        count_wait = 0 # Arrivals that had to wait (queue length > 0 upon arrival or server full?)
                       # Standard definition: W is average time in system. p_wait is prob an arriving customer waits.
                       # A customer waits if upon arrival, all servers are busy.
        
        total_time_in_system = 0.0
        
        last_stat_time = 0.0
        
        while True:
            if not events:
                break
            
            # Pop earliest event
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, ev_data = events.pop(0)
            
            if curr_t > H:
                break
                
            # Integrate areas from last_stat_time to curr_t
            dt = curr_t - last_stat_time
            if last_stat_time < stat_start_time:
                # Partially in warmup, partially in stats?
                # Simpler: only start integrating after stat_start_time
                pass
            
            # Determine effective integration interval
            int_start = max(last_stat_time, stat_start_time)
            int_end = curr_t
            
            if int_start < int_end:
                duration = int_end - int_start
                area_n += n_in_system * duration
                # Busy fraction: station not empty means n_in_system > 0
                if n_in_system > 0:
                    area_busy += duration
                # min(N, c)
                m = min(n_in_system, c)
                area_min_nc += m * duration
            
            last_stat_time = curr_t
            
            if ev_type == 0: # Arrival
                # Check capacity
                if n_in_system >= K:
                    count_blk += 1
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    new_t = curr_t + inter_arr
                    if new_t <= H:
                        events.append((new_t, 0, None))
                else:
                    count_arr += 1
                    n_in_system += 1
                    
                    # Check if a server is free
                    free_idx = -1
                    for k in range(c):
                        if servers_free[k]:
                            free_idx = k
                            break
                            
                    if free_idx != -1:
                        # Start service immediately
                        servers_free[free_idx] = False
                        svc_time = rng.expovariate(mu)
                        dep_t = curr_t + svc_time
                        if dep_t <= H:
                            events.append((dep_t, 1, {'start': curr_t}))
                        else:
                            # If departure is beyond horizon, do we count it?
                            # Usually simulation stops at H. Customers in system at H are still there.
                            # But their service time was drawn. They don't depart within window.
                            # So they contribute to L but not to W completion stats unless we handle truncation.
                            # The prompt implies standard DES. Usually, we stop generating events past H.
                            # However, customers already in system stay until end.
                            # Let's assume if dep_t > H, they remain in system till H.
                            pass
                    else:
                        # All servers busy, join queue
                        queue.append(curr_t)
                        # Mark as waiting? 
                        # p_wait usually refers to probability an arrival has to wait.
                        # Since no server was free, this arrival waits.
                        count_wait += 1
                        
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    new_t = curr_t + inter_arr
                    if new_t <= H:
                        events.append((new_t, 0, None))
                        
            elif ev_type == 1: # Departure
                # Find which server finished? 
                # In our model, we attached start time. We need to know which server slot became free.
                # Actually, simpler approach: when a departure happens, one server becomes free.
                # Then check if queue is non-empty.
                
                # Identify server index? We didn't store it explicitly in event data other than start time.
                # We can just pick any free server logic? No, we need to mark specific server free.
                # Let's modify: When scheduling departure, we should know which server.
                # Refactoring slightly inside loop logic above would be cleaner, but let's fix here.
                # Problem: I didn't store server index in event.
                # Fix: Re-run logic mentally. 
                # On arrival -> assign server idx -> schedule dep with idx.
                # On dep -> free server idx -> check queue.
                
                # Since I can't easily change the structure now without rewriting, let's look at the code generated.
                # Ah, I see `events.append((dep_t, 1, {'start': curr_t}))`. It lacks server ID.
                # This is a bug in my thought process. I must include server ID.
                
                # Let's restart the inner loop logic construction carefully.
                pass 

        # The above loop had a flaw. Let's rewrite the simulation core properly.
        
        # Reset for correct implementation
        rng = random.Random(seed)
        t = 0.0
        n_in_system = 0
        servers_free = [True] * c
        queue = deque() # (arrival_time)
        events = []
        
        next_arr_time = rng.expovariate(lam)
        events.append((next_arr_time, 0, None))
        
        warmup_end = 0.25 * H
        stat_start_time = warmup_end
        
        area_n = 0.0
        area_busy = 0.0
        area_min_nc = 0.0
        
        count_arr = 0
        count_blk = 0
        count_dep = 0
        count_wait = 0
        total_time_in_system = 0.0
        
        last_stat_time = 0.0
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, ev_data = events.pop(0)
            
            if curr_t > H:
                break
            
            # Integrate
            int_start = max(last_stat_time, stat_start_time)
            int_end = curr_t
            if int_start < int_end:
                duration = int_end - int_start
                area_n += n_in_system * duration
                if n_in_system > 0:
                    area_busy += duration
                m = min(n_in_system, c)
                area_min_nc += m * duration
            
            last_stat_time = curr_t
            
            if ev_type == 0: # Arrival
                if n_in_system >= K:
                    count_blk += 1
                else:
                    count_arr += 1
                    n_in_system += 1
                    
                    free_idx = -1
                    for k in range(c):
                        if servers_free[k]:
                            free_idx = k
                            break
                    
                    if free_idx != -1:
                        servers_free[free_idx] = False
                        svc_time = rng.expovariate(mu)
                        dep_t = curr_t + svc_time
                        # Store server index in event data
                        if dep_t <= H:
                            events.append((dep_t, 1, {'server': free_idx, 'start': curr_t}))
                        else:
                            # Customer stays in system until H, but doesn't depart.
                            # We need to track them for L, but not for W completion?
                            # Usually W is avg time of completed services.
                            # Or avg time in system for those who left?
                            # Prompt says "W (minutes)". Standard Little's Law uses completed.
                            # If they don't complete, they aren't counted in W numerator/denominator?
                            # Yes, typically W is based on departures.
                            pass
                    else:
                        queue.append({'arr': curr_t})
                        count_wait += 1
                
                # Next arrival
                inter_arr = rng.expovariate(lam)
                new_t = curr_t + inter_arr
                if new_t <= H:
                    events.append((new_t, 0, None))
                    
            elif ev_type == 1: # Departure
                srv_idx = ev_data['server']
                arr_time = ev_data['start']
                
                # Calculate time in system for this customer
                # Note: If they waited, arr_time is when they arrived.
                # Wait, if they were in queue, their 'start' time in service is different.
                # My previous logic: if free, start=curr_t. If queued, we push to queue.
                # When does a queued customer get served?
                # When a server frees up.
                
                # Correction: The event data 'start' passed above is the ARRIVAL time if immediate service?
                # No, I set `svc_time` based on `curr_t` (arrival time).
                # And `dep_t = curr_t + svc_time`.
                # This assumes service starts immediately.
                # If they wait, service starts later.
                
                # Logic for Queue:
                # When a departure occurs, check if queue is non-empty.
                # If yes, pop front, assign to this freed server, calculate new departure time.
                
                # So, for the departing customer:
                # Their actual service start time might be different from arrival time.
                # We need to track when service actually started.
                
                # Let's refine state:
                # Queue stores arrival times.
                # Servers store (busy_until, start_service_time)? No, just busy flag.
                # When assigning to server, we generate service time.
                
                # Revised Departure Handling:
                # 1. Free the server.
                # 2. Check queue.
                # 3. If queue not empty, pop head, assign to this server, generate service time, schedule new departure.
                # 4. The current departing customer's time in system = curr_t - their_arrival_time.
                #    We need their arrival time.
                #    If they came from queue, we lost their arrival time in the event data?
                #    Event data has 'start'. Is 'start' arrival or service start?
                #    In my code above: `events.append((dep_t, 1, {'server': free_idx, 'start': curr_t}))`
                #    Here `curr_t` is arrival time.
                #    BUT, if they waited, `curr_t` at assignment is NOT arrival time.
                
                # Let's trace:
                # Arrival at T_a. Server busy. Push T_a to queue.
                # Departure at T_d. Server frees. Pop T_a from queue.
                # Assign to server. Service time S. New Dep T_new = T_d + S.
                # Event: (T_new, 1, {'server': idx, 'start': T_a}).
                # So 'start' in event data should ALWAYS be the original arrival time.
                
                # Back to current event:
                # ev_data['start'] is the arrival time of the customer leaving NOW.
                time_in_sys = curr_t - ev_data['start']
                
                # Only count if they departed within window?
                # Yes, this is a departure event.
                count_dep += 1
                total_time_in_system += time_in_system
                
                # Now, check queue for next customer
                if queue:
                    next_cust_arr = queue.popleft()
                    # Assign to this server
                    servers_free[srv_idx] = False # Still busy with new customer
                    svc_time = rng.expovariate(mu)
                    new_dep_t = curr_t + svc_time
                    if new_dep_t <= H:
                        events.append((new_dep_t, 1, {'server': srv_idx, 'start': next_cust_arr}))
                    else:
                        # Stays in system
                        pass
                else:
                    servers_free[srv_idx] = True
                
                n_in_system -= 1

        # End of simulation for this seed
        
        # Calculate stats for this seed
        # Window length
        win_len = H - stat_start_time
        if win_len <= 0:
             # Edge case
             l_val = 0.0
             w_val = 0.0
             bf_val = 0.0
             pl_val = 0.0
             pw_val = 0.0
             bu_val = 0.0
             dr_val = 0.0
             le_val = 0.0
             ca = 0
             cb = 0
             cd = 0
             cw = 0
        else:
            l_val = area_n / win_len
            # W: Average time in system for completed departures
            if count_dep > 0:
                w_val = (total_time_in_system / count_dep) * 60.0 # Convert hours to minutes
            else:
                w_val = 0.0
            
            bf_val = area_busy / win_len # Fraction of time station not empty
            
            total_attempts = count_arr + count_blk
            if total_attempts > 0:
                pl_val = count_blk / total_attempts
            else:
                pl_val = 0.0
                
            if count_arr > 0:
                pw_val = count_wait / count_arr
            else:
                pw_val = 0.0
                
            bu_val = area_min_nc / (win_len * c)
            
            dr_val = count_dep / win_len # Per hour
            
            le_val = count_arr / win_len # Effective arrival rate (accepted)
            
            ca = count_arr
            cb = count_blk
            cd = count_dep
            cw = count_wait

        all_L.append(l_val)
        all_W.append(w_val)
        all_busy_frac.append(bf_val)
        all_p_loss.append(pl_val)
        all_p_wait.append(pw_val)
        all_arr.append(ca)
        all_blk.append(cb)
        all_dep.append(cd)
        all_busy_util.append(bu_val)
        all_dep_rate.append(dr_val)
        all_lam_eff.append(le_val)
        seed_list.append(seed)

    seeds_used = len(all_L)
    
    # Aggregate averages
    def avg(lst):
        return sum(lst)/len(lst) if lst else 0.0
        
    res = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_loss": avg(all_p_loss),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": H - 0.25*H,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_wait": avg(all_p_wait),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
