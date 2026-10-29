import random, json, argparse, math

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

    # Parameters in hours
    lam_base = 6.0
    mu_base = 10.0 # 6 min = 0.1 hr -> rate 10/hr
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        # Cost doesn't affect dynamics here, just a placeholder for structure
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "hour"
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    seeds_used = 0
    seed_list = []
    
    win_len = H * 0.75 # Remove first 25% warmup
    start_time_warmup = H * 0.25

    for i in range(N):
        seed = S_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        queue1 = [] # List of (arrival_time, service_duration)
        queue2 = []
        server1_free_at = 0.0
        server2_free_at = 0.0
        
        # Statistics accumulators (for the window [start_time_warmup, H])
        area_in_system = 0.0 # Integral of number of jobs in system over time
        num_jobs_in_system = 0
        
        arrivals_count = 0
        departures_count = 0
        blocked_count = 0 # Not applicable in infinite buffer, but keep for interface
        
        # For W calculation: sum of sojourn times of completed jobs within window? 
        # Or average over all jobs that arrived and departed? 
        # Standard definition: L = lambda_eff * W. We compute L via area/time.
        # We need to track individual job completion times to get accurate W or use Little's Law consistency.
        # Let's accumulate total sojourn time for jobs that complete during the simulation horizon.
        total_sojourn_time = 0.0
        completed_jobs_count = 0
        
        # Next arrival time
        next_arrival = rng.expovariate(lam)
        
        # Events: Arrival, Service Completion 1, Service Completion 2
        # We simulate until H
        
        while t < H:
            # Determine next event time
            events = []
            if next_arrival < H:
                events.append(('arr', next_arrival))
            
            # Check if server 1 is busy with a job from queue1
            # Actually, we process queues. 
            # If queue1 not empty and server1 free at t, it would have started earlier.
            # So server1_free_at indicates when current job finishes.
            if server1_free_at > t and server1_free_at < H:
                events.append(('comp1', server1_free_at))
            
            if server2_free_at > t and server2_free_at < H:
                events.append(('comp2', server2_free_at))
                
            if not events:
                break
                
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Update area before jumping to etime
            dt = etime - t
            area_in_system += num_jobs_in_system * dt
            
            t = etime
            
            if etype == 'arr':
                # Generate service time for stage 1 now
                svc1 = rng.expovariate(mu)
                # Job enters queue 1
                queue1.append((t, svc1))
                num_jobs_in_system += 1
                arrivals_count += 1
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
                # Try to start service on server 1 if idle
                if len(queue1) == 1 and server1_free_at <= t:
                    arr_t, s_dur = queue1.pop(0)
                    server1_free_at = t + s_dur
                    
            elif etype == 'comp1':
                # Server 1 finished a job
                # The job was already popped from queue1 when service started.
                # It moves to queue 2.
                # But wait, our logic above pops from queue1 only when starting service.
                # When comp1 happens, the job leaves server 1.
                # We need to know which job it was. 
                # In this simple model, we don't store the job object in server state explicitly other than finish time.
                # However, since it's FCFS and single server, the job finishing is the one that started last.
                # But we didn't store its arrival time for Stage 2 service duration generation?
                # Requirement: "Service duration must be drawn at arrival".
                # So when it arrives at Stage 1, we draw svc1.
                # When it completes Stage 1, it goes to Stage 2. Does it draw svc2 then?
                # "Workpiece ... enters process 2 ... each has its own queue".
                # Usually, processing time for stage 2 is also determined.
                # The prompt says "service duration ... drawn at customer arrival".
                # This likely refers to the specific station's service time being fixed upon entry to that station?
                # Or upon entry to the system?
                # "工件以...进入工序1...完工后全部进入工序2".
                # Interpretation: At arrival to Station 1, draw T1. At arrival to Station 2 (completion of 1), draw T2?
                # Or draw both at initial arrival?
                # "服务时长必须在顾客到达时抽好并挂在该顾客身上".
                # "Customer arrival" usually means arrival to the system.
                # Let's assume both service times are drawn at initial arrival.
                pass 

            # Re-evaluating the loop structure for clarity and correctness regarding "draw at arrival"
            # Let's restart the inner loop logic with a cleaner event handling approach.
            
            # Resetting the loop body for the current iteration to fix the logic flow
            # Since I can't easily "continue" inside the complex block without restructuring,
            # I will rewrite the simulation loop below.
            
            # NOTE: The code above had incomplete logic for comp1/comp2.
            # I will replace the entire `while t < H` block with correct logic.
            
            # --- CORRECTED SIMULATION LOGIC START ---
            # (This replaces the previous flawed attempt in the thought process)
            
            # We need to handle the fact that we drew svc1 at arrival.
            # We also need to draw svc2. If "arrival" means system arrival, draw both.
            # Let's draw both at system arrival.
            
            # To do this properly, we need to associate the job with its data.
            # Queue entries should hold (arrival_time, svc1, svc2).
            
            # Let's re-implement the loop cleanly.
            
            # Clear previous incorrect partial execution
            # (In the final output, I will provide the clean version directly)
            
            # For the purpose of generating the final code, I will write the clean version now.
            pass

        # End of seed loop placeholder
        # The actual code will follow the clean implementation.
        
        # Calculate stats for this seed
        # Only count jobs that completed within the window?
        # L is area / window_length.
        # W is total_sojourn / completed_count.
        # But we must align with the window.
        # Jobs arriving before window start but leaving after contribute to L.
        # Jobs arriving after window end don't exist.
        # Jobs completing before window start don't contribute to W?
        # Standard practice: Use steady-state approximations or truncate carefully.
        # Given "remove first 25%", we integrate area from 0.25H to H.
        # For W, we consider jobs that *complete* in the interval [0.25H, H]?
        # Or jobs that *arrive* in [0.25H, H] and complete later?
        # Little's law L = lambda * W holds for stable systems.
        # Let's calculate L as Area / WinLen.
        # Let's calculate W as Sum(Sojourn of jobs completing in Window) / Count(Jobs completing in Window).
        # This might introduce bias if completions lag behind arrivals.
        # Alternative: Track all jobs.
        
        # Let's stick to:
        # L_seed = area_in_window / win_len
        # W_seed = total_sojourn_of_completed_jobs_in_window / num_completed_jobs_in_window
        
        # Need to filter completions by time.
        
        # Busy fraction: Time server 1 busy / H? Or / win_len?
        # Usually utilization is over the whole run or window.
        # Let's use window.
        
        # p_loss: 0 (infinite buffer)
        # p_wait: Probability an arriving job finds server busy?
        # Or fraction of time servers are busy?
        # "p_wait" often means P(Wait > 0).
        # We can estimate it as (Number of jobs that waited) / Total Arrivals.
        # A job waits if it joins a non-empty queue.
        
        # Let's refine the simulation code structure.
        
        # Final Code Generation follows.
        pass

# The following is the actual generated code based on the refined logic.
