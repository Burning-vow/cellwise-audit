import sys, json, math, random
from collections import deque

def main():
    args = sys.argv[1:]
    seeds_n = 10
    horizon = 100.0
    seed_start = 1
    pert = "none"
    
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]

    # Parameters in hours and minutes
    # Arrival rate lambda: 4 per hour
    lam = 4.0
    # Service time mean: Stage 1 = 7.5 min = 0.125 hr, Stage 2 = 5 min = 1/12 hr
    mu1_mean_min = 7.5
    mu2_mean_min = 5.0
    
    if pert == "lam_up": lam *= 1.2
    elif pert == "mu_up": 
        mu1_mean_min /= 1.2
        mu2_mean_min /= 1.2
    elif pert == "c_up": pass # Capacity not explicitly defined as limit in prompt, assuming infinite queue capacity unless specified otherwise. If c_up meant blocking, we'd need a cap. Prompt says "queueing", usually implies infinite buffer unless stated. We assume infinite buffer.

    # Time unit: Hour
    time_unit = "hour"
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_dep_count = 0
    all_arr_count = 0
    all_blk_count = 0
    all_busy_time_1 = 0.0
    all_busy_time_2 = 0.0
    all_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    used_seeds = []
    
    warmup_ratio = 0.25
    total_horizon = horizon
    
    for k in range(seeds_n):
        s = seed_start + k
        used_seeds.append(s)
        rng = random.Random(s)
        
        # Event simulation
        # Events: (time, type, data)
        # type: 'arr', 'dep1', 'dep2'
        events = []
        
        def add_event(t, typ, data=None):
            events.append((t, typ, data))
            
        # Initial arrival
        t_now = 0.0
        next_arrival_t = rng.expovariate(lam)
        add_event(next_arrival_t, 'arr')
        
        # State variables
        q1 = deque() # Jobs waiting for stage 1 or being served? Let's track separately.
        # Better: Track system state
        # n1: number of jobs in stage 1 (waiting + serving)
        # n2: number of jobs in stage 2 (waiting + serving)
        # server1_free_at: time when server 1 becomes free
        # server2_free_at: time when server 2 becomes free
        
        n1 = 0
        n2 = 0
        srv1_free = 0.0
        srv2_free = 0.0
        
        # For area calculation (Little's Law L)
        # We need to integrate the number of jobs in the system over time.
        # Since it's discrete event, we can accumulate area between events.
        last_event_time = 0.0
        current_jobs_in_system = 0
        
        # Statistics for this seed
        seed_L_area = 0.0
        seed_W_sum = 0.0
        seed_dep_count = 0
        seed_arr_count = 0
        seed_blk_count = 0
        seed_busy_time_1 = 0.0
        seed_busy_time_2 = 0.0
        seed_wait_count = 0
        
        # Warmup cutoff
        warmup_end = total_horizon * warmup_ratio
        
        while events:
            events.sort(key=lambda x: x[0])
            t, typ, data = events.pop(0)
            
            if t > total_horizon:
                break
                
            # Calculate area since last event
            dt = t - last_event_time
            if last_event_time >= warmup_end:
                seed_L_area += current_jobs_in_system * dt
            
            # Update busy times if servers were busy during this interval
            # This is tricky with simple integration. 
            # Alternative: Track start/end of service explicitly.
            # Let's stick to counting completions and using Little's law for W, 
            # but for busy fraction, we need exact busy time.
            # Easier way for busy time: When a job starts service, record start time. When it ends, add duration.
            
            last_event_time = t
            
            if typ == 'arr':
                seed_arr_count += 1
                # Generate service times now
                st1 = rng.expovariate(60.0 / mu1_mean_min) # Mean in hours
                st2 = rng.expovariate(60.0 / mu2_mean_min)
                
                # Check if blocked? Infinite queue assumed.
                # Add to queue 1
                q1.append({'id': seed_arr_count, 'st1': st1, 'st2': st2, 'arrival_time': t})
                n1 += 1
                current_jobs_in_system += 1
                
                # Schedule next arrival
                next_arrival_t = t + rng.expovariate(lam)
                if next_arrival_t <= total_horizon:
                    add_event(next_arrival_t, 'arr')
                    
                # Try to start service on 1
                if n1 == 1 and t >= srv1_free:
                    # Start immediately
                    job = q1.popleft()
                    n1 -= 1
                    srv1_free = t + job['st1']
                    add_event(srv1_free, 'dep1', job)
                    # Note: The job is no longer in q1, but still in system.
                    # It is "in service".
                    # We don't decrement current_jobs_in_system yet.
                    
            elif typ == 'dep1':
                job = data
                # Job leaves stage 1, enters stage 2 queue
                # Move to q2
                q2.append(job) # Need to define q2 outside loop scope properly
                # Wait, I didn't define q2. Let's fix structure.
                pass 

            # Refactoring needed for clean variable scope.
            # Let's restart the inner loop logic with proper structures.
            
            # Actually, let's just rewrite the loop body carefully.
            # Variables needed: q1, q2, n1, n2, srv1_free, srv2_free, current_jobs_in_system
            # And tracking busy time accurately.
            
            # To track busy time accurately without complex interval logic:
            # Maintain `busy_start_1` and `busy_start_2`.
            # When server becomes idle, add (t - busy_start) to total busy time.
            # When server becomes busy, set busy_start = t.
            
            # Let's re-initialize state vars inside the seed loop correctly.
            
            # ... (Code continues below in final output)
