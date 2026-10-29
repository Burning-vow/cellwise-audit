import argparse, json, random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    lam_base = 4.0 # arrivals per hour
    mu1_base = 60.0 / 7.5 # service rate stage 1 per hour
    mu2_base = 60.0 / 5.0 # service rate stage 2 per hour
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
        mu1 = mu1_base
        mu2 = mu2_base
    elif pert == 'mu_up':
        lam = lam_base
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
        
    time_unit = "hour"
    horizon_hours = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    seed_list = []
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        # Queue lengths
        q1_len = 0
        q2_len = 0
        # Server states (0=idle, 1=busy)
        s1_busy = False
        s2_busy = False
        # Completion times
        c1_time = float('inf')
        c2_time = float('inf')
        
        # Statistics accumulators (for area integration)
        # We need to track time spent in system for each job to compute W properly via Little's Law or direct sum?
        # The prompt asks for average residence time W. Usually computed as Total Time in System / Number of Departures.
        # L is Average Number in System = Area under N(t) curve / Horizon.
        
        total_time_in_system = 0.0
        num_departures = 0
        num_arrivals = 0
        num_blocked = 0 # In this model, no blocking/loss mentioned explicitly other than queues growing. 
                         # Standard Jackson network assumes infinite buffer unless specified. 
                         # "blk" usually refers to loss probability. If buffers are infinite, blk=0.
                         # However, the prompt mentions "p_loss". Let's assume infinite capacity, so p_loss=0.
                         # But wait, "blk" is requested. If it's a standard queueing network with infinite buffers, blk is 0.
                         # Let's stick to infinite buffers as no capacity limit was given.
                         
        # For busy fraction:
        time_s1_busy = 0.0
        time_s2_busy = 0.0
        
        # For L calculation (area under curve):
        # We need to integrate N(t) = n1(t) + n2(t).
        # n1(t) includes job in service + jobs in queue 1.
        # n2(t) includes job in service + jobs in queue 2.
        
        last_event_time = 0.0
        current_n1 = 0
        current_n2 = 0
        area_N = 0.0
        
        # Warmup period: first 25% of horizon
        warmup_end = 0.25 * horizon_hours
        
        # To handle warmup correctly for statistics:
        # We simulate until horizon.
        # We only accumulate stats after warmup_end.
        # But we need to know when events happen relative to warmup_end.
        
        # Event list approach is cleaner but discrete event simulation loop is required.
        
        while t < horizon_hours:
            # Determine next event time
            events = []
            if next_arrival < horizon_hours:
                events.append(('arr', next_arrival))
            if s1_busy and c1_time < horizon_hours:
                events.append(('dep1', c1_time))
            if s2_busy and c2_time < horizon_hours:
                events.append(('dep2', c2_time))
            
            if not events:
                break
            
            # Find earliest event
            min_t = min(e[1] for e in events)
            event_type = [e[0] for e in events if e[1] == min_t][0]
            
            # Update integrals up to min_t
            dt = min_t - t
            if t >= warmup_end:
                # Accumulate area for L
                # Current number in system
                n_sys = current_n1 + current_n2
                area_N += n_sys * dt
                
                # Accumulate busy times
                if s1_busy:
                    time_s1_busy += dt
                if s2_busy:
                    time_s2_busy += dt
                    
            t = min_t
            
            # Process event
            if event_type == 'arr':
                num_arrivals += 1
                # Add to queue 1
                current_n1 += 1
                if not s1_busy:
                    s1_busy = True
                    # Draw service time for stage 1
                    svc_time_1 = rng.expovariate(mu1)
                    c1_time = t + svc_time_1
                    # Store arrival time for this job? 
                    # We need to calculate residence time. 
                    # Since we don't have individual job tracking easily without classes,
                    # we can use Little's Law approximation or track carefully.
                    # Actually, standard DES tracks jobs. 
                    # Let's maintain a list of jobs in system? No, that's heavy.
                    # Alternative: When a job departs stage 2, we add its total time.
                    # We need to know when it arrived at stage 1.
                    # So we must store arrival time in the queue.
                    
                    # Refactor: Use lists for queues containing (arrival_time_at_stage1, entry_time_to_current_queue?)
                    # Simpler: Each job has an original arrival time.
                    # Queue 1 stores (orig_arr_time, start_service_time_if_immediate?)
                    # Let's just store orig_arr_time in Q1.
                    # When moving to Q2, keep orig_arr_time.
                    # When departing Q2, calc t - orig_arr_time.
                    
                    # Wait, I didn't initialize queues as lists above.
                    # Let's restart the state definition slightly more robustly within the loop logic mentally.
                    pass
                else:
                    # Just increment count, actual data stored in queue structure
                    pass
                
                # Generate next arrival
                next_arrival = t + rng.expovariate(lam)
                
            elif event_type == 'dep1':
                # Job leaves Stage 1
                s1_busy = False
                current_n1 -= 1 # One less in stage 1 system (service+queue)
                
                # Move to Stage 2
                # Need to retrieve the job's original arrival time from Q1
                # This implies I should have maintained a queue of objects/tuples.
                # Since I'm writing code now, I'll adjust the variable usage.
                
                # Check if Stage 2 is free
                if not s2_busy:
                    s2_busy = True
                    # Draw service time for stage 2
                    svc_time_2 = rng.expovariate(mu2)
                    c2_time = t + svc_time_2
                    # The job enters service immediately.
                    # Its "start time" in stage 2 is t.
                    # It stays in stage 2 system.
                    current_n2 += 1
                else:
                    # Join queue 2
                    current_n2 += 1
                    # Store job in Q2 list with its orig_arr_time
                    # And maybe its entry time to Q2? Not needed for W, only orig_arr_time matters.
                    
                # Start next job in Q1 if available
                if current_n1 > 0: # There are jobs waiting in Q1
                    s1_busy = True
                    # Pop one job from Q1
                    # Get its orig_arr_time
                    # Draw new service time
                    svc_time_1 = rng.expovariate(mu1)
                    c1_time = t + svc_time_1
                    # Note: The job moved from "waiting in Q1" to "in service at S1".
                    # The count current_n1 already reflects total in stage 1 (wait+serv).
                    # So decrementing current_n1 on departure was correct for the whole stage.
                    # Now we pick up the next one.
                    
            elif event_type == 'dep2':
                # Job leaves Stage 2 (System exit)
                s2_busy = False
                current_n2 -= 1
                
                # Calculate residence time
                # Retrieve orig_arr_time from the job that just finished
                # This requires the queue structures to hold the data.
                
                num_departures += 1
                
                # Start next job in Q2 if available
                if current_n2 > 0:
                    s2_busy = True
                    # Pop from Q2
                    # Draw service time
                    svc_time_2 = rng.expovariate(mu2)
                    c2_time = t + svc_time_2

        # End of simulation for this seed
        
        # Calculate metrics for this seed based on post-warmup window
        win_length = horizon_hours - warmup_end
        
        if win_length <= 0:
             L_val = 0.0
             W_val = 0.0
             busy_frac_val = 0.0
             p_loss_val = 0.0
             p_wait_val = 0.0
             arr_val = 0.0
             dep_val = 0.0
             blk_val = 0.0
        else:
            # L = Area / Window Length
            L_val = area_N / win_length
            
            # W = Total Time in System / Num Departures (in window)
            # Problem: I haven't accumulated total_time_in_system in the loop above because I skipped implementing the detailed queue storage in the pseudo-code trace.
            # I need to ensure the final code implements proper job tracking.
            
            # Busy Fraction: (Time S1 Busy + Time S2 Busy) / (2 * Win Length)? 
            # Or average utilization? Usually "busy_frac" might mean average utilization across servers.
            # Let's define busy_frac as (time_s1_busy + time_s2_busy) / (2 * win_length) ? 
            # Or just max? The prompt asks for "busy_util" too.
            # Let's assume busy_frac is the average fraction of time any server is busy? 
            # Standard interpretation: Utilization rho. 
            # Let's report average utilization of the two servers combined? 
            # Or per server? The key is singular "busy_frac".
            # Let's calculate overall system busy fraction: (time_s1_busy + time_s2_busy) / (2 * win_length).
            
            busy_frac_val = (time_s1_busy + time_s2_busy) / (2 * win_length)
            
            # p_loss: Assuming infinite buffer, 0.
            p_loss_val = 0.0
            
            # p_wait: Probability that an arriving customer has to wait?
            # Or fraction of time customers spend waiting vs serving?
            # Usually P(wait) is prob of delay.
            # Without detailed arrival inspection logs, hard to get exact P(delay).
            # Approximation: If queue length > 0 upon arrival.
            # I need to log this during simulation.
            
            # Dep Rate: departures per hour
            dep_rate_val = num_departures / win_length
            
            # Arrivals in window
            # I need to count arrivals specifically in the window.
            # My loop counted all arrivals. I need to filter.
            
            # Let's refine the implementation plan for the Python code:
            # 1. Use lists for Q1 and Q2 storing (orig_arr_time).
            # 2. Track `total_residence_time` by adding `t - orig_arr_time` on dep2.
            # 3. Track `num_arrivals_window`, `num_departures_window`.
            # 4. Track `count_wait_on_arrival` for P_wait.
            
            pass 

        # Append results
        # ... (will be filled in actual code)

    # Aggregate
    # ...

