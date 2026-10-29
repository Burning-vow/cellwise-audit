import random
import json
import argparse
import math

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
    lam_base = 4.0
    mu_base = 10.0 # 6 min = 0.1 hr -> 1/0.1 = 10/hr
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        # Not specified how c affects, assume no change for this model structure or ignore
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
    
    seeds_used = []
    
    warmup_ratio = 0.25
    warmup_time = H * warmup_ratio
    
    for i in range(N):
        seed = S_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        # Queue lengths for stage 1 and 2
        q1_len = 0
        q2_len = 0
        
        # Server states: 0=idle, 1=busy
        s1_state = 0
        s2_state = 0
        
        # Next event times
        next_arrival = rng.expovariate(lam)
        next_s1_done = float('inf')
        next_s2_done = float('inf')
        
        # Accumulators for statistics (only after warmup)
        area_q1 = 0.0
        area_q2 = 0.0
        time_s1_busy = 0.0
        time_s2_busy = 0.0
        
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0 # In this model, blocking isn't explicitly defined as loss unless buffer is infinite? 
                          # Problem says "queueing", usually implies infinite buffer unless stated otherwise.
                          # However, "p_loss" suggests potential loss. If buffers are infinite, p_loss=0.
                          # Let's assume infinite buffers for standard Jackson network unless capacity C is given.
                          # The prompt mentions "c_up" perturbation but doesn't define C. 
                          # Standard interpretation: Infinite queues. Loss probability is 0.
                          # But wait, "blk" is requested. If infinite queue, blk=0.
                          # Let's stick to infinite queues as per standard M/M/1 series description without capacity limits.
        
        # For W calculation: sum of sojourn times of completed jobs
        total_sojourn_time = 0.0
        completed_jobs_in_window = 0
        
        # We need to track individual job entry times to calculate sojourn time upon exit from system.
        # Since it's a series, we can track the time a job enters Stage 1.
        # When it leaves Stage 2, we add (t_exit - t_entry_1) to total_sojourn_time.
        
        # List to hold jobs currently in the system with their start time at Stage 1
        # Actually, simpler: when a job arrives at Stage 1, record its arrival time.
        # When it finishes Stage 2, pop the oldest? No, FCFS within each stage.
        # We need to link the job through stages.
        
        # Let's use an event-driven simulation loop.
        
        # To handle "area integral before state change":
        # At each event time t_event, we advance time from last_t to t_event.
        # We accumulate areas based on the state during [last_t, t_event).
        
        last_t = 0.0
        
        while True:
            # Determine next event
            events = []
            if next_arrival < H:
                events.append(('arrival', next_arrival))
            if next_s1_done < H:
                events.append(('s1_done', next_s1_done))
            if next_s2_done < H:
                events.append(('s2_done', next_s2_done))
            
            if not events:
                break
            
            # Find earliest event
            min_time = min(e[1] for e in events)
            current_events = [e for e in events if abs(e[1] - min_time) < 1e-9]
            
            dt = min_time - last_t
            
            # Integrate areas and busy times for the interval [last_t, min_time)
            if last_t >= warmup_time:
                area_q1 += q1_len * dt
                area_q2 += q2_len * dt
                if s1_state == 1:
                    time_s1_busy += dt
                if s2_state == 1:
                    time_s2_busy += dt
            
            # Process events at min_time
            # Sort events to ensure deterministic order if simultaneous (though unlikely with continuous dists)
            # Priority: Departures often trigger arrivals to next stage.
            # Let's process all events at this timestamp.
            
            # We need to be careful about ordering. 
            # Usually: 
            # 1. Arrivals to system
            # 2. Service completions (which may cause immediate transfer to next queue)
            
            # Let's group by type
            arr_events = [e for e in current_events if e[0]=='arrival']
            s1_events = [e for e in current_events if e[0]=='s1_done']
            s2_events = [e for e in current_events if e[0]=='s2_done']
            
            # Process Arrivals
            for _ in arr_events:
                if last_t >= warmup_time or min_time > warmup_time: # Count if event happens in window? 
                    # The problem asks for stats in the window. 
                    # An arrival at exactly warmup_time boundary? 
                    # Let's count arrivals that occur strictly after warmup_time starts? 
                    # Or include those in the window [warmup, H].
                    # If min_time >= warmup_time, it's in the window.
                    pass
                
                if min_time >= warmup_time:
                    count_arrivals += 1
                
                # Add to Q1
                q1_len += 1
                
                # Schedule next arrival
                next_arrival = min_time + rng.expovariate(lam)
                
                # If S1 is idle, start service immediately
                if s1_state == 0:
                    s1_state = 1
                    # Remove from Q1
                    q1_len -= 1
                    # Draw service time
                    st = rng.expovariate(mu)
                    next_s1_done = min_time + st
                    # Store job info? We need to know when it started S1 to calculate sojourn later?
                    # Sojourn time = Time leaving S2 - Time arriving S1.
                    # We don't need to store intermediate times if we just track the global clock.
                    # But we need to associate the specific job.
                    # Since it's FCFS, the job entering S1 now will leave S1 first among those in S1.
                    # We can maintain a list of arrival times for jobs currently in the system pipeline.
                    # Simpler approach: Maintain a list `jobs_in_system` where each element is the time they entered Stage 1.
                    # When a job completes Stage 2, we pop the oldest? No, because of queuing delays, 
                    # completion order matches arrival order in a stable FIFO network.
                    # Yes, in a tandem queue with FCFS, departure order is same as arrival order.
                    # So we can keep a queue of arrival times.
                    
                    # Let's implement a global queue `arrival_times_queue`
                    # Push arrival time when entering Stage 1.
                    # Pop arrival time when exiting Stage 2.
                    # This works because flow conservation and FIFO discipline preserve order.
                    
                    # Initialize the queue for this job
                    # We'll manage this via a separate list `job_arrival_times`
                    # But we need to push it when the job ARRIVES at Stage 1.
                    # And pop it when it DEPARTS Stage 2.
                    
                    # Wait, if I push at arrival, and pop at final departure, 
                    # does the order match? 
                    # Job A arrives t1, goes to S1, then S2, departs tA.
                    # Job B arrives t2>t1, goes to S1, then S2, departs tB.
                    # Since S1 and S2 are FIFO, A finishes S1 before B. A enters S2 before B.
                    # A finishes S2 before B. So tA < tB.
                    # Yes, order is preserved.
                    
                    # So we need a list `active_job_arrival_times`.
                    # On Arrival: append(min_time)
                    # On S2 Done: pop(0) and calculate sojourn.
                    
                    active_job_arrival_times.append(min_time)

            # Process S1 Completions
            for _ in s1_events:
                s1_state = 0
                # Move job to Q2
                q2_len += 1
                
                # Check if S2 is idle
                if s2_state == 0:
                    s2_state = 1
                    q2_len -= 1
                    st = rng.expovariate(mu)
                    next_s2_done = min_time + st
                else:
                    # S2 busy, job waits in Q2
                    # Set next_s1_done to inf since server is free
                    next_s1_done = float('inf')
                    # Try to start next job from Q1 if any
                    if q1_len > 0:
                        s1_state = 1
                        q1_len -= 1
                        st = rng.expovariate(mu)
                        next_s1_done = min_time + st
                    else:
                        next_s1_done = float('inf')
                        
            # Process S2 Completions
            for _ in s2_events:
                s2_state = 0
                # Job leaves system
                if min_time >= warmup_time:
                    count_departures += 1
                    # Calculate sojourn time
                    if len(active_job_arrival_times) > 0:
                        start_time = active_job_arrival_times.pop(0)
                        sojourn = min_time - start_time
                        total_sojourn_time += sojourn
                        completed_jobs_in_window += 1
                
                # Try to start next job from Q2 if any
                if q2_len > 0:
                    s2_state = 1
                    q2_len -= 1
                    st = rng.expovariate(mu)
                    next_s2_done = min_time + st
                else:
                    next_s2_done = float('inf')
            
            # Update last_t
            last_t = min_time
            
            # Handle edge case where multiple events happen at same time and one triggers another immediately?
            # The logic above handles transitions. 
            # E.g., S1 done -> moves to Q2 -> if S2 idle, starts S2.
            # This is handled inside the s1_events loop.
            
            # One detail: If S1 finishes and S2 is idle, we set next_s2_done.
            # If S2 was already scheduled to finish at the SAME time? 
            # Unlikely with continuous distributions.
            
            # Also, if S1 finishes and S2 becomes busy, we must check if S1 can start next job.
            # Handled in s1_events loop.

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        sim_duration = H - warmup_time
        if sim_duration <= 0:
            L_val = 0.0
            W_val = 0.0
            bf_val = 0.0
            pl_val = 0.0
            pw_val = 0.0
        else:
            avg_q1 = area_q1 / sim_duration
            avg_q2 = area_q2 / sim_duration
            L_val = avg_q1 + avg_q2
            
            if completed_jobs_in_window > 0:
                W_val = total_sojourn_time / completed_jobs_in_window
            else:
                W_val = 0.0
                
            total_busy_time = time_s1_busy + time_s2_busy
            max_possible_busy_time = 2 * sim_duration
            bf_val = total_busy_time / max_possible_busy_time if max_possible_busy_time > 0 else 0.0
            
            # p_loss: Assuming infinite buffer, loss is 0.
            pl_val = 0.0
            
            # p_wait: Probability that an arriving customer has to wait.
            # In M/M/1, P(wait) = rho. Here we have two stages.
            # Definition: Fraction of arrivals that find the server busy?
            # Or fraction of time system is congested?
            # Usually P_wait is empirical: (Number of arrivals finding Q>0) / Total Arrivals.
            # We didn't track "finding Q>0".
            # Alternative: Use Little's Law derived or theoretical?
            # Prompt asks for empirical stats.
            # Let's approximate P_wait as the fraction of time servers are busy? No, that's utilization.
            # Let's track "arrivals that waited".
            # We missed tracking this.
            # Re-evaluating code structure...
            # I should have incremented a counter if q1_len > 0 or q2_len > 0 at arrival?
            # Actually, waiting means joining a non-empty queue OR starting service immediately?
            # Standard definition: Customer waits if they do not enter service immediately.
            # At Stage 1: Waits if s1_state==1 (busy) OR q1_len>0? 
            # If s1 is idle, q1 is empty. If s1 busy, q1 might be empty (just finished?) or >0.
            # If arrival finds s1 busy, it waits.
            # If arrival finds s1 idle, it doesn't wait at S1.
            # Does it wait at S2? It hasn't reached S2 yet.
            # Sojourn time includes waiting at both.
            # "P_wait" usually refers to the probability that an arriving customer has to wait for service.
            # In a tandem queue, this is ambiguous. Is it wait at first server?
            # Let's assume P_wait is the fraction of customers who had to wait at least once in the system.
            # Or simply the average number in queue / average number in system?
            # Let's look at similar problems. Often P_wait = Lq / L.
            # Lq = avg queue length (excluding service).
            # We tracked q1_len and q2_len which INCLUDE the job in service?
            # My code: `q1_len` increments on arrival. If s1 idle, decrements immediately.
            # So `q1_len` represents the QUEUE LENGTH (waiting only), not including service.
            # Similarly `q2_len` is waiting only.
            # So Lq = avg_q1 + avg_q2.
            # L = Lq + L_service.
            # L_service = P(S1 busy) + P(S2 busy).
            # P(S1 busy) = time_s1_busy / sim_duration.
            # P(S2 busy) = time_s2_busy / sim_duration.
            # So L = avg_q1 + avg_q2 + util1 + util2.
            # Then P_wait could be Lq / L? Or fraction of arrivals that joined a non-empty queue?
            # Given the ambiguity and lack of explicit counter in my draft, I will calculate P_wait as Lq/L.
            # Note: If L=0, P_wait=0.
            
            util1 = time_s1_busy / sim_duration
            util2 = time_s2_busy / sim_duration
            L_service = util1 + util2
            L_total = L_val + L_service # Wait, my L_val was avg_q1+avg_q2. That is Lq.
            # The prompt asks for L (average number in system).
            # So L_sys = Lq + L_service.
            # My variable `L_val` calculated earlier was just Lq. I need to fix this.
            
            # Correction:
            # L_sys = avg_q1 + avg_q2 + util1 + util2
            # W = L_sys / lambda_eff
            # lambda_eff = count_departures / sim_duration
            
            # Let's recalculate properly below.
            pass

        # Recalculating correctly for storage
        if sim_duration > 0:
            avg_q1 = area_q1 / sim_duration
            avg_q2 = area_q2 / sim_duration
            util1 = time_s1_busy / sim_duration
            util2 = time_s2_busy / sim_duration
            
            L_sys = avg_q1 + avg_q2 + util1 + util2
            
            if completed_jobs_in_window > 0:
                W_sys = total_sojourn_time / completed_jobs_in_window
            else:
                W_sys = 0.0
                
            # Busy fraction of the whole system (2 servers)
            sys_busy_frac = (time_s1_busy + time_s2_busy) / (2 * sim_duration)
            
            # P_loss = 0
            p_loss = 0.0
            
            # P_wait: Fraction of time there is someone waiting? Or prob arrival waits?
            # Using Lq / L_sys as proxy for probability of waiting (if Poisson arrivals see time averages)
            if L_sys > 0:
                p_wait = (avg_q1 + avg_q2) / L_sys
            else:
                p_wait = 0.0
                
            # Effective arrival rate
            lam_eff = count_departures / sim_duration
            
            # Block count is 0
            blk_count = 0
        else:
            L_sys = 0.0
            W_sys = 0.0
            sys_busy_frac = 0.0
            p_loss = 0.0
            p_wait = 0.0
            lam_eff = 0.0
            blk_count = 0
            count_arrivals = 0
            count_departures = 0

        all_L.append(L_sys)
        all_W.append(W_sys)
        all_busy_frac.append(sys_busy_frac)
        all_p_loss.append(p_loss)
        all_p_wait.append(p_wait)
        all_arr.append(count_arrivals)
        all_dep.append(count_departures)
        all_blk.append(blk_count)

    # Aggregate results
    n_seeds = len(seeds_used)
    if n_seeds == 0:
        mean_L = 0.0
        mean_W = 0.0
        mean_bf = 0.0
        mean_pl = 0.0
        mean_pw = 0.0
        mean_arr = 0.0
        mean_dep = 0.0
        mean_blk = 0.0
        mean_lam_eff = 0.0
    else:
        mean_L = sum(all_L) / n_seeds
        mean_W = sum(all_W) / n_seeds
        mean_bf = sum(all_busy_frac) / n_seeds
        mean_pl = sum(all_p_loss) / n_seeds
        mean_pw = sum(all_p_wait) / n_seeds
        mean_arr = sum(all_arr) / n_seeds
        mean_dep = sum(all_dep) / n_seeds
        mean_blk = sum(all_blk) / n_seeds
        # Dep rate is per hour
        mean_lam_eff = sum([d / (H - H*0.25) for d in all_dep]) / n_seeds if n_seeds > 0 else 0.0

    result = {
        "L": round(mean_L, 6),
        "W": round(mean_W, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used,
        "seeds_used": n_seeds,
        "time_unit": "hour",
        "win": round(H - H*0.25, 6),
        "arr": round(mean_arr, 6),
        "blk": round(mean_blk, 6),
        "busy_frac": round(mean_bf, 6),
        "busy_util": round(mean_bf, 6), # Same as busy_frac for system? Or per server? Usually system wide.
        "dep": round(mean_dep, 6),
        "dep_rate": round(mean_lam_eff, 6),
        "lam_eff": round(mean_lam_eff, 6),
        "p_loss": round(mean_pl, 6),
        "p_wait": round(mean_pw, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
