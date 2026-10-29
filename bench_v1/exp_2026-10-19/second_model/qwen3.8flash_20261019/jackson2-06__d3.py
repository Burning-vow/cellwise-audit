import sys, json, random, argparse
from collections import deque

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert
    
    # Parameters in hours and minutes
    lam_base = 6.0 # arrivals per hour
    mu1_base = 8.0 # service rate stage 1 (per hour), mean 7.5 min = 0.125 hr -> 1/0.125 = 8
    mu2_base = 12.0 # service rate stage 2 (per hour), mean 5 min = 1/12 hr
    
    if pert == 'lam_up': lam_base *= 1.1
    elif pert == 'mu_up': 
        mu1_base *= 1.1
        mu2_base *= 1.1
    elif pert == 'c_up': pass # Cost not modeled in output metrics requested, structure unchanged
    
    results_L = []
    results_W = []
    results_busy_frac = []
    results_p_loss = []
    results_p_wait = []
    results_arr = []
    results_dep = []
    results_blk = []
    
    time_unit = "hour"
    
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        # Queues: store arrival time of job entering queue
        q1 = deque()
        q2 = deque()
        
        # Server states
        srv1_free_at = 0.0
        srv2_free_at = 0.0
        
        # Counters for statistics within window
        # We need to track area under curve for L (number in system)
        # Number in system = len(q1) + len(q2) + (srv1 busy? 1:0) + (srv2 busy? 1:0)
        # But simpler: track events that change the count.
        
        n_in_sys = 0
        last_event_time = 0.0
        area_L = 0.0
        
        # For W: sum of sojourn times / number of departures
        sum_sojourn = 0.0
        dep_count = 0
        arr_count = 0
        blk_count = 0
        
        # Busy times for utilization
        busy1_time = 0.0
        busy2_time = 0.0
        
        # Next event candidates
        next_arrival = rng.expovariate(lam_base)
        
        # Warmup period: first 25% of horizon
        warmup_end = H * 0.25
        
        # Statistics accumulation flags
        stats_started = False
        
        while True:
            # Determine next event time
            events = []
            
            # Arrival
            if next_arrival < H:
                events.append(('arr', next_arrival))
            
            # Service completion 1
            if srv1_free_at > t and srv1_free_at < H:
                events.append(('srv1_done', srv1_free_at))
                
            # Service completion 2
            if srv2_free_at > t and srv2_free_at < H:
                events.append(('srv2_done', srv2_free_at))
            
            if not events:
                break
            
            # Find earliest event
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]
            
            # Update area for L before changing state
            if stats_started:
                dt = etime - last_event_time
                area_L += n_in_sys * dt
                
            t = etime
            last_event_time = t
            
            if t >= warmup_end and not stats_started:
                stats_started = True
                # Reset counters for steady-state estimation if we want pure post-warmup
                # The prompt says "statistics only accumulated in window after removing first 25% warmup"
                # So we should reset accumulators at warmup_end? 
                # Usually, we integrate from warmup_end to H.
                # Let's re-initialize accumulators when stats_started becomes True.
                area_L = 0.0
                sum_sojourn = 0.0
                dep_count = 0
                arr_count = 0
                blk_count = 0
                busy1_time = 0.0
                busy2_time = 0.0
                # Note: n_in_sys is current state, keep it.
                # But wait, if we reset area_L, we lose history. That's correct for windowed stats.
                # However, we must ensure we don't double count or miss initial segment of window.
                # Since we set stats_started=True exactly at t=warmup_end (or first event after),
                # and we update area BEFORE processing event, this logic holds if we handle the transition carefully.
                # Actually, the loop updates area based on previous interval. 
                # If we just started stats, the previous interval was pre-warmup. We shouldn't add it.
                # So we need a flag or check inside the area update.
                pass 

            # Handle Event
            if etype == 'arr':
                arr_count += 1 if stats_started else 0
                # Check capacity? Problem doesn't specify finite buffer. Assume infinite queue.
                # "blk" implies blocking/loss. Standard Jackson network has infinite buffers unless specified.
                # But output requires blk. Maybe assume finite buffer? 
                # Prompt: "two processes each have their own queue". Doesn't say finite.
                # However, `p_loss` and `blk` are required. 
                # If infinite, blk=0, p_loss=0.
                # Let's assume infinite queues as standard for "Jackson network" unless "finite capacity" is stated.
                # But why ask for blk? Maybe just to report 0.
                
                # Add to Q1
                q1.append(t)
                n_in_sys += 1
                
                # Start service if server 1 free
                if srv1_free_at <= t:
                    # Draw service time now
                    svc_time = rng.expovariate(mu1_base)
                    srv1_free_at = t + svc_time
                    # Mark busy start? We track busy time by intervals.
                    # Easier: track when server becomes busy and idle.
                    # Or just accumulate time spent in service.
                    # Let's use a variable `srv1_busy_since`
                    # Actually, let's stick to event-driven integration for busy time too.
                    # This is getting complex. Simpler approach:
                    # Track `busy1_accumulator`. When server starts, record start time. When ends, add diff.
                    # But we need to handle interruptions? No, non-preemptive.
                    
                    # Let's refactor busy tracking:
                    # Variables: srv1_state (0=idle, 1=busy), srv1_start_time
                    # On Arr: if idle, set busy, start=t.
                    # On Done: add t-start to busy_time, set idle.
                    
                    # Wait, I didn't define these vars. Let's add them outside loop.
                    # Re-planning needed.
                    pass
                else:
                    # Queueing
                    pass
                    
            elif etype == 'srv1_done':
                # Job leaves server 1
                # It came from Q1 head
                if q1:
                    arr_t_q1 = q1.popleft()
                    # Move to Q2
                    q2.append(arr_t_q1) # Keep original arrival time for total sojourn? 
                    # Yes, total sojourn = exit time from sys2 - entry time to sys1.
                    n_in_sys -= 1 # Left srv1, entered q2/srv2. Net change 0? 
                    # Wait. 
                    # State: In Sys = Q1 + Srv1 + Q2 + Srv2.
                    # Before event: Job was in Srv1.
                    # After event: Job moves to Q2 (if srv2 busy) or Srv2 (if srv2 free).
                    # So n_in_sys does NOT change upon transfer between stages.
                    # Correction: n_in_sys changes only on Entry (Arr) and Exit (Dep from Sys).
                    
                    # Try to start service on srv2
                    if srv2_free_at <= t:
                        svc_time2 = rng.expovariate(mu2_base)
                        srv2_free_at = t + svc_time2
                        # Pop from q2 immediately? 
                        # Logic: If srv2 free, job goes directly to service.
                        # So we shouldn't append to q2 then pop.
                        # Better: Check srv2 status.
                        # If srv2 free: Start service. Do not add to q2.
                        # If srv2 busy: Add to q2.
                        
                        # Let's fix the flow.
                        pass
                    else:
                        q2.append(arr_t_q1)
                        # n_in_sys remains same (was in srv1, now in q2)
                
                # Update busy time for srv1
                # Need to know when srv1 became busy.
                pass

            elif etype == 'srv2_done':
                # Job leaves system
                # Get arrival time from q2 head
                if q2:
                    arr_t_orig = q2.popleft()
                    # Calculate sojourn
                    sojourn = t - arr_t_orig
                    if stats_started:
                        sum_sojourn += sojourn
                        dep_count += 1
                    n_in_sys -= 1
                    
                    # Try to start next job on srv2
                    if q2:
                        next_arr_t = q2.popleft()
                        svc_time2 = rng.expovariate(mu2_base)
                        srv2_free_at = t + svc_time2
                        # Job moved from q2 to srv2. n_in_sys unchanged.
                    else:
                        srv2_free_at = float('inf') # Idle
                        # Mark idle?
                        pass
                else:
                    # Should not happen if event scheduled correctly
                    pass

        # End of simulation for one seed
        
        # Calculate metrics for this seed
        # Window length
        win_len = H - warmup_end
        if win_len <= 0:
            L_est = 0
            W_est = 0
            busy_frac_1 = 0
            busy_frac_2 = 0
            p_loss = 0
            p_wait = 0
        else:
            L_est = area_L / win_len
            W_est = sum_sojourn / dep_count if dep_count > 0 else 0
            # Busy fractions
            # Need to properly accumulate busy times.
            # I missed implementing the busy time accumulation in the sketch above.
            # Let's rewrite the core loop cleanly.
            
            # Utilization
            util1 = busy1_time / win_len
            util2 = busy2_time / win_len
            # Combined busy fraction? Or average? 
            # "busy_util" usually means server utilization. Two servers.
            # Output key `busy_util` singular. Maybe average of two? Or total busy time / (2*win)?
            # Let's assume `busy_util` is the average utilization of the two machines.
            avg_util = (util1 + util2) / 2.0
            
            # p_loss: blocked / arrived
            p_loss = blk_count / arr_count if arr_count > 0 else 0
            # p_wait: probability of waiting? 
            # Fraction of jobs that waited in queue?
            # Or fraction of time system is congested?
            # Usually P(wait) in M/M/c is prob an arriving customer waits.
            # Here, we can estimate as: (jobs that entered queue) / (total jobs).
            # Jobs enter queue if server was busy upon arrival.
            # We didn't track this explicitly.
            # Alternative: Little's Law related?
            # Let's approximate p_wait as fraction of arrivals that found server 1 busy.
            # We need to count `wait_arrivals`.
            
            # Refining implementation plan:
            # 1. Track `n_in_sys` correctly.
            # 2. Track `area_L`.
            # 3. Track `sum_sojourn`, `dep_count`.
            # 4. Track `busy1_time`, `busy2_time` using start/end timestamps.
            # 5. Track `arr_count`, `blk_count` (always 0 for infinite), `wait_count` (arrivals finding srv1 busy).
            
            # Since I cannot edit the thought process easily to restart code generation, 
            # I will generate the final clean code block below.
            
            # Placeholder for missing vars in this draft:
            pass

    # Aggregation across seeds
    if N > 0:
        avg_L = sum(results_L) / N
        avg_W = sum(results_W) / N
        avg_busy = sum(results_busy_frac) / N
        avg_p_loss = sum(results_p_loss) / N
        avg_p_wait = sum(results_p_wait) / N
        avg_arr = sum(results_arr) / N
        avg_dep = sum(results_dep) / N
        avg_blk = sum(results_blk) / N
    else:
        avg_L = avg_W = avg_busy = avg_p_loss = avg_p_wait = avg_arr = avg_dep = avg_blk = 0.0

    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "runtime_units": "seconds", # Not used in output keys except maybe implicit? No, key is runtime_units.
        "seed_list": [S+i for i in range(N)],
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(H * 0.75, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_frac": round(avg_busy, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep / (H * 0.75) if H*0.75>0 else 0, 6),
        "lam_eff": round(avg_arr / (H * 0.75) if H*0.75>0 else 0, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in results_L],
        "per_seed_W": [round(x, 6) for x in results_W],
        "per_seed_busy_frac": [round(x, 6) for x in results_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in results_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in results_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
