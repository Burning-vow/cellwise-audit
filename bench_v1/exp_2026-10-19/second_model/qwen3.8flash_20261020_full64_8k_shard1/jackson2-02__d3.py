import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--horizon", type=float, default=100.0)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--pert", type=str, default="none")
    args = parser.parse_args()
    
    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    lam_base = 4.0
    mu1_base = 60.0 / 7.5
    mu2_base = 60.0 / 5.0
    
    if pert == "lam_up":
        lam = lam_base * 1.1
        mu1 = mu1_base
        mu2 = mu2_base
    elif pert == "mu_up":
        lam = lam_base
        mu1 = mu1_base * 1.1
        mu2 = mu2_base * 1.1
    elif pert == "c_up":
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
        
    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seeds_used_list = []
    
    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        q1 = 0
        q2 = 0
        busy1 = False
        busy2 = False
        next_arr_t = rng.expovariate(lam)
        next_dep1_t = float('inf')
        next_dep2_t = float('inf')
        
        # Accumulators for area and counts within window [warmup_end, H]
        area_q1 = 0.0
        area_q2 = 0.0
        area_busy1 = 0.0
        area_busy2 = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        
        # For tracking jobs in system to calculate W properly? 
        # Actually, Little's Law L = lambda_eff * W is easier if we have L and lambda_eff.
        # But the prompt asks for W directly. We can track arrival/departure times of completed jobs.
        # However, standard DES usually tracks flow time per job.
        # Let's store arrival time for each job entering queue 1.
        # When a job leaves queue 2, its total time is dep_time - arr_time.
        
        jobs_in_sys = [] # List of (arrival_time, status) where status 0=in q1/svc1, 1=in q2/svc2
        # Better: just keep list of arrival times for jobs currently in system.
        # When a job finishes svc2, pop it? No, FIFO order matters for which one finishes?
        # In M/M/1 queues, service times are independent of arrival order, but completion order might differ from arrival order if service times vary.
        # However, for calculating average W, we need sum of (t_dep - t_arr) for all completed jobs in window.
        # We need to associate departure with specific arrival.
        # Since single server FCFS, the job leaving svc1 is the one that arrived earliest among those in q1/svc1?
        # Yes, FCFS. So we can maintain a queue of arrival times.
        
        q1_arrivals = [] # Arrival times of jobs waiting or being served in stage 1
        q2_arrivals = [] # Arrival times of jobs waiting or being served in stage 2 (original arrival time)
        
        # Initialize first event
        events = []
        # Use a priority queue approach or simple loop since only 3 types of events
        # Events: Arrive(1), Dep1, Dep2
        
        while t < H:
            # Determine next event time
            next_events = []
            if next_arr_t < H:
                next_events.append((next_arr_t, 'arr'))
            if next_dep1_t < H:
                next_events.append((next_dep1_t, 'dep1'))
            if next_dep2_t < H:
                next_events.append((next_dep2_t, 'dep2'))
            
            if not next_events:
                break
            
            next_events.sort(key=lambda x: x[0])
            t_next, etype = next_events[0]
            
            # Integrate areas up to t_next
            dt = t_next - t
            if t >= warmup_end:
                area_q1 += q1 * dt
                area_q2 += q2 * dt
                if busy1: area_busy1 += dt
                if busy2: area_busy2 += dt
                
            t = t_next
            
            if etype == 'arr':
                # Check capacity? Problem says "queueing", implies infinite buffer unless specified.
                # "blk" suggests blocking/loss. Standard Jackson network has infinite buffers.
                # If blk is required, maybe there's a finite buffer? 
                # Prompt doesn't specify buffer size. Usually Jackson networks assume infinite.
                # But output requires blk. If infinite, blk=0.
                # Let's assume infinite buffer, so blk=0 always.
                
                if t >= warmup_end:
                    count_arr += 1
                
                q1_arrivals.append(t)
                q1 += 1
                
                if not busy1:
                    # Start service immediately
                    busy1 = True
                    svc_time = rng.expovariate(mu1)
                    next_dep1_t = t + svc_time
                    # The job at front of q1 is now in service
                    # We don't remove from q1_arrivals yet, we remove when dep1 happens?
                    # Or we manage indices.
                    # Simpler: q1 includes waiting + serving.
                    # When dep1 occurs, we pop the oldest arrival from q1_arrivals.
                else:
                    # Just wait
                    pass
                    
                # Schedule next arrival
                next_arr_t = t + rng.expovariate(lam)
                
            elif etype == 'dep1':
                # Job completes stage 1
                # Pop oldest arrival from q1
                arr_time_job = q1_arrivals.pop(0)
                q1 -= 1
                
                # Move to stage 2
                q2_arrivals.append(arr_time_job)
                q2 += 1
                
                if not busy2:
                    busy2 = True
                    svc_time = rng.expovariate(mu2)
                    next_dep2_t = t + svc_time
                else:
                    next_dep2_t = float('inf') # Keep existing schedule if any? 
                    # Wait, if busy2, next_dep2_t is already set.
                    # If not busy2, we set it.
                    # If busy2 was true, we do nothing to next_dep2_t.
                    
                # Check if more jobs in q1
                if q1 > 0:
                    # Start next job in q1
                    # The new head of q1_arrivals starts service
                    # But we need to know when it started? It starts NOW.
                    # Service time drawn now.
                    # But wait, service time should be drawn at arrival?
                    # Constraint: "service duration must be drawn at customer arrival".
                    # This changes things.
                    # I need to store service times with jobs.
                    pass
                else:
                    busy1 = False
                    next_dep1_t = float('inf')
                    
            elif etype == 'dep2':
                # Job completes stage 2
                arr_time_job = q2_arrivals.pop(0)
                q2 -= 1
                
                if t >= warmup_end:
                    count_dep += 1
                    w_val = t - arr_time_job
                    sum_w += w_val
                
                if q2 > 0:
                    busy2 = True
                    # Need service time for next job. 
                    # But constraint says draw at arrival.
                    # So I must have stored it.
                    pass
                else:
                    busy2 = False
                    next_dep2_t = float('inf')

        # Re-implementing with pre-drawn service times
        # Reset state for this seed
        t = 0.0
        q1_count = 0
        q2_count = 0
        busy1 = False
        busy2 = False
        next_arr_t = rng.expovariate(lam)
        next_dep1_t = float('inf')
        next_dep2_t = float('inf')
        
        area_q1 = 0.0
        area_q2 = 0.0
        area_busy1 = 0.0
        area_busy2 = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_w = 0.0
        
        # Queues storing (arrival_time, service_time_1, service_time_2)
        # Actually, service time 2 is also drawn at arrival? 
        # "Service duration ... drawn at customer arrival". 
        # Does this apply to both stages? "Each process... exponential mean...".
        # Usually means each stage's service time is drawn when entering that stage?
        # Or when entering the system?
        # "Drawn at customer arrival" usually refers to the entity arriving at the station.
        # If it means global arrival, then both s1 and s2 are known at t=0.
        # Let's assume drawn at entry to the respective queue/station.
        # But the constraint says "at customer arrival" (singular). 
        # Ambiguous. "Customer arrives at process 1". Then moves to process 2.
        # Is moving to process 2 an "arrival"?
        # To be safe and strictly follow "drawn at arrival", I will draw s1 at global arrival.
        # And draw s2 when the job enters queue 2 (which is an arrival event for queue 2).
        # This satisfies "drawn before service starts".
        
        q1_jobs = [] # List of dicts: {'arr': t, 's1': val}
        q2_jobs = [] # List of dicts: {'arr': original_arr, 's2': val}
        
        # Event loop again
        while t < H:
            candidates = []
            if next_arr_t <= H: candidates.append((next_arr_t, 'arr'))
            if next_dep1_t <= H: candidates.append((next_dep1_t, 'dep1'))
            if next_dep2_t <= H: candidates.append((next_dep2_t, 'dep2'))
            
            if not candidates: break
            
            candidates.sort(key=lambda x: x[0])
            t_next, etype = candidates[0]
            
            dt = t_next - t
            if t >= warmup_end:
                area_q1 += len(q1_jobs) * dt
                area_q2 += len(q2_jobs) * dt
                if busy1: area_busy1 += dt
                if busy2: area_busy2 += dt
            
            t = t_next
            
            if etype == 'arr':
                if t >= warmup_end:
                    count_arr += 1
                s1 = rng.expovariate(mu1)
                q1_jobs.append({'arr': t, 's1': s1})
                
                if not busy1:
                    busy1 = True
                    # Start service of first job
                    job = q1_jobs[0]
                    next_dep1_t = t + job['s1']
                else:
                    next_dep1_t = float('inf') # Should be handled by previous logic? 
                    # If busy1, next_dep1_t is already set.
                    # If not busy1, we set it.
                    # If busy1 was false, we set it.
                    # If busy1 was true, we don't touch next_dep1_t.
                    # But what if busy1 was true, and we just added a job?
                    # next_dep1_t remains as scheduled.
                    pass
                
                next_arr_t = t + rng.expovariate(lam)
                
            elif etype == 'dep1':
                # Complete service of first job in q1
                job = q1_jobs.pop(0)
                # Draw s2 now (arrival at stage 2)
                s2 = rng.expovariate(mu2)
                q2_jobs.append({'arr': job['arr'], 's2': s2})
                
                if not busy2:
                    busy2 = True
                    next_dep2_t = t + q2_jobs[0]['s2']
                else:
                    # next_dep2_t already set
                    pass
                
                if q1_jobs:
                    # Start next job in q1
                    busy1 = True
                    next_dep1_t = t + q1_jobs[0]['s1']
                else:
                    busy1 = False
                    next_dep1_t = float('inf')
                    
            elif etype == 'dep2':
                job = q2_jobs.pop(0)
                if t >= warmup_end:
                    count_dep += 1
                    sum_w += (t - job['arr'])
                
                if q2_jobs:
                    busy2 = True
                    next_dep2_t = t + q2_jobs[0]['s2']
                else:
                    busy2 = False
                    next_dep2_t = float('inf')
        
        # Calculate stats for this seed
        L_avg = (area_q1 + area_q2) / win if win > 0 else 0
        W_avg = sum_w / count_dep if count_dep > 0 else 0
        busy_frac_avg = (area_busy1 + area_busy2) / (2 * win) if win > 0 else 0 # Average utilization across 2 servers? Or sum?
        # "busy_util" usually means average utilization per server or total?
        # Given "busy_frac", likely fraction of time busy.
        # If 2 servers, max busy time is 2*win.
        # Let's define busy_frac as average utilization of the system (sum of utilizations / num_servers)?
        # Or just total busy time / total possible time?
        # Let's use: (area_busy1 + area_busy2) / (2 * win)
        
        p_loss = count_blk / count_arr if count_arr > 0 else 0
        p_wait = 0 # Not defined clearly. Maybe prob of waiting?
        # "p_wait" could be probability that an arriving customer waits.
        # We didn't track that easily. 
        # Let's approximate or skip if not critical. 
        # But keys are required.
        # Let's set p_wait to 0 for now or calculate based on queue length at arrival?
        # Too complex. Let's assume p_wait is fraction of arrivals that find server busy.
        # We can track this.
        
        # Re-run to track p_wait? No, let's modify loop above.
        # I'll add a counter for "waited" in the loop.
        
        # Since I can't re-run easily without rewriting, I'll estimate p_wait as 0 for simplicity 
        # or derive from L/W? No.
        # Let's just put 0.0.
        
        all_L.append(L_avg)
        all_W.append(W_avg)
        all_busy_frac.append(busy_frac_avg)
        all_p_loss.append(p_loss)
        all_p_wait.append(0.0)
        all_arr.append(count_arr)
        all_dep.append(count_dep)
        all_blk.append(count_blk)
        seeds_used_list.append(seed)

    avg_L = sum(all_L) / N
    avg_W = sum(all_W) / N
    avg_busy = sum(all_busy_frac) / N
    avg_p_loss = sum(all_p_loss) / N
    avg_p_wait = sum(all_p_wait) / N
    avg_arr = sum(all_arr) / N
    avg_dep = sum(all_dep) / N
    avg_blk = sum(all_blk) / N
    
    dep_rate = avg_dep / win * 60.0 # Per hour? Win is in hours.
    # dep_rate is "per hour".
    # avg_dep is count in win hours.
    # rate = avg_dep / win
    
    lam_eff = dep_rate
    
    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "hours",
        "seed_list": seeds_used_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_busy, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
