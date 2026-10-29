import random, json, math, sys

def main():
    import argparse
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

    # Parameters in minutes
    lam_base = 6.0 / 60.0  # jobs per minute (6 per hour)
    mu1_base = 1.0 / 6.0   # service rate stage 1 (mean 6 min)
    mu2_base = 1.0 / 5.0   # service rate stage 2 (mean 5 min)

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == 'c_up':
        # Cost perturbation doesn't change dynamics for this metric, assume no change or slight variation? 
        # Problem says "perturbation only changes parameters not structure". c usually cost. 
        # If it affects nothing, keep base. Let's assume it might affect priority or something not modeled here.
        # For safety, treat as none unless specified otherwise.
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base

    time_unit = "minute"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    seeds_used = 0
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        # Queue lengths
        q1 = 0
        q2 = 0
        # Server status: 0=idle, 1=busy
        s1_busy = False
        s2_busy = False
        
        # Event list: (time, type, data)
        # Types: 'arr' (arrival), 'dep1' (departure from 1), 'dep2' (departure from 2)
        events = []
        
        # Statistics accumulators (for area integration)
        # We need to integrate L over time and W over count.
        # But standard DES stats:
        # L_avg = (Integral of L(t) dt) / T_window
        # W_avg = (Sum of sojourn times) / Count_departures
        
        # Warmup: discard first 25% of horizon
        warmup_end = 0.25 * H
        stat_start_time = warmup_end
        
        # Accumulators for the statistical window
        int_L = 0.0      # Integral of total number in system (q1+q2+busy1+busy2)
        sum_W = 0.0      # Sum of sojourn times for completed jobs in window
        count_dep = 0    # Number of departures in window
        count_arr = 0    # Number of arrivals in window
        count_blk = 0    # Blocked/lost (not applicable here, infinite queue assumed?) 
                         # "each has its own queue" implies infinite capacity. So blk=0.
        
        # Time tracking for integration
        last_stat_time = -1.0
        current_L_val = 0
        
        # To handle integration correctly with discrete events:
        # We maintain a variable `current_total_in_system` which is q1 + q2 + (1 if s1_busy else 0) + (1 if s2_busy else 0)
        # When an event happens at time t_event:
        # 1. If t_event > stat_start_time:
        #    Add (t_event - max(last_stat_time, stat_start_time)) * current_L_val to int_L
        #    Update last_stat_time = t_event
        # 2. Process event, update state.
        # 3. Recalculate current_L_val.
        
        # Initial arrival
        next_arr_time = rng.expovariate(lam)
        events.append((next_arr_time, 'arr', None))
        
        # Job tracking for W calculation
        # Map job_id -> arrival_time
        # Since we don't have explicit IDs, we can store arrival time in the event tuple or a separate dict.
        # Better: Store arrival time in the queue items.
        # q1 stores arrival_times of jobs waiting in Q1
        # q2 stores arrival_times of jobs waiting in Q2
        # s1_job_info: (start_service_time, arrival_time) if busy
        # s2_job_info: (start_service_time, arrival_time) if busy
        
        q1_times = []
        q2_times = []
        s1_arrival = None
        s2_arrival = None
        
        while events:
            events.sort(key=lambda x: x[0])
            t_curr, ev_type, _ = events.pop(0)
            
            if t_curr > H:
                break
                
            # Integration step before processing event
            if t_curr > stat_start_time:
                start_int = max(last_stat_time, stat_start_time)
                if t_curr > start_int:
                    duration = t_curr - start_int
                    int_L += duration * current_L_val
                last_stat_time = t_curr
            
            # Process Event
            if ev_type == 'arr':
                count_arr += 1 if t_curr >= stat_start_time else 0
                # Arrive at Stage 1
                if not s1_busy:
                    s1_busy = True
                    s1_arrival = t_curr
                    dur = rng.expovariate(mu1)
                    events.append((t_curr + dur, 'dep1', None))
                else:
                    q1_times.append(t_curr)
                
                # Schedule next arrival
                next_arr_time = t_curr + rng.expovariate(lam)
                if next_arr_time <= H:
                    events.append((next_arr_time, 'arr', None))
                    
            elif ev_type == 'dep1':
                # Job leaves Stage 1
                arr_t = s1_arrival
                s1_busy = False
                s1_arrival = None
                
                # Move to Stage 2
                if not s2_busy:
                    s2_busy = True
                    s2_arrival = arr_t # Keep original arrival time for W calc
                    dur = rng.expovariate(mu2)
                    events.append((t_curr + dur, 'dep2', None))
                else:
                    q2_times.append(arr_t)
                
                # Start next job in Q1 if any
                if q1_times:
                    next_arr_t = q1_times.pop(0)
                    s1_busy = True
                    s1_arrival = next_arr_t
                    dur = rng.expovariate(mu1)
                    events.append((t_curr + dur, 'dep1', None))
                    
            elif ev_type == 'dep2':
                # Job leaves System
                arr_t = s2_arrival
                s2_busy = False
                s2_arrival = None
                
                w_i = t_curr - arr_t
                if t_curr >= stat_start_time:
                    sum_W += w_i
                    count_dep += 1
                
                # Start next job in Q2 if any
                if q2_times:
                    next_arr_t = q2_times.pop(0)
                    s2_busy = True
                    s2_arrival = next_arr_t
                    dur = rng.expovariate(mu2)
                    events.append((t_curr + dur, 'dep2', None))
            
            # Update current L value after state change
            current_L_val = len(q1_times) + len(q2_times) + (1 if s1_busy else 0) + (1 if s2_busy else 0)

        # Final integration up to H
        if H > stat_start_time:
            start_int = max(last_stat_time, stat_start_time)
            if H > start_int:
                duration = H - start_int
                int_L += duration * current_L_val
        
        win_len = H - stat_start_time
        
        if win_len > 0 and count_dep > 0:
            L_est = int_L / win_len
            W_est = sum_W / count_dep
        else:
            L_est = 0.0
            W_est = 0.0
            
        # Busy fraction: integral of busy time / win_len
        # We didn't track busy time separately. 
        # Approximation: In steady state, utilization rho = lambda_eff / mu.
        # But we need empirical.
        # Let's re-run logic or add trackers. 
        # Adding trackers is cleaner.
        
        # Re-calculate busy fractions using simple counters during simulation would be better.
        # For now, let's estimate based on counts if possible, or just return 0 if not tracked.
        # Actually, I should have tracked busy time.
        # Let's modify the loop slightly in thought process, but code is already written above.
        # Wait, I can compute busy_frac from L? No.
        # Let's assume the prompt allows approximations or I missed adding busy timers.
        # Given constraints, I'll output 0 for busy_frac if not tracked, but that fails checks.
        # I must track busy time.
        
        # Refactoring needed? No, I can't edit previous lines easily in one shot without rewriting.
        # I will rewrite the inner loop to include busy time tracking.
        
        pass 

    # Since I cannot go back, I will provide the corrected full code below.
