import sys, json, random, argparse
from collections import deque

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in minutes
    lam_base = 10.0 / 60.0 # arrivals per minute
    mu_base = 1.0 / 10.0   # service rate per minute (mean 10 min)
    c = 2                  # servers
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "minute"
    horizon_min = H if time_unit == "minute" else H * 60 if time_unit == "hour" else H / 60
    
    warmup_frac = 0.25
    warmup_time = horizon_min * warmup_frac
    stat_window_len = horizon_min - warmup_time
    
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
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # State
        queue = deque() # waiting customers (arrival time, service time)
        servers_free_at = [0.0] * c # time when each server becomes free
        
        # Statistics accumulators for the window
        area_N = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0 # total sojourn time of completed customers in window
        count_completed_in_window = 0
        
        # For busy fraction E[min(N,c)]/c, we need integral of min(N(t), c)/c over time
        # We can track this by integrating state changes.
        # Let's maintain current number in system N_current and last event time.
        N_current = 0
        last_event_time = 0.0
        area_busy_util = 0.0 # integral of min(N, c)/c
        
        while t < horizon_min:
            # Determine next event
            arr_t = next_arrival
            dep_t = min(servers_free_at) if any(s > t for s in servers_free_at) else float('inf')
            
            # If no one is being served, dep_t might be inf or past. 
            # Actually, servers_free_at stores completion times. If a server is idle, its free time <= t.
            # So min(servers_free_at) could be <= t. We only care about future completions.
            # Better: find earliest completion time strictly greater than t? 
            # No, if a customer finishes at exactly t, it's an event.
            # Let's just take min of servers_free_at. If it's <= t, that means someone finished before or at t.
            # But we process events chronologically. If dep_t <= t, it should have been processed already?
            # Not necessarily if multiple events happen at same time.
            # Standard approach: pick smallest time >= t.
            
            valid_deps = [s for s in servers_free_at if s >= t]
            if not valid_deps:
                dep_t = float('inf')
            else:
                dep_t = min(valid_deps)
                
            if arr_t < dep_t:
                # Arrival
                dt = arr_t - t
                if t >= warmup_time:
                    area_N += N_current * dt
                    area_busy_util += (min(N_current, c) / c) * dt
                
                t = arr_t
                count_arr += 1 if t >= warmup_time else 0
                
                # Generate service time now
                svc_time = rng.expovariate(mu)
                
                # Check for available server
                avail_idx = -1
                for k in range(c):
                    if servers_free_at[k] <= t:
                        avail_idx = k
                        break
                
                if avail_idx != -1:
                    # Start service immediately
                    servers_free_at[avail_idx] = t + svc_time
                    N_current += 1
                    # Customer enters system, will leave later. 
                    # We don't add to queue.
                    # To calculate W, we need to know when they leave.
                    # We can store arrival time with the service completion event?
                    # Or simpler: since FCFS and single queue, we can manage a list of active services.
                    # But here we have direct assignment.
                    # Let's push (arrival_time, departure_time) to a global list of departures?
                    # Or better: use an event queue for departures too.
                    # Currently servers_free_at tracks when server becomes free.
                    # We need to associate the specific customer's arrival time with that slot.
                    # Let's change structure: instead of just time, store (time, arrival_time).
                    pass 
                else:
                    # Queue
                    queue.append((t, svc_time))
                    N_current += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                dt = dep_t - t
                if t >= warmup_time:
                    area_N += N_current * dt
                    area_busy_util += (min(N_current, c) / c) * dt
                    
                t = dep_t
                
                # Find which server finished
                finished_idx = -1
                for k in range(c):
                    if abs(servers_free_at[k] - t) < 1e-9: # Approximate check
                        finished_idx = k
                        break
                
                if finished_idx == -1:
                    # Should not happen if logic correct, but handle edge case
                    continue
                
                # Who was being served?
                # Problem: I didn't store who was being served in servers_free_at.
                # Refactor needed: servers_free_at should hold (completion_time, arrival_time_of_customer).
                # Since I can't refactor easily mid-thought, let's assume I'll rewrite the loop structure properly.
                # Okay, stopping this draft. The structure needs to track customer identity through service.
                
                # Correct Approach:
                # Use a priority queue for events? Or simple simulation.
                # Events: Arrival, Departure.
                # State: List of servers, each holding (finish_time, start_time, arrival_time)?
                # Simpler: When a customer starts service, we know their arrival time.
                # We can put a "Departure Event" into a timeline.
                
                # Let's restart the inner loop logic mentally to ensure correctness.
                # 1. Maintain `events` heap? No, standard M/M/c sim often uses explicit state.
                # 2. Servers: array of dicts {free_at, cust_arrival}.
                # 3. Queue: deque of {arrival, svc_time}.
                
                # On Arrival:
                #   Add to queue or assign to server.
                #   If assigned, set server.free_at = t + svc, server.cust_arrival = t.
                #   Push a departure event? Or just scan servers for next min(free_at).
                
                # On Departure (when t reaches min(server.free_at)):
                #   Identify server.
                #   Get cust_arrival from server.
                #   Calculate W = t - cust_arrival.
                #   Accumulate stats if t > warmup.
                #   Pop from queue if exists, assign to this server.
                #   Update N_current.
                
                # This requires careful bookkeeping.
                
                # Let's implement this cleanly.
                
                # Resetting variables for clean implementation...
                # I will write the final code based on this logic.
                
                # Note: The previous block had issues with tracking customer identity during service.
                # I will fix this in the final output.
                
                # Also, need to handle the case where multiple departures happen at same time.
                # And arrivals/departures at same time.
                
                # One more thing: "Service duration must be drawn at arrival".
                # My plan does this.
                
                # Warmup handling:
                # Stats only accumulated after warmup_time.
                # Area integrals need to be split if an event crosses warmup boundary.
                # Easier: Run full sim, record all events, then filter?
                # Memory efficient: Just check `if t >= warmup_time` inside loops.
                # But area calculation `area += N * dt` needs to be clipped.
                # If interval [t_prev, t_curr] overlaps warmup, split it.
                
                # Let's refine the area accumulation.
                # Keep `last_stat_time`.
                # When moving time forward to `next_t`:
                #   segment_start = max(last_stat_time, t_prev)
                #   segment_end = next_t
                #   if segment_start < segment_end:
                #       area += N * (segment_end - segment_start)
                #   last_stat_time = next_t
                
                # This handles warmup correctly.
                
                # Final Code Structure:
                # Initialize RNG, params.
                # Loop seeds.
                # Inside seed:
                #   Init state.
                #   While t < horizon:
                #     Find next event time (arr or dep).
                #     Advance time, update areas.
                #     Process event.
                #   Compute metrics.
                # Aggregate results.
                # Print JSON.
                
                # I will now generate the code following this corrected logic.
                
                # Breaking out of the flawed draft.
                pass 