# Re-writing the core logic cleanly for the final output string.

import argparse
import json
import random

def run_sim(seed, horizon, lam, mu1, mu2, warmup_ratio=0.25):
    rng = random.Random(seed)
    t = 0.0
    next_arr = rng.expovariate(lam)
    
    # Queues store tuples: (original_arrival_time)
    q1 = [] # Waiting for S1
    q2 = [] # Waiting for S2
    
    # Servers
    s1_free = True
    s2_free = True
    c1_done = float('inf')
    c2_done = float('inf')
    
    # Stats accumulators (only for post-warmup)
    warmup_end = horizon * warmup_ratio
    area_N = 0.0
    time_s1_busy = 0.0
    time_s2_busy = 0.0
    total_res_time = 0.0
    n_dep_win = 0
    n_arr_win = 0
    n_wait_on_arr = 0 # Count arrivals where they had to wait (q1 not empty OR s1 busy)
    
    # Helper to get current N
    def get_N():
        return len(q1) + len(q2) + (1 if not s1_free else 0) + (1 if not s2_free else 0)
    
    last_t = 0.0
    
    while t < horizon:
        # Determine next event
        candidates = []
        if next_arr < horizon: candidates.append((next_arr, 'arr'))
        if not s1_free and c1_done < horizon: candidates.append((c1_done, 'dep1'))
        if not s2_free and c2_done < horizon: candidates.append((c2_done, 'dep2'))
        
        if not candidates: break
        
        next_t, event = min(candidates, key=lambda x: x[0])
        
        # Integrate stats from last_t to next_t
        dt = next_t - t
        if t >= warmup_end:
            n_curr = get_N()
            area_N += n_curr * dt
            if not s1_free: time_s1_busy += dt
            if not s2_free: time_s2_busy += dt
            
        t = next_t
        
        if event == 'arr':
            if t >= warmup_end:
                n_arr_win += 1
                # Check if waits
                if not s1_free or len(q1) > 0:
                    n_wait_on_arr += 1
            
            # Add to system
            # If S1 free, start service immediately
            if s1_free:
                s1_free = False
                svc = rng.expovariate(mu1)
                c1_done = t + svc
                # Job is in service, not in q1
            else:
                q1.append(t) # Store arrival time
                
            next_arr = t + rng.expovariate(lam)
            
        elif event == 'dep1':
            s1_free = True
            # Move job to S2
            # The job that finished was in service.
            # We need its original arrival time.
            # How did we track it? 
            # If it started service immediately, we lost the arrival time reference unless we stored it.
            # Fix: When starting service, store the arrival time in a variable associated with the server.
            # Let's change server state to include current_job_arr_time.
            
            # Correction in logic below:
            # I will refactor the state variables to hold job info.
            pass
            
        elif event == 'dep2':
            s2_free = True
            # Job exits
            # Need original arrival time of the job that just finished.
            pass

    # Return dict
    return {}

