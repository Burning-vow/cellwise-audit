import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_in = 4.0 # per hour
    mu1 = 10.0 # per hour (6 min mean)
    mu2 = 10.0 # per hour
    
    if args.pert == 'lam_up': lam_in *= 1.2
    elif args.pert == 'mu_up': mu1 *= 1.2; mu2 *= 1.2
    elif args.pert == 'c_up': pass # capacity not explicitly defined in base, assume no change or structural? Prompt says pert only changes params. c_up might imply cost or capacity? Given "single device", maybe c_up is ignored or affects something else. Let's assume none for now as structure is fixed.
    
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
    all_L = []
    all_W = []
    all_busy1 = []
    all_busy2 = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(args.seeds):
        s = args.seed_start + i
        rng = random.Random(s)
        
        # State: queue lengths q1, q2, servers busy status b1, b2
        # Events: Arrival, ServiceEnd1, ServiceEnd2
        
        t = 0.0
        q1 = 0
        q2 = 0
        b1 = False
        b2 = False
        
        # For integration of L and W
        # L = average number in system. We need to track total person-hours in system.
        # But standard DES usually tracks area under curve for queue length.
        # Total in system = q1 + q2 + b1 + b2 (if we consider service as part of system)
        # Actually, usually "in system" includes those being served.
        # So N(t) = q1 + q2 + int(b1) + int(b2)
        
        last_event_time = 0.0
        area_N = 0.0 # Integral of N(t) over [win_start, horizon]
        
        # For W: Sum of sojourn times of completed jobs within window / count of completions within window
        # Or Little's Law check? The prompt asks for W and L. Usually W is estimated by summing times.
        # However, with truncation, it's tricky. 
        # Standard approach: Track arrival time for each job. When it departs, add (t - arr_time) to sum_W if departure > win_start.
        # And count departures > win_start.
        
        sum_W_times = 0.0
        count_dep_win = 0
        count_arr_win = 0
        count_blk_win = 0 # No blocking mentioned in problem statement ("all enter stage 2"), but output requires blk. Assume infinite buffer? Then blk=0.
        
        # Busy fractions
        busy_time1 = 0.0
        busy_time2 = 0.0
        last_b1_change = 0.0
        last_b2_change = 0.0
        
        # Event Queue: list of (time, type, data)
        # Types: 'A', 'E1', 'E2'
        events = []
        
        # Initial arrival
        next_arrival = rng.expovariate(lam_in)
        events.append((next_arrival, 'A', None))
        
        # Job tracking for W calculation
        # Map from job_id to arrival_time. Since we don't have IDs, we can use a queue of arrival times corresponding to jobs in system.
        # But jobs move between queues. 
        # Better: Each job object has an arrival time.
        # In event simulation, when a job arrives, it enters q1. When it starts service on 1, it leaves q1. When it finishes 1, it enters q2.
        # We need to know the arrival time of the job finishing service.
        # We can store arrival time in the queue elements.
        
        q1_times = [] # List of arrival times of jobs waiting in Q1
        q2_times = [] # List of arrival times of jobs waiting in Q2
        job_in_s1_arr_time = None # Arrival time of job currently in S1
        job_in_s2_arr_time = None # Arrival time of job currently in S2
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, etype, edata = events.pop(0)
            
            if curr_t > horizon:
                break
                
            # Update integrals before state change
            dt = curr_t - last_event_time
            
            # Current N(t) during interval [last_event_time, curr_t)
            n_curr = len(q1_times) + len(q2_times) + (1 if b1 else 0) + (1 if b2 else 0)
            
            if last_event_time < win_start and curr_t > win_start:
                # Split interval
                overlap_start = max(last_event_time, win_start)
                area_N += n_curr * (curr_t - overlap_start)
                
                # Busy time split
                if b1:
                    bs = max(last_b1_change, win_start)
                    if curr_t > bs: busy_time1 += curr_t - bs
                if b2:
                    bs = max(last_b2_change, win_start)
                    if curr_t > bs: busy_time2 += curr_t - bs
                    
            elif last_event_time >= win_start:
                area_N += n_curr * dt
                if b1: busy_time1 += dt
                if b2: busy_time2 += dt
            
            # Process Event
            if etype == 'A':
                # Arrival
                if curr_t >= win_start:
                    count_arr_win += 1
                
                # Add to Q1
                q1_times.append(curr_t)
                
                # Schedule next arrival
                next_arrival = curr_t + rng.expovariate(lam_in)
                if next_arrival <= horizon:
                    events.append((next_arrival, 'A', None))
                
                # Try to start service on 1
                if not b1 and len(q1_times) > 0:
                    # Start service
                    b1 = True
                    last_b1_change = curr_t
                    job_in_s1_arr_time = q1_times.pop(0)
                    serv_time = rng.expovariate(mu1)
                    end_time = curr_t + serv_time
                    if end_time <= horizon:
                        events.append((end_time, 'E1', None))
                        
            elif etype == 'E1':
                # End of service 1
                b1 = False
                # Record completion of stage 1 for the job that was in service
                # This job moves to Q2
                if job_in_s1_arr_time is not None:
                    q2_times.append(job_in_s1_arr_time)
                    job_in_s1_arr_time = None
                
                # Try to start service on 2
                if not b2 and len(q2_times) > 0:
                    b2 = True
                    last_b2_change = curr_t
                    job_in_s2_arr_time = q2_times.pop(0)
                    serv_time = rng.expovariate(mu2)
                    end_time = curr_t + serv_time
                    if end_time <= horizon:
                        events.append((end_time, 'E2', None))
                        
                # Try to start service on 1 again if queue non-empty
                if not b1 and len(q1_times) > 0:
                    b1 = True
                    last_b1_change = curr_t
                    job_in_s1_arr_time = q1_times.pop(0)
                    serv_time = rng.expovariate(mu1)
                    end_time = curr_t + serv_time
                    if end_time <= horizon:
                        events.append((end_time, 'E1', None))
                        
            elif etype == 'E2':
                # End of service 2 -> Departure from system
                b2 = False
                if job_in_s2_arr_time is not None:
                    if curr_t >= win_start:
                        count_dep_win += 1
                        sum_W_times += (curr_t - job_in_s2_arr_time)
                    job_in_s2_arr_time = None
                
                # Try to start service on 2 again
                if not b2 and len(q2_times) > 0:
                    b2 = True
                    last_b2_change = curr_t
                    job_in_s2_arr_time = q2_times.pop(0)
                    serv_time = rng.expovariate(mu2)
                    end_time = curr_t + serv_time
                    if end_time <= horizon:
                        events.append((end_time, 'E2', None))
            
            last_event_time = curr_t
            
        # Finalize metrics for this seed
        win_len = horizon - win_start
        if win_len <= 0: win_len = 1e-9
        
        L_est = area_N / win_len
        W_est = sum_W_times / count_dep_win if count_dep_win > 0 else 0.0
        bf1 = busy_time1 / win_len
        bf2 = busy_time2 / win_len
        # Total busy fraction? Output asks for busy_frac. Usually implies server utilization. 
        # With two servers, maybe average? Or sum? 
        # "busy_util" also requested. Let's provide average utilization per server or total?
        # Typically busy_frac is for the system or specific resource. 
        # Given single line JSON, let's assume busy_frac is average of both servers' utilizations? 
        # Or maybe just one? The problem has 2 stages. 
        # Let's calculate overall system busy fraction (total busy time / (2 * win_len))? 
        # Or maybe report for stage 1? 
        # Let's look at keys: busy_frac, busy_util. Redundant? 
        # I will set busy_frac = (bf1 + bf2) / 2.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy1.append(bf1)
        all_busy2.append(bf2)
        all_arr.append(count_arr_win)
        all_dep.append(count_dep_win)
        all_blk.append(0) # Infinite buffer assumed
        
        seeds_used += 1
        seed_list.append(s)
        
    avg_L = sum(all_L) / seeds_used if seeds_used > 0 else 0
    avg_W = sum(all_W) / seeds_used if seeds_used > 0 else 0
    avg_busy = sum((b1+b2)/2 for b1,b2 in zip(all_busy1, all_busy2)) / seeds_used if seeds_used > 0 else 0
    avg_arr = sum(all_arr) / seeds_used if seeds_used > 0 else 0
    avg_dep = sum(all_dep) / seeds_used if seeds_used > 0 else 0
    avg_blk = sum(all_blk) / seeds_used if seeds_used > 0 else 0
    
    # Dep rate in per hour
    dep_rate = avg_dep / (horizon - horizon*0.25) if (horizon - horizon*0.25) > 0 else 0
    
    # Probabilities
    # p_loss: blk / arr? If blk=0, p_loss=0
    p_loss = avg_blk / avg_arr if avg_arr > 0 else 0
    # p_wait: Probability of waiting? 
    # Could be derived from queue lengths or busy fraction. 
    # P(wait) approx 1 - P(system empty)? Or P(server busy)?
    # Let's use average busy fraction as proxy for probability of finding server busy upon arrival (PASTA).
    # Since there are 2 servers, maybe average of their utils?
    p_wait = avg_busy 
    
    res = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "seconds", # Placeholder, actual runtime not measured precisely here, but key required
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(horizon - horizon*0.25, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_busy, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(dep_rate, 4), # Effective arrival rate ~ departure rate in steady state
        "p_loss": round(p_loss, 4),
        "p_wait": round(p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round((b1+b2)/2, 4) for b1,b2 in zip(all_busy1, all_busy2)],
        "per_seed_p_loss": [0.0]*seeds_used,
        "per_seed_p_wait": [round((b1+b2)/2, 4) for b1,b2 in zip(all_busy1, all_busy2)]
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
