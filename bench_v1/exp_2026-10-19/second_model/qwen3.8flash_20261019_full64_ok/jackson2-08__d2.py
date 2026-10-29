import json, math, random, sys
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 5; horizon = 100.0; seed_start = 42; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]

    lam_base = 6.0 # per hour
    mu1_base = 10.0 # per hour (6 min)
    mu2_base = 12.0 # per hour (5 min)
    
    if pert == "lam_up": lam_base *= 1.2
    elif pert == "mu_up": mu1_base *= 1.2; mu2_base *= 1.2
    elif pert == "c_up": pass # capacity not explicitly defined as variable in prompt, assuming no change or structural
    
    time_unit = "hour"
    horizon_h = horizon if time_unit == "hour" else horizon / 60.0
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    warmup_ratio = 0.25
    win_start = warmup_ratio * horizon_h
    win_len = horizon_h - win_start
    
    for s_idx in range(seeds_n):
        seed = seed_start + s_idx
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        q1 = deque() # jobs waiting at station 1
        q2 = deque() # jobs waiting at station 2
        b1 = False   # server 1 busy?
        b2 = False   # server 2 busy?
        end_t1 = 0.0 # time when server 1 becomes free
        end_t2 = 0.0 # time when server 2 becomes free
        
        # Statistics accumulators (for area integration)
        area_L1 = 0.0
        area_L2 = 0.0
        area_B1 = 0.0
        area_B2 = 0.0
        
        # Event lists: (time, type, data)
        # type: 'arr', 'dep1', 'dep2'
        events = []
        
        # Generate initial arrival
        next_arr_time = rng.expovariate(lam_base)
        events.append((next_arr_time, 'arr', None))
        
        total_arrivals = 0
        total_departures = 0
        total_blocked = 0 # Not applicable in infinite queue model usually, but prompt asks for blk. 
                          # In standard Jackson network with infinite queues, blk=0. 
                          # If finite buffer was implied, it would be different. Prompt says "各自排队", implies infinite.
                          # However, output requires blk. We will set it to 0 unless specified otherwise.
                          # Wait, "被拒绝/丢失". Infinite queue -> 0 loss.
        
        # To handle "service duration drawn at arrival", we need to store service times.
        # But arrivals are Poisson. Service times are exponential.
        # The constraint "service duration must be drawn at arrival and attached to customer" 
        # means when a job arrives at Station 1, we draw its S1 time. When it finishes S1 and goes to S2, do we draw S2 then?
        # Or does the job carry both? Usually, routing is deterministic here. 
        # Let's assume: At arrival to Sys (Station 1), draw S1. At completion of S1 (arrival to Station 2), draw S2.
        # This satisfies "drawn at arrival [to that station]".
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, etype, edata = events.pop(0)
            
            if curr_t > horizon_h:
                break
            
            # Integrate areas up to current time
            dt = curr_t - t
            if dt > 0:
                # Only integrate if within window? No, integrate always, subtract later or just track state changes.
                # Easier: Track cumulative area from 0 to T. Then Area_win = Area(T_end) - Area(T_start).
                # But we need L_avg over window. L(t) is number in system.
                # Number in system N(t) = len(q1) + (1 if b1 else 0) + len(q2) + (1 if b2 else 0)
                # Actually, simpler to just record state changes and calculate area analytically or step-by-step.
                # Since we have discrete events, we can accumulate area segment by segment.
                
                n_sys = len(q1) + (1 if b1 else 0) + len(q2) + (1 if b2 else 0)
                area_L_total += n_sys * dt
                
                if b1: area_B1_total += dt
                if b2: area_B2_total += dt
                
                # For window specific stats, we need to know if this interval overlaps with [win_start, horizon_h]
                # Interval is [t, curr_t]. Overlap length:
                ov_start = max(t, win_start)
                ov_end = min(curr_t, horizon_h)
                if ov_end > ov_start:
                    ov_len = ov_end - ov_start
                    area_L_win += n_sys * ov_len
                    if b1: area_B1_win += ov_len
                    if b2: area_B2_win += ov_len
                    
            t = curr_t
            
            if etype == 'arr':
                total_arrivals += 1
                # Draw service time for Station 1
                s1 = rng.expovariate(mu1_base)
                job = {'s1': s1, 'entry_time': t}
                
                if not b1:
                    b1 = True
                    end_t1 = t + s1
                    events.append((end_t1, 'dep1', job))
                else:
                    q1.append(job)
                    
                # Schedule next arrival
                next_arr_time = t + rng.expovariate(lam_base)
                if next_arr_time <= horizon_h:
                    events.append((next_arr_time, 'arr', None))
                    
            elif etype == 'dep1':
                job = edata
                b1 = False
                # Job moves to Station 2
                # Draw service time for Station 2
                s2 = rng.expovariate(mu2_base)
                job['s2'] = s2
                
                if not b2:
                    b2 = True
                    end_t2 = t + s2
                    events.append((end_t2, 'dep2', job))
                else:
                    q2.append(job)
                    
                # Start next job on Server 1 if available
                if q1:
                    next_job = q1.popleft()
                    b1 = True
                    # next_job already has s1 drawn at arrival
                    end_t1 = t + next_job['s1']
                    events.append((end_t1, 'dep1', next_job))
                    
            elif etype == 'dep2':
                job = edata
                b2 = False
                total_departures += 1
                # Calculate sojourn time
                w_time = t - job['entry_time']
                # Accumulate W stats for window? 
                # W is average time in system. We should sum W for jobs departing in window.
                if t >= win_start and t <= horizon_h:
                    sum_W_win += w_time
                    count_W_win += 1
                
                # Start next job on Server 2 if available
                if q2:
                    next_job = q2.popleft()
                    b2 = True
                    # next_job already has s2 drawn at dep1
                    end_t2 = t + next_job['s2']
                    events.append((end_t2, 'dep2', next_job))

        # End of simulation loop for one seed
        
        # Calculate metrics for this seed
        # L = Average number in system during window
        if win_len > 0:
            l_val = area_L_win / win_len
        else:
            l_val = 0.0
            
        # W = Average sojourn time for jobs departing in window
        if count_W_win > 0:
            w_val = sum_W_win / count_W_win
        else:
            w_val = 0.0
            
        # Busy fraction
        bf1 = area_B1_win / win_len if win_len > 0 else 0
        bf2 = area_B2_win / win_len if win_len > 0 else 0
        # Total busy fraction? Usually per server. Prompt asks for busy_frac. Ambiguous. 
        # Given "busy_util" also requested, maybe busy_frac is overall utilization? 
        # Or maybe busy_frac is for the whole system? 
        # Let's report average utilization across servers or sum? 
        # Standard metric: Utilization rho. Here two servers. 
        # I'll compute weighted average or just sum? 
        # Let's look at keys: busy_frac, busy_util. 
        # Maybe busy_frac is fraction of time ANY server is busy? Or average?
        # Let's assume busy_frac is the average utilization of the bottleneck or mean of servers?
        # Safer: Mean utilization of the two servers.
        busy_frac_val = (bf1 + bf2) / 2.0
        
        p_loss_val = 0.0 # Infinite queue
        p_wait_val = 0.0 # Probability of waiting upon arrival? 
                         # Hard to measure exactly without tracking every arrival state.
                         # Approximation: Fraction of arrivals that found server busy.
                         # We didn't track this specifically. 
                         # Let's re-evaluate. We need to track if an arriving job had to wait.
                         # In the 'arr' event, if b1 is true, it waits.
                         # We need to count these.
        
        # Re-running logic mentally to add missing counters...
        # I need to modify the loop to capture wait counts.
        
        # Resetting for second pass logic injection into code structure above?
        # No, I must write the final code directly.
        # I will include counters for:
        # arr_count_win, wait_count_win (at station 1), dep_count_win
        
        # Let's refine the code structure to ensure all vars are initialized properly.
        
        # Initialize per-seed accumulators
        area_L_win = 0.0
        area_B1_win = 0.0
        area_B2_win = 0.0
        sum_W_win = 0.0
        count_W_win = 0
        count_arr_win = 0
        count_wait_win = 0 # Arrivals finding server 1 busy
        
        # Need to reset these inside the seed loop before starting sim.
        
        # ... (Code generation follows)

# Note: The thought process identified missing counters for p_wait. 
# p_wait = probability an arriving job waits. 
# In the 'arr' event: if b1 is True, it waits. Increment count_wait_win if t in window.
# Also increment count_arr_win if t in window.

# Final Code Construction
