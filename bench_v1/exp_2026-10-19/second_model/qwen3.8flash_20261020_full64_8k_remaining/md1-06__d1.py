import sys, json, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 8.0
    mu_base = 60.0 / 5.0 # 12 per hour (since service is 5 mins = 1/12 hour)
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H * 0.75 # Remove first 25% as warmup
    start_time_warmup = H * 0.25
    
    total_L_sum = 0.0
    total_W_sum = 0.0
    total_busy_frac_sum = 0.0
    total_arr_count = 0
    total_dep_count = 0
    total_blk_count = 0
    total_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(N_seeds):
        seed_id = S_start + i
        seed_list.append(seed_id)
        rng = random.Random(seed_id)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        queue = [] # List of arrival times
        n_in_system = 0
        busy_time_accum = 0.0
        last_event_time = 0.0
        state_last_change = 0.0
        
        # For L calculation via area integral
        area_L = 0.0
        current_n = 0
        
        # Stats within window
        arr_win = 0
        dep_win = 0
        blk_win = 0
        wait_win = 0
        sum_W_win = 0.0
        
        while t < H:
            # Determine next event
            if next_arrival < next_departure:
                t_next = next_arrival
                event_type = 'arrival'
            else:
                t_next = next_departure
                event_type = 'departure'
                
            if t_next > H:
                break
                
            # Integrate area for L before changing state
            dt = t_next - t
            if t >= start_time_warmup:
                area_L += current_n * dt
                if current_n > 0:
                    busy_time_accum += dt
            
            t = t_next
            
            if event_type == 'arrival':
                # Generate service time now (fixed 5 mins = 1/12 hour)
                svc_time = 1.0 / 12.0
                # Check capacity? Problem says "auto car wash", usually single server queue with infinite buffer unless specified blocking. 
                # "blk" implies blocking/loss. Standard M/M/1 has no loss. But prompt asks for blk and p_loss.
                # If it's a single bay, cars wait. If system is full? No max capacity given. 
                # However, "blk" is requested. In standard queues without finite capacity, blk=0.
                # Let's assume infinite buffer, so blk=0 always.
                
                if t >= start_time_warmup:
                    arr_win += 1
                
                queue.append((t, svc_time))
                current_n += 1
                
                if len(queue) == 1:
                    # Start service immediately
                    next_departure = t + svc_time
                else:
                    # Waiting
                    pass
                    
                next_arrival = t + rng.expovariate(lam)
                
            else: # departure
                if not queue:
                    next_departure = float('inf')
                    continue
                    
                # Complete the head of queue
                arr_t, svc_t = queue.pop(0)
                current_n -= 1
                dep_t = t
                
                if t >= start_time_warmup:
                    dep_win += 1
                    w = dep_t - arr_t
                    sum_W_win += w
                    if w > 0: # Waited in queue (service started after arrival)
                        wait_win += 1
                        
                if queue:
                    # Next customer starts service immediately
                    next_svc_t = queue[0][1]
                    next_departure = t + next_svc_t
                else:
                    next_departure = float('inf')
                    
        # End of simulation loop for this seed
        
        # Calculate stats for this seed
        if win > 0:
            l_val = area_L / win
            w_val = sum_W_win / dep_win if dep_win > 0 else 0.0
            bf_val = busy_time_accum / win
            pl_val = blk_win / arr_win if arr_win > 0 else 0.0
            pw_val = wait_win / dep_win if dep_win > 0 else 0.0
        else:
            l_val = 0.0
            w_val = 0.0
            bf_val = 0.0
            pl_val = 0.0
            pw_val = 0.0
            
        per_seed_L.append(l_val)
        per_seed_W.append(w_val)
        per_seed_busy_frac.append(bf_val)
        per_seed_p_loss.append(pl_val)
        per_seed_p_wait.append(pw_val)
        
        total_L_sum += l_val
        total_W_sum += w_val
        total_busy_frac_sum += bf_val
        total_arr_count += arr_win
        total_dep_count += dep_win
        total_blk_count += blk_win
        total_wait_count += wait_win

    seeds_used = N_seeds
    avg_L = total_L_sum / seeds_used if seeds_used > 0 else 0.0
    avg_W = total_W_sum / seeds_used if seeds_used > 0 else 0.0
    avg_busy_frac = total_busy_frac_sum / seeds_used if seeds_used > 0 else 0.0
    
    # Convert W to minutes
    W_min = avg_W * 60.0
    
    # Busy util E[min(N,c)]/c -> c=1, so just avg_N_if_busy? No, utilization is fraction of time busy.
    # busy_util = avg_busy_frac
    # busy_occupied = 1 - pi_0. pi_0 is prob empty. 
    # In steady state M/M/1, P(empty) = 1 - rho. Utilization = rho.
    # So busy_util should be close to avg_busy_frac.
    # busy_occupied = 1 - (fraction of time empty).
    # Fraction of time empty = 1 - avg_busy_frac.
    # So busy_occupied = avg_busy_frac.
    
    busy_util = avg_busy_frac
    busy_occupied = avg_busy_frac
    
    dep_rate = (total_dep_count / seeds_used) / win if win > 0 else 0.0
    lam_eff = dep_rate
    
    p_loss_total = total_blk_count / total_arr_count if total_arr_count > 0 else 0.0
    p_wait_total = total_wait_count / total_dep_count if total_dep_count > 0 else 0.0
    
    out = {
        "L": round(avg_L, 4),
        "W": round(W_min, 4),
        "busy_frac": round(avg_busy_frac, 4),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(total_arr_count / seeds_used, 4),
        "blk": round(total_blk_count / seeds_used, 4),
        "busy_util": round(busy_util, 4),
        "dep": round(total_dep_count / seeds_used, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(p_loss_total, 4),
        "p_wait": round(p_wait_total, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    
    print(json.dumps(out))

if __name__ == "__main__":
    main()
