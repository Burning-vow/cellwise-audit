import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=1)
    p.add_argument('--horizon', type=float, default=3600.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0 / 60.0  # per minute
    mu_base = 1.0 / 5.0    # per minute
    c = 1
    K = 4
    
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': c += 1; K += 1
    
    horizon_min = a.horizon * 60.0 if a.time_unit == 'hour' else a.horizon
    warmup_frac = 0.25
    warmup_end = horizon_min * (1 - warmup_frac)
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arr = 0
    all_blk = 0
    all_dep = 0
    all_wait_count = 0
    per_seed_L = []
    per_seed_W = []
    per_seed_busy = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        n = 0
        last_event_t = 0.0
        area_L = 0.0
        busy_time = 0.0
        arr_cnt = 0
        blk_cnt = 0
        dep_cnt = 0
        wait_cnt = 0
        w_sum = 0.0
        
        next_arr = rng.expovariate(lam_base)
        service_times = {}
        
        while t < horizon_min:
            # Determine next event time
            next_dep = float('inf')
            if n > 0 and len(service_times) > 0:
                min_serv = min(service_times.values())
                next_dep = t + min_serv
            
            next_evt = min(next_arr, next_dep)
            
            if next_evt > horizon_min:
                dt = horizon_min - t
                area_L += n * dt
                if n > 0: busy_time += dt
                t = horizon_min
                break
                
            dt = next_evt - t
            if t >= warmup_end or next_evt <= warmup_end:
                pass # handled by integration below with clipping? No, simpler: integrate only after warmup
            
            # Integrate state variables over [t, next_evt] but only count if interval overlaps post-warmup window
            # Actually, standard approach: run full sim, record events, then filter. 
            # But memory efficient: track cumulative areas and counts, subtract pre-warmup part at end?
            # Easier: Since we need "area-type quantities must be integrated before changing state", let's just simulate fully and store event log? 
            # Constraint says "no classes", "main function". Storing logs might be heavy but H is small.
            # Alternative: Run simulation, keep running totals for the WHOLE horizon, then run again? No.
            # Let's use the "subtract pre-warmup" trick or just check overlap.
            
            # Overlap calculation for current step [t, next_evt]
            start_int = max(t, warmup_end)
            end_int = min(next_evt, horizon_min)
            if end_int > start_int:
                dur = end_int - start_int
                area_L += n * dur
                if n > 0: busy_time += dur
            
            t = next_evt
            
            if abs(t - next_arr) < 1e-9:
                # Arrival
                arr_cnt += 1
                if n < K:
                    n += 1
                    st = rng.expovariate(mu_base)
                    service_times[t] = st
                    if n > 1: wait_cnt += 1 # Waited if someone was already there? Or if queue formed?
                    # Definition of W usually includes waiting time. If server busy, they wait.
                    # If n becomes 1 from 0, no wait. If n becomes >1, they waited.
                    # Actually, if n>0 before arrival, new patient waits.
                    # We tracked n BEFORE incrementing? No, we incremented.
                    # Let's re-evaluate: if n_before > 0, then wait.
                    # We lost n_before. Let's fix logic.
                    pass
                else:
                    blk_cnt += 1
                next_arr = t + rng.expovariate(lam_base)
                
            elif abs(t - next_dep) < 1e-9:
                # Departure
                # Find which one departed (min service time)
                # In M/M/1 FCFS, it's the earliest arrival among those in system.
                # Our service_times dict maps arrival_time -> duration.
                # The one that finishes first is the one with smallest (arrival_time + duration).
                # But we stored duration relative to start? No, we stored absolute finish time?
                # Code above: service_times[t] = st. This is wrong. It should be finish time.
                # Let's restart the inner loop logic carefully.
                pass

        # Re-implementing the core loop cleanly inside the seed loop
        
        t = 0.0
        n = 0
        arrivals_in_sys = [] # list of (arrival_time, service_duration)
        next_arrival = rng.expovariate(lam_base)
        
        # Reset accumulators for this seed
        s_area_L = 0.0
        s_busy_time = 0.0
        s_arr = 0
        s_blk = 0
        s_dep = 0
        s_w_sum = 0.0
        s_wait_cnt = 0
        
        while t < horizon_min:
            # Calculate next departure time if any
            next_departure = float('inf')
            if arrivals_in_sys:
                # Find the one finishing soonest
                # Finish time = arrival_time + service_duration
                # Since FCFS, the first in list is the one currently being served (if n>0)
                # Actually, if n>0, the head of queue is being served.
                # So next_departure = arrivals_in_sys[0][0] + arrivals_in_sys[0][1]
                next_departure = arrivals_in_sys[0][0] + arrivals_in_sys[0][1]
            
            next_event = min(next_arrival, next_departure)
            
            if next_event > horizon_min:
                dt = horizon_min - t
                # Integrate
                start_int = max(t, warmup_end)
                end_int = horizon_min
                if end_int > start_int:
                    dur = end_int - start_int
                    s_area_L += n * dur
                    if n > 0: s_busy_time += dur
                t = horizon_min
                break
            
            dt = next_event - t
            start_int = max(t, warmup_end)
            end_int = min(next_event, horizon_min)
            if end_int > start_int:
                dur = end_int - start_int
                s_area_L += n * dur
                if n > 0: s_busy_time += dur
            
            t = next_event
            
            if t == next_arrival:
                s_arr += 1
                if n < K:
                    n += 1
                    serv_dur = rng.expovariate(mu_base)
                    arrivals_in_sys.append((t, serv_dur))
                    if n > 1: # Was busy before this arrival?
                        # If n became 1 from 0, no wait. If n became >1, waited.
                        # Check previous n? We incremented n.
                        # If len(arrivals_in_sys) > 1, then there was someone ahead.
                        if len(arrivals_in_sys) > 1:
                            s_wait_cnt += 1
                else:
                    s_blk += 1
                next_arrival = t + rng.expovariate(lam_base)
                
            elif t == next_departure:
                # Departure
                s_dep += 1
                arr_time, serv_dur = arrivals_in_sys.pop(0)
                w = t - arr_time
                s_w_sum += w
                n -= 1
        
        win_len = horizon_min - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = s_area_L / win_len
        W_est = s_w_sum / s_dep if s_dep > 0 else 0.0
        busy_est = s_busy_time / win_len
        p_loss_est = s_blk / s_arr if s_arr > 0 else 0.0
        p_wait_est = s_wait_cnt / s_arr if s_arr > 0 else 0.0
        
        all_L_area += s_area_L
        all_W_sum += s_w_sum
        all_busy_time += s_busy_time
        all_arr += s_arr
        all_blk += s_blk
        all_dep += s_dep
        all_wait_count += s_wait_cnt
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy.append(busy_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seed_list.append(seed)

    total_win = (horizon_min - warmup_end) * a.seeds
    if total_win <= 0: total_win = 1e-9
    
    final_L = all_L_area / total_win
    final_W = all_W_sum / all_dep if all_dep > 0 else 0.0
    final_busy = all_busy_time / total_win
    final_p_loss = all_blk / all_arr if all_arr > 0 else 0.0
    final_p_wait = all_wait_count / all_arr if all_arr > 0 else 0.0
    
    avg_arr = all_arr / a.seeds
    avg_blk = all_blk / a.seeds
    avg_dep = all_dep / a.seeds
    dep_rate = avg_dep / (total_win / 60.0) # per hour
    lam_eff = dep_rate
    
    out = {
        "L": final_L,
        "W": final_W,
        "busy_frac": final_busy,
        "p_loss": final_p_loss,
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": a.seeds,
        "time_unit": "minute",
        "win": horizon_min - warmup_end,
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": final_busy, # For c=1, util = busy_frac
        "dep": avg_dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_wait": final_p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