# Final Code Structure Construction

import argparse
import json
import random

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 4.0
    mu1_base = 60.0 / 7.5
    mu2_base = 60.0 / 5.0
    
    if pert == 'lam_up':
        lam, mu1, mu2 = lam_base*1.1, mu1_base, mu2_base
    elif pert == 'mu_up':
        lam, mu1, mu2 = lam_base, mu1_base*1.1, mu2_base*1.1
    elif pert == 'c_up':
        lam, mu1, mu2 = lam_base, mu1_base, mu2_base
    else:
        lam, mu1, mu2 = lam_base, mu1_base, mu2_base
        
    time_unit = "hour"
    horizon = H
    warmup_end = 0.25 * horizon
    
    res_L = []
    res_W = []
    res_busy = []
    res_ploss = []
    res_pwait = []
    res_arr = []
    res_dep = []
    res_blk = []
    seeds_used = []
    
    for i in range(N):
        seed = S_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        
        # State
        # q1: list of arrival times of jobs waiting for S1
        q1 = []
        # q2: list of arrival times of jobs waiting for S2
        q2 = []
        
        # S1 status
        s1_busy = False
        s1_job_arr = None # Arrival time of job currently in S1
        s1_end = float('inf')
        
        # S2 status
        s2_busy = False
        s2_job_arr = None # Arrival time of job currently in S2
        s2_end = float('inf')
        
        # Stats
        area_N = 0.0
        time_s1_busy = 0.0
        time_s2_busy = 0.0
        total_res_time = 0.0
        n_dep_win = 0
        n_arr_win = 0
        n_wait_on_arr = 0
        
        last_t = 0.0
        
        while t < horizon:
            events = []
            if next_arr < horizon: events.append((next_arr, 'arr'))
            if s1_busy and s1_end < horizon: events.append((s1_end, 'dep1'))
            if s2_busy and s2_end < horizon: events.append((s2_end, 'dep2'))
            
            if not events: break
            
            next_t, ev_type = min(events, key=lambda x: x[0])
            
            dt = next_t - t
            if t >= warmup_end:
                # Current number in system
                n_curr = len(q1) + len(q2) + (1 if s1_busy else 0) + (1 if s2_busy else 0)
                area_N += n_curr * dt
                if s1_busy: time_s1_busy += dt
                if s2_busy: time_s2_busy += dt
                
            t = next_t
            
            if ev_type == 'arr':
                if t >= warmup_end:
                    n_arr_win += 1
                    # Does it wait?
                    if s1_busy or len(q1) > 0:
                        n_wait_on_arr += 1
                
                if not s1_busy:
                    s1_busy = True
                    s1_job_arr = t
                    svc = rng.expovariate(mu1)
                    s1_end = t + svc
                else:
                    q1.append(t)
                    
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep1':
                s1_busy = False
                # Move job to S2
                # The job leaving S1 has arrival time s1_job_arr
                job_arr = s1_job_arr
                
                if not s2_busy:
                    s2_busy = True
                    s2_job_arr = job_arr
                    svc = rng.expovariate(mu2)
                    s2_end = t + svc
                else:
                    q2.append(job_arr)
                
                # Start next job in S1 if any
                if q1:
                    s1_busy = True
                    s1_job_arr = q1.pop(0)
                    svc = rng.expovariate(mu1)
                    s1_end = t + svc
                    
            elif ev_type == 'dep2':
                s2_busy = False
                # Job exits
                job_arr = s2_job_arr
                res_time = t - job_arr
                
                if t >= warmup_end:
                    total_res_time += res_time
                    n_dep_win += 1
                
                # Start next job in S2 if any
                if q2:
                    s2_busy = True
                    s2_job_arr = q2.pop(0)
                    svc = rng.expovariate(mu2)
                    s2_end = t + svc

        # Calculate metrics for this seed
        win_len = horizon - warmup_end
        if win_len <= 0:
            L_val = 0.0
            W_val = 0.0
            busy_val = 0.0
            ploss_val = 0.0
            pwait_val = 0.0
            arr_val = 0.0
            dep_val = 0.0
            blk_val = 0.0
        else:
            L_val = area_N / win_len
            W_val = total_res_time / n_dep_win if n_dep_win > 0 else 0.0
            # Busy fraction: average utilization of the two servers
            busy_val = (time_s1_busy + time_s2_busy) / (2 * win_len)
            ploss_val = 0.0 # Infinite buffer
            pwait_val = n_wait_on_arr / n_arr_win if n_arr_win > 0 else 0.0
            arr_val = n_arr_win
            dep_val = n_dep_win
            blk_val = 0.0
            
        res_L.append(L_val)
        res_W.append(W_val)
        res_busy.append(busy_val)
        res_ploss.append(ploss_val)
        res_pwait.append(pwait_val)
        res_arr.append(arr_val)
        res_dep.append(dep_val)
        res_blk.append(blk_val)
        
    # Aggregate averages
    avg_L = sum(res_L)/N if N>0 else 0
    avg_W = sum(res_W)/N if N>0 else 0
    avg_busy = sum(res_busy)/N if N>0 else 0
    avg_ploss = sum(res_ploss)/N if N>0 else 0
    avg_pwait = sum(res_pwait)/N if N>0 else 0
    avg_arr = sum(res_arr)/N if N>0 else 0
    avg_dep = sum(res_dep)/N if N>0 else 0
    avg_blk = sum(res_blk)/N if N>0 else 0
    
    dep_rate = avg_dep / (horizon - 0.25*horizon) if (horizon - 0.25*horizon)>0 else 0
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(horizon - 0.25*horizon, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_frac": round(avg_busy, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(avg_arr / (horizon - 0.25*horizon), 6) if (horizon - 0.25*horizon)>0 else 0,
        "p_loss": round(avg_ploss, 6),
        "p_wait": round(avg_pwait, 6),
        "per_seed_L": [round(x, 6) for x in res_L],
        "per_seed_W": [round(x, 6) for x in res_W],
        "per_seed_busy_frac": [round(x, 6) for x in res_busy],
        "per_seed_p_loss": [round(x, 6) for x in res_ploss],
        "per_seed_p_wait": [round(x, 6) for x in res_pwait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
