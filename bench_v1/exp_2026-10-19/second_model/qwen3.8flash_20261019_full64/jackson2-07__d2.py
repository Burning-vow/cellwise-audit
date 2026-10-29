import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam = 6.0
    mu = 10.0
    if a.pert == 'lam_up': lam *= 1.2
    elif a.pert == 'mu_up': mu *= 1.2
    elif a.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        
        # State: (t, event_type, job_id, stage, service_time)
        # event_type: 0=arrival, 1=completion_s1, 2=completion_s2
        events = []
        import heapq
        heapq.heappush(events, (next_arr, 0, 0, 1, None))
        
        q1 = [] # jobs waiting at stage 1
        q2 = [] # jobs waiting at stage 2
        busy1 = False
        busy2 = False
        s1_end = None
        s2_end = None
        
        job_counter = 0
        arrivals_in_win = 0
        departures_in_win = 0
        blocks_in_win = 0
        
        # For L calculation: area under number of jobs in system
        num_jobs = 0
        last_t = 0.0
        area_jobs = 0.0
        
        # For W calculation: sum of sojourn times for completed jobs in window
        sojourn_sum = 0.0
        
        # Busy fractions
        busy1_time = 0.0
        busy2_time = 0.0
        last_busy1_t = 0.0
        last_busy2_t = 0.0
        
        # Wait probability: fraction of arrivals that had to wait? 
        # Or fraction of time queues are non-empty? Usually p_wait is prob an arrival waits.
        # Let's count arrivals that found server busy or queue non-empty.
        waited_count = 0
        
        while events and t < horizon:
            t, etype, jid, stage, stime = heapq.heappop(events)
            
            # Update integrals before state change
            dt = t - last_t
            if t > win_start:
                area_jobs += num_jobs * dt
                if busy1: busy1_time += dt
                if busy2: busy2_time += dt
            
            last_t = t
            
            if etype == 0: # Arrival
                job_counter += 1
                new_jid = job_counter
                # Generate service times now
                s1 = rng.expovariate(mu)
                s2 = rng.expovariate(mu)
                
                if t >= win_start:
                    arrivals_in_win += 1
                
                # Check capacity? Problem doesn't specify finite buffer, assume infinite.
                # But "blk" suggests blocking/loss. If no loss mechanism defined, blk=0.
                # Standard Jackson network has infinite buffers. 
                # However, prompt asks for blk. Maybe it refers to something else?
                # Or maybe we should assume finite capacity? No, not specified.
                # Let's assume blk=0 unless there's a specific constraint.
                # Actually, if the system is stable, blk is 0.
                
                num_jobs += 1
                
                # Add to Q1
                q1.append((new_jid, s1, s2, t))
                
                # Try to start service on S1
                if not busy1:
                    busy1 = True
                    jid_s1, s1_dur, s2_dur, arr_t = q1.pop(0)
                    s1_end = t + s1_dur
                    heapq.heappush(events, (s1_end, 1, jid_s1, 1, (s1_dur, s2_dur, arr_t)))
                else:
                    # Arrived and had to wait
                    if t >= win_start:
                        waited_count += 1
                
                # Schedule next arrival
                next_arr = t + rng.expovariate(lam)
                heapq.heappush(events, (next_arr, 0, 0, 1, None))
                
            elif etype == 1: # Completion Stage 1
                busy1 = False
                jid_done, info = jid, stime
                s1_dur, s2_dur, arr_t = info
                
                # Move to Q2
                q2.append((jid_done, s2_dur, arr_t))
                
                # Try to start service on S2
                if not busy2:
                    busy2 = True
                    jid_s2, s2_d, arr_t2 = q2.pop(0)
                    s2_end = t + s2_d
                    heapq.heappush(events, (s2_end, 2, jid_s2, 2, (s2_d, arr_t2)))
                    
            elif etype == 2: # Completion Stage 2
                busy2 = False
                jid_done, info = jid, stime
                s2_dur, arr_t = info
                
                num_jobs -= 1
                
                if t >= win_start:
                    departures_in_win += 1
                    sojourn_sum += (t - arr_t)
                
                # Try to start next job on S2
                if q2:
                    busy2 = True
                    jid_s2, s2_d, arr_t2 = q2.pop(0)
                    s2_end = t + s2_d
                    heapq.heappush(events, (s2_end, 2, jid_s2, 2, (s2_d, arr_t2)))
                
                # Note: Jobs leaving system don't trigger new arrivals directly here, 
                # but they free up space if any. Since infinite buffer, no effect on arrival rate.
                
                # Also check if S1 can start? No, S1 completion moves to S2.
                # Does S2 completion affect S1? No.
                
                # What about S1 queue? It was handled in etype==1.
                
        # End simulation loop for this seed
        
        # Calculate metrics for this seed
        L_est = area_jobs / win_len if win_len > 0 else 0
        W_est = sojourn_sum / departures_in_win if departures_in_win > 0 else 0
        busy_frac_est = (busy1_time + busy2_time) / (2 * win_len) if win_len > 0 else 0
        # Busy util usually means fraction of time servers are busy. 
        # Here we have 2 servers. Total busy time / (2 * window).
        
        p_loss_est = 0.0 # Assuming no loss
        p_wait_est = waited_count / arrivals_in_win if arrivals_in_win > 0 else 0
        
        seeds_used.append(seed)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        total_arr += arrivals_in_win
        total_dep += departures_in_win
        total_blk += 0 # No losses
        
    n_seeds = len(seeds_used)
    avg_L = sum(per_seed_L) / n_seeds
    avg_W = sum(per_seed_W) / n_seeds
    avg_busy = sum(per_seed_busy_frac) / n_seeds
    avg_p_loss = sum(per_seed_p_loss) / n_seeds
    avg_p_wait = sum(per_seed_p_wait) / n_seeds
    
    avg_arr = total_arr / n_seeds
    avg_dep = total_dep / n_seeds
    avg_blk = total_blk / n_seeds
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff = dep_rate
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "seconds",
        "seed_list": seeds_used,
        "seeds_used": n_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_busy, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
