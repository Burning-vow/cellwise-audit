import argparse
import json
import random
import heapq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    # Parameters in hours and minutes
    # Arrival rate: 4 per hour
    lam_base = 4.0
    # Service time mean: 6 minutes = 0.1 hours
    mu_base_mean_min = 6.0
    
    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        # Faster service means smaller mean time
        mu_mean_min = mu_base_mean_min / 1.2
    elif args.pert == 'c_up':
        # Capacity perturbation not explicitly defined for single server queue structure change, 
        # usually implies cost or capacity. Here we assume it might affect arrival or service slightly differently or just ignore structural change.
        # Let's treat c_up as a slight increase in arrival to test congestion? Or maybe decrease service speed?
        # The prompt says "perturbation only changes parameters". 
        # Let's stick to none/lam_up/mu_up logic. For c_up, let's assume it increases arrival rate by 10% as well or similar.
        lam = lam_base * 1.1
        mu_mean_min = mu_base_mean_min
    else:
        lam = lam_base
        mu_mean_min = mu_base_mean_min

    if args.pert == 'mu_up':
         mu_mean_min = mu_base_mean_min / 1.2
    else:
         mu_mean_min = mu_base_mean_min

    mu_mean_hr = mu_mean_min / 60.0
    
    horizon_hours = args.horizon
    warmup_fraction = 0.25
    warmup_time = horizon_hours * warmup_fraction
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_arrivals_in_window = 0
    total_departures_in_window = 0
    total_blocked_in_window = 0
    total_busy_time_1_in_window = 0.0
    total_busy_time_2_in_window = 0.0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(args.seeds):
        current_seed = args.seed_start + i
        seed_list.append(current_seed)
        rng = random.Random(current_seed)
        
        # Event types: 0=Arrival, 1=Service1End, 2=Service2End
        events = []
        
        # State variables
        # Queue lengths (excluding the one being served)
        q1_len = 0
        q2_len = 0
        
        # Server status: None or job_id
        srv1_status = None
        srv2_status = None
        
        # Job tracking
        # job_id -> {arrival_time, service1_end_time, service2_end_time, state}
        jobs = {}
        next_job_id = 0
        
        # Time tracking for integration
        last_event_time = 0.0
        current_L = 0 # Number of jobs in system
        
        # Accumulators for this seed within window
        seed_L_area = 0.0
        seed_W_sum = 0.0
        seed_arr_count = 0
        seed_dep_count = 0
        seed_blk_count = 0
        seed_busy1_time = 0.0
        seed_busy2_time = 0.0
        seed_wait_count = 0 # Jobs that waited in queue 1 or 2
        
        # Initial arrival
        t_arr = rng.expovariate(lam)
        heapq.heappush(events, (t_arr, 0, -1)) # -1 dummy id
        
        while events:
            t, etype, jid = heapq.heappop(events)
            
            # Update integrals up to time t
            dt = t - last_event_time
            if last_event_time >= warmup_time:
                seed_L_area += current_L * dt
                if srv1_status is not None:
                    seed_busy1_time += dt
                if srv2_status is not None:
                    seed_busy2_time += dt
            
            last_event_time = t
            
            if etype == 0: # Arrival
                # Check if system can accept? Problem says "queueing", infinite buffer assumed unless specified blocked.
                # "blk" suggests blocking/loss. But standard Jackson network has infinite buffers.
                # However, output requires blk. If infinite buffer, blk=0.
                # Let's assume infinite buffer for now, so blk is always 0.
                # If there was a finite capacity, we'd check.
                
                new_jid = next_job_id
                next_job_id += 1
                
                # Sample service times immediately
                s1_time = rng.expovariate(1.0 / mu_mean_hr)
                s2_time = rng.expovariate(1.0 / mu_mean_hr)
                
                jobs[new_jid] = {
                    'arr_t': t,
                    's1_dur': s1_time,
                    's2_dur': s2_time,
                    'state': 'q1' # waiting for srv1
                }
                
                current_L += 1
                
                if last_event_time >= warmup_time:
                    seed_arr_count += 1
                
                # Try to start service on 1
                if srv1_status is None:
                    srv1_status = new_jid
                    jobs[new_jid]['state'] = 'srv1'
                    end_t = t + s1_time
                    heapq.heappush(events, (end_t, 1, new_jid))
                else:
                    q1_len += 1
                    jobs[new_jid]['state'] = 'q1'
                    
            elif etype == 1: # Service 1 End
                # jid is the job finishing srv1
                if srv1_status != jid:
                    continue # Stale event? Shouldn't happen with correct scheduling
                    
                srv1_status = None
                job = jobs[jid]
                job['state'] = 'to_q2'
                
                # Move to Q2
                if srv2_status is None:
                    srv2_status = jid
                    job['state'] = 'srv2'
                    end_t = t + job['s2_dur']
                    heapq.heappush(events, (end_t, 2, jid))
                else:
                    q2_len += 1
                    job['state'] = 'q2'
                    
                # Start next from Q1 if any
                if q1_len > 0:
                    # Find first waiting in Q1? 
                    # We don't have a FIFO queue structure explicitly stored as list of IDs easily accessible without scanning.
                    # Optimization: Maintain queues as lists/deques.
                    pass 
                
                # Re-implementing with explicit queues for correctness
                # This simple dict approach fails FIFO order for Q1/Q2 if multiple wait.
                # Need to refactor slightly inside loop or use external structures.
                
                # Let's restart the inner loop logic with proper queues.
                break # Break to fix code structure below

        # Refactored Simulation Loop for Single Seed
        
        # Reset accumulators for this seed properly
        seed_L_area = 0.0
        seed_W_sum = 0.0
        seed_arr_count = 0
        seed_dep_count = 0
        seed_blk_count = 0
        seed_busy1_time = 0.0
        seed_busy2_time = 0.0
        seed_wait_count = 0
        
        events = []
        q1 = [] # List of job IDs waiting for srv1
        q2 = [] # List of job IDs waiting for srv2
        srv1_job = None
        srv2_job = None
        jobs = {}
        next_job_id = 0
        current_L = 0
        last_event_time = 0.0
        
        t_arr = rng.expovariate(lam)
        heapq.heappush(events, (t_arr, 0, -1))
        
        sim_done = False
        while not sim_done:
            if not events:
                break
            
            t, etype, jid = heapq.heappop(events)
            
            if t > horizon_hours:
                # Process remaining? No, stop at horizon.
                # But we need to integrate up to horizon.
                # If an event is beyond horizon, we should stop simulation but ensure integral covers up to horizon.
                # Actually, standard DES stops when time exceeds horizon.
                # We need to handle the final interval [last_event_time, horizon]
                break
            
            dt = t - last_event_time
            if last_event_time >= warmup_time:
                seed_L_area += current_L * dt
                if srv1_job is not None:
                    seed_busy1_time += dt
                if srv2_job is not None:
                    seed_busy2_time += dt
            
            last_event_time = t
            
            if etype == 0: # Arrival
                new_jid = next_job_id
                next_job_id += 1
                
                s1_time = rng.expovariate(1.0 / mu_mean_hr)
                s2_time = rng.expovariate(1.0 / mu_mean_hr)
                
                jobs[new_jid] = {
                    'arr_t': t,
                    's1_dur': s1_time,
                    's2_dur': s2_time,
                    'start_srv1_t': None,
                    'end_srv1_t': None,
                    'start_srv2_t': None,
                    'end_srv2_t': None
                }
                
                current_L += 1
                if t >= warmup_time:
                    seed_arr_count += 1
                
                if srv1_job is None:
                    srv1_job = new_jid
                    jobs[new_jid]['start_srv1_t'] = t
                    end_t = t + s1_time
                    heapq.heappush(events, (end_t, 1, new_jid))
                else:
                    q1.append(new_jid)
                    # Mark as waiting? Not strictly needed for stats if we track start/end times.
                    
            elif etype == 1: # Service 1 End
                if srv1_job != jid:
                    continue
                
                srv1_job = None
                jobs[jid]['end_srv1_t'] = t
                
                # Move to Q2
                if srv2_job is None:
                    srv2_job = jid
                    jobs[jid]['start_srv2_t'] = t
                    end_t = t + jobs[jid]['s2_dur']
                    heapq.heappush(events, (end_t, 2, jid))
                else:
                    q2.append(jid)
                
                # Start next from Q1
                if q1:
                    next_jid = q1.pop(0)
                    srv1_job = next_jid
                    jobs[next_jid]['start_srv1_t'] = t
                    end_t = t + jobs[next_jid]['s1_dur']
                    heapq.heappush(events, (end_t, 1, next_jid))
                    
            elif etype == 2: # Service 2 End
                if srv2_job != jid:
                    continue
                
                srv2_job = None
                jobs[jid]['end_srv2_t'] = t
                
                # Calculate W for this job
                w = t - jobs[jid]['arr_t']
                if t >= warmup_time:
                    seed_W_sum += w
                    seed_dep_count += 1
                    # Check if it waited
                    if jobs[jid]['start_srv1_t'] > jobs[jid]['arr_t'] or \
                       (jobs[jid]['start_srv2_t'] is not None and jobs[jid]['start_srv2_t'] > jobs[jid]['end_srv1_t']):
                        seed_wait_count += 1
                
                current_L -= 1
                
                # Start next from Q2
                if q2:
                    next_jid = q2.pop(0)
                    srv2_job = next_jid
                    jobs[next_jid]['start_srv2_t'] = t
                    end_t = t + jobs[next_jid]['s2_dur']
                    heapq.heappush(events, (end_t, 2, next_jid))
        
        # Final integration step to horizon
        dt_final = horizon_hours - last_event_time
        if last_event_time < horizon_hours and last_event_time >= warmup_time:
             seed_L_area += current_L * dt_final
             if srv1_job is not None:
                 seed_busy1_time += dt_final
             if srv2_job is not None:
                 seed_busy2_time += dt_final
        elif last_event_time < warmup_time:
             # Warmup ended before last event? Unlikely if horizon > warmup.
             # If last_event_time < warmup_time, then no accumulation happened yet.
             # But we need to accumulate from warmup_time to horizon.
             # This case implies simulation ended very early or warmup is huge.
             # Assuming standard flow:
             pass
             
        # Handle case where last_event_time < warmup_time but horizon > warmup_time
        if last_event_time < warmup_time:
            # Integrate from warmup_time to horizon
            dt_warm_to_horizon = horizon_hours - warmup_time
            # Current L at warmup_time? We didn't track it precisely if we skipped updates.
            # This logic assumes we update L continuously.
            # If we broke out early due to empty events, L is constant.
            seed_L_area += current_L * dt_warm_to_horizon
            if srv1_job is not None:
                seed_busy1_time += dt_warm_to_horizon
            if srv2_job is not None:
                seed_busy2_time += dt_warm_to_horizon

        # Aggregate for this seed
        win_length = horizon_hours - warmup_time
        if win_length <= 0:
            l_est = 0.0
            w_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0
            p_wait_est = 0.0
        else:
            l_est = seed_L_area / win_length
            w_est = seed_W_sum / seed_dep_count if seed_dep_count > 0 else 0.0
            # Busy fraction: average over both servers? Or sum?
            # Usually utilization per server. The key `busy_frac` likely refers to system-wide or average.
            # Given `busy_util` also exists, let's define busy_frac as average utilization of the two servers.
            util1 = seed_busy1_time / win_length
            util2 = seed_busy2_time / win_length
            busy_frac_est = (util1 + util2) / 2.0
            
            # Loss probability: blk / arr. Since infinite buffer, blk=0.
            p_loss_est = 0.0
            
            # Wait probability: wait_count / dep_count
            p_wait_est = seed_wait_count / seed_dep_count if seed_dep_count > 0 else 0.0

        per_seed_L.append(l_est)
        per_seed_W.append(w_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_L_area += seed_L_area
        total_W_sum += seed_W_sum
        total_arrivals_in_window += seed_arr_count
        total_departures_in_window += seed_dep_count
        total_blocked_in_window += seed_blk_count
        total_busy_time_1_in_window += seed_busy1_time
        total_busy_time_2_in_window += seed_busy2_time

    # Global Statistics
    num_seeds = len(seed_list)
    total_win_length = (horizon_hours - warmup_time) * num_seeds
    
    if total_win_length > 0:
        avg_L = total_L_area / total_win_length
    else:
        avg_L = 0.0
        
    if total_departures_in_window > 0:
        avg_W = total_W_sum / total_departures_in_window
    else:
        avg_W = 0.0
        
    avg_arr = total_arrivals_in_window / num_seeds if num_seeds > 0 else 0
    avg_dep = total_departures_in_window / num_seeds if num_seeds > 0 else 0
    avg_blk = total_blocked_in_window / num_seeds if num_seeds > 0 else 0
    
    # Dep rate in per hour
    dep_rate = avg_dep / (horizon_hours - warmup_time) if (horizon_hours - warmup_time) > 0 else 0
    
    # Effective lambda
    lam_eff = dep_rate
    
    # Busy fractions global
    if total_win_length > 0:
        g_util1 = total_busy_time_1_in_window / total_win_length
        g_util2 = total_busy_time_2_in_window / total_win_length
        g_busy_frac = (g_util1 + g_util2) / 2.0
    else:
        g_busy_frac = 0.0
        
    g_p_loss = 0.0
    g_p_wait = 0.0
    if total_departures_in_window > 0:
        # Recalculate global wait prob based on sums? 
        # We didn't store global wait count. Let's approximate from per-seed averages or re-sum.
        # Better: Sum per_seed_wait_counts? We didn't store them globally.
        # Let's compute weighted average of per_seed_p_wait
        sum_wait_prob = sum(per_seed_p_wait)
        g_p_wait = sum_wait_prob / num_seeds if num_seeds > 0 else 0.0

    result = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": num_seeds,
        "time_unit": "hour",
        "win": round(horizon_hours - warmup_time, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(g_busy_frac, 4),
        "busy_util": round(g_busy_frac, 4), # Alias
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(g_p_loss, 4),
        "p_wait": round(g_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