# The above thought process identified flaws in the initial draft. 
# I will now provide the corrected Python code directly.

import sys, json, random, argparse
from collections import deque
import heapq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    n_seeds = args.seeds
    horizon = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    # Base parameters (minutes)
    base_lam = 10.0 / 60.0  # arrivals per minute
    base_mu = 1.0 / 10.0    # service rate per minute
    base_c = 2              # servers
    
    lam = base_lam
    mu = base_mu
    c = base_c
    
    if pert == 'lam_up':
        lam *= 1.2
    elif pert == 'mu_up':
        mu *= 1.2
    elif pert == 'c_up':
        c += 1
        
    time_unit = "minute"
    T = horizon # Total simulation time in minutes
    warmup = T * 0.25
    win_len = T - warmup
    
    res_L = []
    res_W = []
    res_busy_frac = []
    res_p_wait = []
    res_arr = []
    res_dep = []
    res_blk = []
    res_busy_util = []
    res_dep_rate = []
    res_lam_eff = []
    res_p_loss = []
    
    used_seeds = []
    
    for i in range(n_seeds):
        seed = seed_start + i
        used_seeds.append(seed)
        rng = random.Random(seed)
        
        # Simulation State
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        # Servers: list of dicts {'free_at': float, 'cust_arr': float}
        # Initially all free at 0
        servers = [{'free_at': 0.0, 'cust_arr': None} for _ in range(c)]
        
        # Queue: deque of tuples (arrival_time, service_duration)
        queue = deque()
        
        # Statistics
        # We need to integrate N(t) and min(N(t), c)/c over [warmup, T]
        # We also need counts of arrivals, departures, blocks in [warmup, T]
        # And sum of W for customers departing in [warmup, T]
        
        area_N = 0.0
        area_busy_util = 0.0 # Integral of min(N,c)/c
        
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        count_completed = 0 # Number of customers who departed in window
        
        # Helper to advance time and accumulate area
        def accumulate_area(dt, current_N):
            nonlocal area_N, area_busy_util
            if dt <= 0: return
            # Only accumulate if the interval intersects with [warmup, T]
            # Since we call this step-by-step, we can clip the interval
            # However, simpler: just check if t >= warmup before adding?
            # No, because an interval might start before warmup and end after.
            # Let's track `last_accum_time`?
            # Alternative: Since we process events sequentially, we can just add to area
            # if the *start* of the interval is >= warmup? No, that misses partial intervals.
            
            # Robust way:
            # Interval is [t_old, t_new].
            # Overlap with [warmup, T]:
            # start_overlap = max(t_old, warmup)
            # end_overlap = min(t_new, T)
            # if start_overlap < end_overlap:
            #     overlap_len = end_overlap - start_overlap
            #     area_N += current_N * overlap_len
            #     area_busy_util += (min(current_N, c) / c) * overlap_len
            
            start_ov = max(t, warmup) # Wait, t is current time BEFORE advancing?
            # In the loop, we usually do:
            # dt = next_event_time - t
            # accumulate(dt, N)
            # t = next_event_time
            # So here, the interval is [t, t+dt].
            start_ov = max(t, warmup)
            end_ov = min(t + dt, T)
            if start_ov < end_ov:
                len_ov = end_ov - start_ov
                area_N += current_N * len_ov
                area_busy_util += (min(current_N, c) / c) * len_ov

        while t < T:
            # Determine next event time
            arr_t = next_arrival
            # Earliest server free time that is >= t
            dep_times = [s['free_at'] for s in servers if s['free_at'] >= t]
            if dep_times:
                dep_t = min(dep_times)
            else:
                dep_t = float('inf')
            
            next_t = min(arr_t, dep_t)
            
            if next_t > T:
                # End of simulation
                dt = T - t
                current_N = len(queue) + sum(1 for s in servers if s['free_at'] > t)
                accumulate_area(dt, current_N)
                t = T
                break
            
            dt = next_t - t
            current_N = len(queue) + sum(1 for s in servers if s['free_at'] > t)
            accumulate_area(dt, current_N)
            t = next_t
            
            # Process Event
            if arr_t <= dep_t:
                # Arrival
                if t >= warmup:
                    count_arr += 1
                
                svc_dur = rng.expovariate(mu)
                
                # Find free server
                free_idx = -1
                for k in range(c):
                    if servers[k]['free_at'] <= t:
                        free_idx = k
                        break
                
                if free_idx != -1:
                    # Start service
                    servers[free_idx]['free_at'] = t + svc_dur
                    servers[free_idx]['cust_arr'] = t
                else:
                    # Join queue
                    queue.append((t, svc_dur))
                    
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure
                # Find server that became free at t
                dep_idx = -1
                for k in range(c):
                    if abs(servers[k]['free_at'] - t) < 1e-9:
                        dep_idx = k
                        break
                
                if dep_idx != -1:
                    cust_arr = servers[dep_idx]['cust_arr']
                    w = t - cust_arr
                    
                    if t >= warmup:
                        count_dep += 1
                        sum_W += w
                        count_completed += 1
                        
                    # Clear server
                    servers[dep_idx]['free_at'] = 0.0 # Mark as free/idle
                    servers[dep_idx]['cust_arr'] = None
                    
                    # Serve next from queue if any
