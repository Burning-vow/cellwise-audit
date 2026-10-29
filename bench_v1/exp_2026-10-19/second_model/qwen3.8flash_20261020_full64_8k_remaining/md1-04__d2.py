import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed-start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 12.0 # 5 min service -> 12 per hour
    
    if pert == 'lam_up': lam = lam_base * 1.2
    elif pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif pert == 'c_up': lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occ = []
    
    seed_list = []
    
    for i in range(N_seeds):
        s_id = S_start + i
        seed_list.append(s_id)
        rng = random.Random(s_id)
        
        t = 0.0
        next_arr_t = rng.expovariate(lam)
        serv_time = 1.0 / mu
        
        queue = [] # list of arrival times
        busy_until = 0.0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        
        # For area integration
        last_event_t = 0.0
        area_N = 0.0
        area_busy = 0.0
        total_wait_area = 0.0 # sum of (departure - arrival) for completed services in window
        
        # We need to track state changes to integrate properly.
        # Since it's a single server FCFS with no loss (infinite capacity implied by "auto car wash" usually, but prompt mentions blk/p_loss. 
        # Standard M/M/1 has no blocking unless finite capacity. Prompt says "先到先洗", doesn't specify capacity limit. 
        # However, output requires blk and p_loss. If infinite capacity, blk=0, p_loss=0.
        # Let's assume infinite capacity as is standard for basic M/M/1 unless specified otherwise. 
        # But wait, "blk" is requested. If I assume infinite, blk is always 0.
        # Let's re-read carefully: "某自动洗车机... 车辆按泊松流到达... 请给出稳态平均停留时间 W ... 与场内平均车辆数 L".
        # It does not mention a buffer size or rejection policy. 
        # Usually, if not mentioned, it's infinite queue. Thus blk=0, p_loss=0.
        # I will implement infinite queue.
        
        while t < H:
            # Determine next event time
            if queue:
                next_serv_end = busy_until
            else:
                next_serv_end = float('inf')
            
            next_event = min(next_arr_t, next_serv_end)
            
            if next_event > H:
                break
                
            dt = next_event - t
            
            # Integrate areas before updating state
            n_curr = len(queue) + (1 if t < busy_until else 0)
            # Actually, simpler: N(t) is number in system.
            # If server busy, N >= 1. Queue length is len(queue). Total N = len(queue) + (1 if busy else 0).
            # But we are at time t, just before event.
            # State during [t, next_event):
            is_busy = t < busy_until
            n_sys = len(queue) + (1 if is_busy else 0)
            
            area_N += n_sys * dt
            if is_busy:
                area_busy += 1 * dt
            
            t = next_event
            
            if abs(t - next_arr_t) < 1e-9:
                # Arrival
                arr_count += 1
                # Check if we should start recording stats? No, we record everything then filter later?
                # Prompt: "统计量只在去掉前 25% 预热后的窗口内累计"
                # This implies we need to know which events fall in the window.
                # Easier approach: Run simulation, store events? Or run two passes?
                # Or: Only accumulate stats if t >= warmup_time.
                
                warmup_t = H * warmup_frac
                
                if t >= warmup_t:
                    # This arrival is in window.
                    # But wait, if an arrival happens before warmup, but departure after, 
                    # its waiting time contributes to W in the window?
                    # Standard definition: W is average time spent in system for customers who DEPART in the window?
                    # Or customers who ARRIVE in the window?
                    # Usually, for steady state estimation via time averages:
                    # L = Area / Time.
                    # W = L / lambda_eff.
                    # The prompt asks for W and L.
                    # "面积型量必须在改变状态之前积分" -> L is area based.
                    # W can be derived from Little's Law or direct customer tracking.
                    # Given "per_seed_W", likely direct tracking or Little's law.
                    # Let's use Little's Law for consistency with L and lambda, OR track individual sojourns.
                    # Tracking individual sojourns for those departing in window is common.
                    
                    pass
                
                # Add to queue
                queue.append(t)
                
                # Generate next arrival
                next_arr_t = t + rng.expovariate(lam)
                
            elif abs(t - next_serv_end) < 1e-9:
                # Departure
                if queue:
                    arr_time = queue.pop(0)
                    dep_count += 1
                    
                    warmup_t = H * warmup_frac
                    if t >= warmup_t:
                        # Customer departed in window.
                        # Sojourn time = t - arr_time
                        total_wait_area += (t - arr_time)
                        
                    # Server becomes idle if queue empty
                    if not queue:
                        busy_until = float('inf')
                    else:
                        # Start next service immediately
                        # Service time was fixed, already known.
                        # Next end time = current time + service time
                        busy_until = t + serv_time
                else:
                    # Should not happen if logic correct
                    busy_until = float('inf')

        # End of simulation loop for this seed
        
        # Calculate metrics for this seed
        # Window length is win_len
        # Area_N accumulated only when t >= warmup? 
        # NO. My integration above integrated over ALL time [0, H].
        # I need to restrict integration to [warmup_t, H].
        
        # Correction: The loop integrates over the whole timeline.
        # To get window stats, I must either:
        # 1. Reset accumulators at warmup_t.
        # 2. Subtract pre-warmup area.
        
        # Let's restart the accumulation logic inside the loop more carefully.
        # I will rewrite the inner loop logic to handle the warmup cutoff correctly.
        
        # Re-initializing variables for correct calculation
        # (Since I can't easily edit the previous block in my head without rewriting the whole function structure, 
        # I will write the final code assuming the logic below handles the window correctly.)
        
        # Strategy: 
        # Keep running totals for Area_N, Area_Busy, Count_Arr_Window, Count_Dep_Window, Sum_Sojourn_Window.
        # When crossing warmup boundary, reset these specific counters.
        
        # Let's redo the seed loop body properly.
        pass 

    # Due to complexity of resetting mid-loop in a single pass without storing history,
    # I will implement a check: if t crosses warmup, reset accumulators.
    
    # Final Code Structure Plan:
    # 1. Parse args.
    # 2. Loop seeds.
    # 3. Inside seed loop:
    #    - Init RNG, state vars.
    #    - Init accumulators: area_N_win, area_busy_win, arr_win, dep_win, blk_win, soj_sum_win.
    #    - warmup_t = H * 0.25
    #    - crossed_warmup = False
    #    - While t < H:
    #       - Find next event.
    #       - dt = next_event - t
    #       - If crossed_warmup: add dt * n_sys to area_N_win, etc.
    #       - Else if t < warmup_t and next_event >= warmup_t:
    #           - Split interval: part 1 [t, warmup_t] ignored. Part 2 [warmup_t, next_event] counted.
    #           - Set crossed_warmup = True.
    #           - Add remaining dt to accumulators.
    #       - Update t = next_event.
    #       - Process event (Arrival/Departure).
    #         - If crossed_warmup: increment arr_win/dep_win, add sojourn to sum if dep.
    #    - Compute L = area_N_win / win_len
    #    - Compute W = soj_sum_win / dep_win (if dep_win > 0)
    #    - Compute busy_frac = area_busy_win / win_len
    #    - Compute p_loss = blk_win / arr_win (if arr_win > 0)
    #    - Compute p_wait = ? (Prob of waiting? In M/M/1 infinite, P(wait) = rho. 
    #      Empirical: fraction of arrivals that found server busy? 
    #      Or fraction of departures that had wait > 0? 
    #      Usually p_wait is probability an arriving customer waits.
    #      I'll count arrivals where queue was non-empty or server busy upon arrival.)
    
    # Let's refine p_wait: Probability that an arriving customer has to wait.
    # In FCFS, if server is busy, they wait.
    # Count arrivals in window where (server busy OR queue non-empty).
    
    # Let's write the code.

    results_L = []
    results_W = []
    results_busy = []
    results_ploss = []
    results_pwait = []
    results_arr = []
    results_dep = []
    results_blk = []
    results_butil = []
    results_bocc = []
    
    for i in range(N_seeds):
        s_id = S_start + i
        rng = random.Random(s_id)
        
        t = 0.0
        next_arr_t = rng.expovariate(lam)
        serv_dur = 1.0 / mu
        
        queue = []
        busy_until = 0.0
        
        warmup_t = H * 0.25
        win_len = H - warmup_t
        
        # Accumulators for window
        area_N = 0.0
        area_busy = 0.0
        cnt_arr = 0
        cnt_dep = 0
        cnt_blk = 0
        sum_soj = 0.0
        cnt_wait_arr = 0 # Arrivals that waited
        
        in_window = False
        
        while t < H:
            # Determine next event
            if queue:
                next_serv_end = busy_until
            else:
                next_serv_end = float('inf')
            
            next_event = min(next_arr_t, next_serv_end)
            
            if next_event > H:
                next_event = H # Cap at horizon for integration? 
                # Actually, if next_event > H, we stop. But we need to integrate up to H.
                # So set next_event = H for the final step.
                pass
            
            dt = next_event - t
            
            # Current state during [t, next_event)
            is_busy = t < busy_until
            n_sys = len(queue) + (1 if is_busy else 0)
            
            # Handle Warmup Crossing
            if not in_window:
                if t >= warmup_t:
                    in_window = True
                    # Integrate full dt
                    area_N += n_sys * dt
                    if is_busy: area_busy += dt
                elif next_event > warmup_t:
                    # Crosses boundary
                    dt_pre = warmup_t - t
                    dt_post = next_event - warmup_t
                    # Ignore dt_pre
                    area_N += n_sys * dt_post
                    if is_busy: area_busy += dt_post
                    in_window = True
                else:
                    # Entirely in warmup, ignore
                    pass
            else:
                # Already in window
                area_N += n_sys * dt
                if is_busy: area_busy += dt
            
            t = next_event
            
            if t >= H:
                break
                
            if abs(t - next_arr_t) < 1e-9:
                # Arrival Event
                if in_window:
                    cnt_arr += 1
                    # Did they wait?
                    if is_busy or len(queue) > 0:
                        cnt_wait_arr += 1
                
                queue.append(t)
                next_arr_t = t + rng.expovariate(lam)
                
            elif abs(t - next_serv_end) < 1e-9:
                # Departure Event
                if queue:
                    arr_time = queue.pop(0)
                    if in_window:
                        cnt_dep += 1
                        sum_soj += (t - arr_time)
                    
                    if not queue:
                        busy_until = float('inf')
                    else:
                        busy_until = t + serv_dur
                else:
                    busy_until = float('inf')
        
        # Calculate Seed Metrics
        L_val = area_N / win_len if win_len > 0 else 0
        W_val = sum_soj / cnt_dep if cnt_dep > 0 else 0
        busy_frac_val = area_busy / win_len if win_len > 0 else 0
        
        # Busy Utilization E[min(N,c)]/c. Here c=1. E[N]/1 = L_val? 
        # Wait, busy_util defined as E[min(N,c)]/c. For c=1, min(N,1) is 1 if N>=1, 0 if N=0.
        # So E[min(N,1)] = P(N>=1) = busy_frac_val.
        # So busy_util = busy_frac_val.
        # busy_occupied = 1 - pi_0. pi_0 is prob N=0. 1-pi_0 = P(N>0) = busy_frac_val.
        # They are identical for c=1.
        
        p_loss_val = cnt_blk / cnt_arr if cnt_arr > 0 else 0
        p_wait_val = cnt_wait_arr / cnt_arr if cnt_arr > 0 else 0
        
        results_L.append(L_val)
        results_W.append(W_val)
        results_busy.append(busy_frac_val)
        results_ploss.append(p_loss_val)
        results_pwait.append(p_wait_val)
        results_arr.append(cnt_arr)
        results_dep.append(cnt_dep)
        results_blk.append(cnt_blk)
        results_butil.append(busy_frac_val)
        results_bocc.append(busy_frac_val)

    # Aggregate
    avg_L = sum(results_L) / N_seeds
    avg_W = sum(results_W) / N_seeds
    avg_busy = sum(results_busy) / N_seeds
    avg_ploss = sum(results_ploss) / N_seeds
    avg_pwait = sum(results_pwait) / N_seeds
    avg_arr = sum(results_arr) / N_seeds
    avg_dep = sum(results_dep) / N_seeds
    avg_blk = sum(results_blk) / N_seeds
    avg_butil = sum(results_butil) / N_seeds
    avg_bocc = sum(results_bocc) / N_seeds
    
    dep_rate = avg_dep / (win_len / 60.0) if win_len > 0 else 0 # Per hour. Win_len is in hours? 
    # Wait, time_unit. I used hours for lam/mu/t.
    # So win_len is in hours.
    # dep_rate = avg_dep / win_len (per hour).
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    
    lam_eff = dep_rate # Effective arrival rate = departure rate in stable system
    
    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy, 4),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": N_seeds,
        "time_unit": "hour",
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_butil, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(avg_ploss, 4),
        "p_wait": round(avg_pwait, 4),
        "per_seed_L": [round(x, 4) for x in results_L],
        "per_seed_W": [round(x, 4) for x in results_W],
        "per_seed_busy_frac": [round(x, 4) for x in results_busy],
        "per_seed_p_loss": [round(x, 4) for x in results_ploss],
        "per_seed_p_wait": [round(x, 4) for x in results_pwait],
        "busy_occupied": round(avg_bocc, 4)
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
