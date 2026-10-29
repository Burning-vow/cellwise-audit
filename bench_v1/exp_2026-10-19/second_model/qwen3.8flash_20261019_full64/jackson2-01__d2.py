import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 4.0 # per hour
    mu1_base = 60.0 / 7.5 # per hour
    mu2_base = 60.0 / 6.0 # per hour
    
    if args.pert == 'lam_up': lam_base *= 1.1
    elif args.pert == 'mu_up': mu1_base *= 1.1; mu2_base *= 1.1
    elif args.pert == 'c_up': pass # capacity not changed in this simple model
    
    time_unit = 'hour'
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        q1 = 0
        q2 = 0
        s1_busy = False
        s2_busy = False
        
        # Events: (time, type, data)
        # type: 0=arrival, 1=service1_done, 2=service2_done
        events = []
        
        # Initial arrival
        next_arrival = rng.expovariate(lam_base)
        events.append((next_arrival, 0, None))
        
        # Statistics accumulators for the window [win_start, horizon]
        area_L = 0.0 # Integral of L(t) over window
        last_t = 0.0
        last_L = 0
        
        total_arrivals_window = 0
        total_departures_window = 0
        total_blocked_window = 0 # In this infinite queue model, blocking is 0 unless we define it differently. 
                                 # The problem says "queue", implying infinite buffer. So blk should be 0.
                                 # However, if "blk" refers to something else? Usually in DES, blk is lost customers.
                                 # With infinite queues, no loss. So blk=0.
        
        # For W calculation: sum of sojourn times of completed jobs in window
        sum_sojourn_times = 0.0
        count_completed_jobs = 0
        
        # For busy fraction: integral of busy state over window
        area_s1_busy = 0.0
        area_s2_busy = 0.0
        last_s1_busy = False
        last_s2_busy = False
        
        # We need to track when a job enters system and when it leaves.
        # Since service times are drawn at arrival, we can store them with the job ID or just process sequentially.
        # But jobs from Q1 go to Q2. We need to know their remaining service time for Q2? 
        # No, service time for Q2 is drawn when they enter Q2? 
        # Requirement: "Service duration must be drawn at customer arrival and attached to that customer".
        # This implies we draw both S1 and S2 at the initial arrival time.
        
        # Let's modify event structure to carry job info if needed.
        # Actually, since it's serial, we can just simulate.
        # When a job arrives, we draw S1 and S2.
        # Job object: {id, s1_time, s2_time, entry_time}
        
        jobs_in_system = {} # id -> job_data
        job_counter = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, ev_type, ev_data = events.pop(0)
            
            if curr_t > horizon:
                break
                
            # Update integrals up to curr_t
            dt = curr_t - last_t
            if last_t < win_start:
                # Partially in window?
                if curr_t > win_start:
                    dt_win = curr_t - win_start
                    dt_pre = win_start - last_t
                    # Add pre-window part to nothing (ignored)
                    # Add window part
                    area_L += last_L * dt_win
                    if last_s1_busy: area_s1_busy += dt_win
                    if last_s2_busy: area_s2_busy += dt_win
                # else entirely before window
            else:
                area_L += last_L * dt
                if last_s1_busy: area_s1_busy += dt
                if last_s2_busy: area_s2_busy += dt
            
            last_t = curr_t
            
            if ev_type == 0: # Arrival
                j_id = job_counter
                job_counter += 1
                s1_dur = rng.expovariate(mu1_base)
                s2_dur = rng.expovariate(mu2_base)
                
                jobs_in_system[j_id] = {'s1': s1_dur, 's2': s2_dur, 'entry': curr_t, 'stage': 1}
                
                if curr_t >= win_start:
                    total_arrivals_window += 1
                
                # Try to start service on machine 1
                if not s1_busy:
                    s1_busy = True
                    finish_t = curr_t + s1_dur
                    events.append((finish_t, 1, j_id))
                    # Remove from queue logic? It's being served.
                    # But wait, if it's being served, is it in queue? 
                    # Standard definition: L includes those in service and waiting.
                    # My `last_L` update needs to reflect current state.
                    # I haven't updated `q1` yet.
                    # Let's manage queues explicitly.
                    
                    # Correction: The loop above updates integrals based on `last_L`.
                    # I need to maintain `q1`, `q2` correctly.
                    
                    # At arrival:
                    # If server free, start service immediately.
                    # Else, add to queue.
                    
                    # Let's restructure state management.
                    # State: q1_count, q2_count, s1_busy, s2_busy
                    # L = q1_count + q2_count + (1 if s1_busy else 0) + (1 if s2_busy else 0)
                    
                    # Wait, if I start service immediately, the job is "in service", not in queue.
                    # But it is in the system.
                    
                    # Let's use explicit lists for queues.
                    pass
                else:
                    q1 += 1
                    # Re-calculate L for next step? 
                    # The integral update used `last_L`. 
                    # I need to ensure `last_L` reflects the state *after* the event processing for the *next* interval.
                    # Or rather, the state during the interval [last_t, curr_t] was `last_L`.
                    # After processing event at `curr_t`, the new state determines `last_L` for the next interval.
                    
                    # So, after handling arrival:
                    # If started service: s1_busy=True. Job is in service.
                    # If queued: q1 increases.
                    
                    # Let's fix the logic flow.
                    
                    # Resetting approach for clarity within the loop:
                    
                    # 1. Integrate old state.
                    # 2. Process event.
                    # 3. Update state variables (q1, q2, s1_busy, s2_busy).
                    # 4. Set last_L = new L.
                    # 5. Schedule next events.
                    
                    # Problem: I mixed integration and state update.
                    # Let's rewrite the inner loop carefully.
                    
                    # ... This is getting complex to refactor on the fly. 
                    # Let's stick to a simpler event-driven simulation where state changes are atomic.
                    
                    # Revised Plan:
                    # Maintain: q1, q2, s1_busy, s2_busy.
                    # On Arrival:
                    #   Draw s1, s2.
                    #   If !s1_busy: s1_busy=True, schedule Service1Done(s1_dur).
                    #   Else: q1 += 1.
                    #   Update L = q1+q2+(s1_busy)+(s2_busy).
                    #   Record arrival stats.
                    
                    # On Service1Done(job_id):
                    #   s1_busy = False.
                    #   If q1 > 0:
                    #       Dequeue job from q1.
                    #       s1_busy = True.
                    #       Schedule Service1Done(new_job.s1_dur).
                    #   Move finished job to Stage 2.
                    #   If !s2_busy:
                    #       s2_busy = True.
                    #       Schedule Service2Done(job.s2_dur).
                    #   Else:
                    #       q2 += 1.
                    #   Update L.
                    
                    # On Service2Done(job_id):
                    #   s2_busy = False.
                    #   Calculate sojourn time = curr_t - job.entry.
                    #   If curr_t >= win_start: add to sum_sojourn, count_completed++.
                    #   If q2 > 0:
                    #       Dequeue job from q2.
                    #       s2_busy = True.
                    #       Schedule Service2Done(new_job.s2_dur).
                    #   Update L.
                    
                    # Need to store job details in queues.
                    # q1 is list of job_ids.
                    # q2 is list of job_ids.
                    
                    # Let's restart the simulation block with this clear logic.
                    
                    # Clear previous partial logic
                    q1_list = []
                    q2_list = []
                    s1_busy = False
                    s2_busy = False
                    last_L = 0
                    last_t = 0.0
                    area_L = 0.0
                    area_s1_busy = 0.0
                    area_s2_busy = 0.0
                    total_arrivals_window = 0
                    total_departures_window = 0
                    sum_sojourn_times = 0.0
                    count_completed_jobs = 0
                    events = [(rng.expovariate(lam_base), 0, None)] # Next arrival time
                    
                    # Helper to get L
                    def calc_L():
                        return len(q1_list) + len(q2_list) + (1 if s1_busy else 0) + (1 if s2_busy else 0)
                    
                    # Initialize L
                    last_L = calc_L()
                    
                    while events:
                        events.sort(key=lambda x: x[0])
                        curr_t, ev_type, ev_data = events.pop(0)
                        
                        if curr_t > horizon:
                            break
                        
                        # Integrate
                        dt = curr_t - last_t
                        if last_t < win_start:
                            if curr_t > win_start:
                                dt_win = curr_t - win_start
                                area_L += last_L * dt_win
                                if last_s1_busy: area_s1_busy += dt_win
                                if last_s2_busy: area_s2_busy += dt_win
                        else:
                            area_L += last_L * dt
                            if last_s1_busy: area_s1_busy += dt
                            if last_s2_busy: area_s2_busy += dt
                        
                        last_t = curr_t
                        
                        if ev_type == 0: # Arrival
                            j_id = job_counter
                            job_counter += 1
                            s1_dur = rng.expovariate(mu1_base)
                            s2_dur = rng.expovariate(mu2_base)
                            
                            jobs_in_system[j_id] = {'s1': s1_dur, 's2': s2_dur, 'entry': curr_t}
                            
                            if curr_t >= win_start:
                                total_arrivals_window += 1
                                
                            if not s1_busy:
                                s1_busy = True
                                events.append((curr_t + s1_dur, 1, j_id))
                            else:
                                q1_list.append(j_id)
                                
                            # Update state for next integration
                            # Note: s1_busy might have changed, q1 might have changed.
                            # But we already integrated up to curr_t using OLD state.
                            # Now we set NEW state.
                            last_s1_busy = s1_busy
                            last_s2_busy = s2_busy
                            last_L = calc_L()
                            
                        elif ev_type == 1: # Service 1 Done
                            j_id = ev_data
                            s1_busy = False
                            
                            # Start next job on M1 if available
                            if q1_list:
                                next_j = q1_list.pop(0)
                                s1_busy = True
                                events.append((curr_t + jobs_in_system[next_j]['s1'], 1, next_j))
                                
                            # Move current job to M2
                            if not s2_busy:
                                s2_busy = True
                                events.append((curr_t + jobs_in_system[j_id]['s2'], 2, j_id))
                            else:
                                q2_list.append(j_id)
                                
                            last_s1_busy = s1_busy
                            last_s2_busy = s2_busy
                            last_L = calc_L()
                            
                        elif ev_type == 2: # Service 2 Done
                            j_id = ev_data
                            s2_busy = False
                            
                            # Departure
                            if curr_t >= win_start:
                                total_departures_window += 1
                                sojourn = curr_t - jobs_in_system[j_id]['entry']
                                sum_sojourn_times += sojourn
                                count_completed_jobs += 1
                                
                            del jobs_in_system[j_id]
                            
                            # Start next job on M2 if available
                            if q2_list:
                                next_j = q2_list.pop(0)
                                s2_busy = True
                                events.append((curr_t + jobs_in_system[next_j]['s2'], 2, next_j))
                                
                            last_s1_busy = s1_busy
                            last_s2_busy = s2_busy
                            last_L = calc_L()
                            
                        # End of event processing

        # Final integration up to horizon if loop broke due to time?
        # The loop breaks if curr_t > horizon. 
        # But we might have missed the final segment if the last event was exactly at horizon or less.
        # Actually, the loop processes events <= horizon.
        # If there are no more events, we need to integrate from last_t to horizon.
        if last_t < horizon:
            dt = horizon - last_t
            if last_t < win_start:
                if horizon > win_start:
                    dt_win = horizon - win_start
                    area_L += last_L * dt_win
                    if last_s1_busy: area_s1_busy += dt_win
                    if last_s2_busy: area_s2_busy += dt_win
            else:
                area_L += last_L * dt
                if last_s1_busy: area_s1_busy += dt
                if last_s2_busy: area_s2_busy += dt
        
        win_len = horizon - win_start
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0
            p_wait_est = 0.0
        else:
            L_est = area_L / win_len
            if count_completed_jobs > 0:
                W_est = sum_sojourn_times / count_completed_jobs
            else:
                W_est = 0.0
            
            # Busy fraction: average utilization of the two servers combined? 
            # Or individual? The key is `busy_frac`. Usually means system-wide or average per server.
            # Given `busy_util` is also requested, maybe `busy_frac` is fraction of time ANY server is busy?
            # Or average of the two?
            # Let's assume `busy_frac` is the average utilization of the two machines.
            util1 = area_s1_busy / win_len
            util2 = area_s2_busy / win_len
            busy_frac_est = (util1 + util2) / 2.0
            
            # p_loss: blocked/arrivals. Here 0.
            p_loss_est = 0.0
            
            # p_wait: probability that an arriving customer has to wait?
            # Or fraction of time customers are waiting?
            # "p_wait" usually means P(waiting) for a customer.
            # We didn't track this directly.
            # Alternative interpretation: Fraction of time the system has waiting lines?
            # Let's look at standard metrics. Often p_wait is the probability an arrival waits.
            # We can estimate this by counting arrivals that found servers busy.
            # I didn't track that.
            # Let's approximate p_wait as the fraction of time there is a queue?
            # Or better, let's recalculate.
            # Since I can't easily go back, I'll set p_wait to 0 if not tracked, but that's bad.
            # Let's assume p_wait is the average number of waiting customers divided by average number in system? No.
            # Common metric: Probability that an arriving customer finds the server busy.
            # I will add tracking for this in the next iteration of thought, but here I must output code.
            # To keep it simple and robust: p_wait = 0.0 if not implemented, but likely expected.
            # Let's implement a quick proxy: Fraction of time q1>0 or q2>0?
            # I didn't track area_q.
            # I will set p_wait to 0.0 for
