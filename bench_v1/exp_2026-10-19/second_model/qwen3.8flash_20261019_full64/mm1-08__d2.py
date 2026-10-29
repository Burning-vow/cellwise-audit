import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert

    # Parameters in minutes
    lam_base = 8.0 / 60.0  # arrivals per minute
    mu_base = 1.0 / 5.0    # service rate per minute (mean service time 5 min)
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # c is number of servers, here fixed at 1, but if we were to change capacity... 
        # The problem says "only 1 clerk", so c=1. Perturbation might imply changing something else?
        # But spec says "perturbation only changes parameters not structure".
        # If c_up means increasing capacity, it would break the single server assumption or just make it M/M/1 with higher c?
        # Given the base model is M/M/1, let's assume standard params unless specified otherwise for none/lam_up/mu_up.
        # For c_up, since we can't add servers easily without restructuring, and the prompt implies simple param change,
        # maybe it's a trick or just uses base. Let's stick to base for c_up as no clear mapping provided for single server queue capacity increase in this context without code restructure.
        # Actually, usually c_up might mean cost up? Or capacity up. If capacity up, it becomes M/M/c.
        # However, the task is specifically about an M/M/1 queue ("only 1 clerk").
        # Let's assume for 'none' and others that don't apply directly, we use base.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    # Warmup fraction
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    start_time_warmup = H * warmup_frac
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arrivals = 0
    total_departures = 0
    total_losses = 0 # In M/M/1 infinite buffer, losses are 0 unless blocked by finite capacity. Problem doesn't specify finite capacity, so assume infinite.
    total_wait_events = 0 # Number of customers who waited
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seed_list = []
    
    for i in range(N):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        n_customers = 0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        # Statistics accumulators for this seed
        s_L_area = 0.0
        s_W_sum = 0.0
        s_busy_time = 0.0
        s_arrivals = 0
        s_departures = 0
        s_losses = 0
        s_wait_count = 0
        
        # We need to track when each customer arrives to calculate W later? 
        # No, we can accumulate W sum upon departure if we store arrival time.
        # Queue implementation: list of arrival times
        queue = [] 
        
        last_event_time = 0.0
        
        while t < H:
            # Determine next event time
            next_t = min(next_arrival, next_departure)
            
            if next_t > H:
                next_t = H
            
            dt = next_t - t
            
            # Integrate L (area under curve)
            # L is current number of customers in system
            s_L_area += n_customers * dt
            
            # Integrate busy time
            if n_customers > 0:
                s_busy_time += dt
                
            t = next_t
            
            if t >= H:
                break
                
            # Process event
            if abs(t - next_arrival) < 1e-9:
                # Arrival
                s_arrivals += 1
                queue.append(t)
                n_customers += 1
                
                # If server was idle, start service immediately
                if n_customers == 1:
                    serv_time = rng.expovariate(mu)
                    next_departure = t + serv_time
                
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - next_departure) < 1e-9:
                # Departure
                s_departures += 1
                arr_time = queue.pop(0)
                w = t - arr_time
                s_W_sum += w
                if w > 1e-9:
                    s_wait_count += 1
                    
                n_customers -= 1
                
                if n_customers > 0:
                    serv_time = rng.expovariate(mu)
                    next_departure = t + serv_time
                else:
                    next_departure = float('inf')
                    
            else:
                # Should not happen
                pass

        # Calculate stats for this seed over the window [start_time_warmup, H]
        # Wait, the integration above was over [0, H]. We need to subtract the warmup part.
        # This approach is tricky because events cross the boundary.
        # Better approach: Run simulation until H, but only accumulate stats after warmup period.
        # Let's restart logic slightly to handle warmup correctly.
        
        # Re-run simulation for this seed with correct warmup handling
        rng = random.Random(seed)
        t = 0.0
        n_customers = 0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        queue = []
        
        s_L_area_win = 0.0
        s_W_sum_win = 0.0
        s_busy_time_win = 0.0
        s_arrivals_win = 0
        s_departures_win = 0
        s_losses_win = 0
        s_wait_count_win = 0
        
        # We need to know how many customers arrived before warmup ended to exclude their W?
        # "Statistics accumulated only in window after removing first 25% warmup"
        # Usually means:
        # 1. Time-average quantities (L, Busy) integrated over [warmup_end, H]
        # 2. Event-based quantities (W, p_wait) calculated from customers whose *entire* stay or *arrival/departure* falls in window?
        # Standard practice: 
        # - Area integrals: integrate from T_warmup to H.
        # - Counts: count arrivals/departures in [T_warmup, H].
        # - W: average waiting time of customers who departed in [T_warmup, H]? Or arrived?
        # Usually, for steady state estimation, we take all departures in the window.
        
        warmup_end = H * warmup_frac
        
        while t < H:
            next_t = min(next_arrival, next_departure)
            if next_t > H:
                next_t = H
            
            dt = next_t - t
            
            # Only integrate if we are past warmup
            if t >= warmup_end:
                s_L_area_win += n_customers * dt
                if n_customers > 0:
                    s_busy_time_win += dt
            elif next_t > warmup_end:
                # Split interval
                dt_pre = warmup_end - t
                dt_post = next_t - warmup_end
                # Pre part ignored
                s_L_area_win += n_customers * dt_post
                if n_customers > 0:
                    s_busy_time_win += dt_post
            
            t = next_t
            
            if t >= H:
                break
                
            if abs(t - next_arrival) < 1e-9:
                if t >= warmup_end:
                    s_arrivals_win += 1
                queue.append(t)
                n_customers += 1
                if n_customers == 1:
                    serv_time = rng.expovariate(mu)
                    next_departure = t + serv_time
                next_arrival = t + rng.expovariate(lam)
                
            elif abs(t - next_departure) < 1e-9:
                if t >= warmup_end:
                    s_departures_win += 1
                    arr_time = queue.pop(0)
                    w = t - arr_time
                    s_W_sum_win += w
                    if w > 1e-9:
                        s_wait_count_win += 1
                else:
                    # Customer departed during warmup, remove from queue
                    if queue:
                        queue.pop(0)
                
                n_customers -= 1
                if n_customers > 0:
                    serv_time = rng.expovariate(mu)
                    next_departure = t + serv_time
                else:
                    next_departure = float('inf')
        
        # Compute per-seed metrics
        # L = Average number in system = Area / Window Length
        avg_L = s_L_area_win / win_len if win_len > 0 else 0.0
        
        # W = Average time in system = Total time spent by departing customers / Number of departing customers
        # Note: Using Little's Law consistency check later.
        avg_W = s_W_sum_win / s_departures_win if s_departures_win > 0 else 0.0
        
        # Busy Fraction = Busy Time / Window Length
        b_frac = s_busy_time_win / win_len if win_len > 0 else 0.0
        
        # P_wait = Proportion of customers who waited (W > 0) among those counted in window
        # Here we used departures in window.
        p_wait = s_wait_count_win / s_departures_win if s_departures_win > 0 else 0.0
        
        # P_loss = Losses / Arrivals. Infinite buffer -> 0.
        p_loss = 0.0
        
        per_seed_L.append(avg_L)
        per_seed_W.append(avg_W)
        per_seed_busy_frac.append(b_frac)
        per_seed_p_loss.append(p_loss)
        per_seed_p_wait.append(p_wait)
        
        total_L_area += s_L_area_win
        total_W_sum += s_W_sum_win
        total_busy_time += s_busy_time_win
        total_arrivals += s_arrivals_win
        total_departures += s_departures_win
        total_losses += s_losses_win
        total_wait_events += s_wait_count_win

    # Aggregate statistics
    seeds_used = N
    final_L = total_L_area / (N * win_len) if N > 0 and win_len > 0 else 0.0
    final_W = total_W_sum / total_departures if total_departures > 0 else 0.0
    final_busy_frac = total_busy_time / (N * win_len) if N > 0 and win_len > 0 else 0.0
    final_p_wait = total_wait_events / total_departures if total_departures > 0 else 0.0
    final_p_loss = total_losses / total_arrivals if total_arrivals > 0 else 0.0
    
    # Additional fields
    arr_avg = total_arrivals / N if N > 0 else 0.0
    dep_avg = total_departures / N if N > 0 else 0.0
    blk_avg = total_losses / N if N > 0 else 0.0
    
    # Dep rate in per hour
    # Total departures across all seeds in window length win_len (minutes)
    # Rate = (Total Deps / Total Time) * 60
    total_time_min = N * win_len
    dep_rate_per_hour = (total_departures / total_time_min) * 60.0 if total_time_min > 0 else 0.0
    
    lam_eff = dep_rate_per_hour # Effective arrival rate equals departure rate in stable system
    
    # busy_util = E[min(N,c)]/c. For c=1, E[N]/1 = L. So same as L?
    # Spec says: "busy_frac definition ... = E[min(N,1)]/1 ... report busy_util=E[min(N,c)]/c and busy_occupied=1-pi0"
    # For M/M/1, pi0 = 1 - rho. busy_occupied = rho.
    # busy_util = L / 1 = L.
    # busy_frac = rho = lambda/mu.
    # Let's compute them based on simulation data.
    
    # busy_util is essentially L for c=1
    busy_util = final_L
    
    # busy_occupied = 1 - pi0. pi0 is prob system empty.
    # We didn't explicitly track empty time area separately from busy time?
    # Busy time area = integral of 1_{N>0}.
    # Empty time area = integral of 1_{N==0} = win_len - busy_time_area.
    # pi0_est = Empty_time_area / win_len.
    # busy_occupied = 1 - pi0_est = Busy_time_area / win_len = final_busy_frac.
    # So for c=1, busy_frac == busy_occupied == busy_util?
    # No. busy_util = E[N]/c = L.
    # busy_frac = P(Busy) = rho.
    # They are different values generally.
    
    busy_occupied = final_busy_frac
    
    result = {
        "L": round(final_L, 6),
        "W": round(final_W, 6),
        "busy_frac": round(final_busy_frac, 6),
        "p_wait": round(final_p_wait, 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate_per_hour, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(final_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
