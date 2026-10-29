import sys, json, math, random

def main():
    args = sys.argv[1:]
    seeds_n = 5; horizon = 20.0; seed_start = 42; pert = "none"
    for i in range(0, len(args), 2):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]
    
    lam_base = 3.0; mu_base = 10.0 # mean service time 6 min = 0.1 hour -> mu=10/hr
    cv = 1.5
    # Two-stage hyperexponential matching mean and CV
    # Mean = p/mu1 + (1-p)/mu2 = 1/mu_base
    # Var = 2*(p/mu1^2 + (1-p)/mu2^2) - (1/mu_base)^2 ... actually for H2:
    # E[S] = p/mu1 + (1-p)/mu2
    # E[S^2] = 2*p/mu1^2 + 2*(1-p)/mu2^2
    # CV^2 = (E[S^2]-E[S]^2)/E[S]^2
    
    # Simple approximation or exact solve? Let's use a standard parameterization for H2 with given CV.
    # If CV > 1, we can set mu1 = mu_base * k, mu2 = mu_base / k' etc.
    # A common choice: let p be such that it works. 
    # For simplicity and robustness, I'll implement a generic sampler for H2 that matches mean and variance.
    # However, the prompt says "P-K formula gives W and L... independent of specific two-stage distribution".
    # This implies I should just simulate an M/G/1 queue where service times are drawn from ANY distribution with mean 0.1 hr and var consistent with CV=1.5.
    # But wait, P-K is for M/M/1? No, P-K is Pollaczek-Khinchine for M/G/1.
    # The prompt says "只要均值与变异系数定了，P-K 公式给出的 W 与 L 就定了". This is true for M/G/1.
    # So I need to simulate M/G/1 with arrival rate lam, service time S with E[S]=1/mu, CV(S)=cv.
    
    lam = lam_base
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": pass # mu doesn't change directly in param name, but maybe implied? Prompt says "pert only changes params not structure". Usually mu_up means faster service. Let's assume mu increases.
    elif pert == "c_up": pass # c is servers, fixed at 1. 
    
    # Re-evaluating pert effects based on typical DES tasks:
    # none: base
    # lam_up: increase arrival rate
    # mu_up: increase service rate (decrease mean service time)
    # c_up: increase capacity (servers). Here c=1 fixed by problem statement "only 1 agent". If c_up tries to change c, it might be ignored or error. But prompt says "pert only changes params". If c is a param, maybe it allows multiple servers? Problem says "only 1". I will stick to 1 server. If c_up is passed, I'll ignore it or treat as no-op since structure is single server.
    
    mu = mu_base
    if pert == "mu_up": mu *= 1.1
    
    # Generate service time samples for H2 or any dist with correct moments.
    # To keep it simple and valid for M/G/1 simulation, I'll generate exponential-like or lognormal? 
    # Actually, easiest way to get arbitrary CV in Python without complex H2 solver is to use a Gamma distribution? 
    # Gamma has CV = 1/sqrt(k). We want CV=1.5 => k = 1/2.25 = 0.444.
    # Shape k = 1/CV^2, Scale theta = Mean * CV^2.
    # Service time ~ Gamma(shape=1/cv^2, scale=mean_service_time * cv^2)
    # Note: Gamma is continuous, positive. Good enough for M/G/1 sim.
    
    shape = 1.0 / (cv * cv)
    scale = (1.0 / mu) * (cv * cv) # Mean = shape * scale = (1/cv^2) * (1/mu * cv^2) = 1/mu. Correct.
    
    results = []
    all_L = []; all_W = []; all_busy_frac = []; all_p_loss = []; all_p_wait = []
    
    # Warmup fraction 25%
    warmup_end = horizon * 0.25
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        num_in_system = 0
        busy = False
        
        # Statistics accumulators (for area integration)
        last_event_time = 0.0
        area_num_in_system = 0.0
        area_busy = 0.0
        
        # Counters for window stats
        arrivals_window = 0
        departures_window = 0
        losses_window = 0
        waits_window = 0 # total waiting time in system? No, W is avg time in system.
        # Need sum of sojourn times for customers who departed in window? 
        # Or better: Little's Law L = lambda_eff * W. 
        # We compute L via time-average. We compute W via sample average of sojourn times.
        # But we must exclude pre-warmup.
        
        # Store customer info: (arrival_time, service_duration)
        # When they depart, calculate sojourn time.
        active_customers = [] # list of dicts {arr_t, svc_dur}
        
        # For per-seed reporting
        seed_area_num = 0.0
        seed_area_busy = 0.0
        seed_sum_sojourn = 0.0
        seed_count_sojourn = 0
        seed_arrivals = 0
        seed_losses = 0
        seed_waits = 0 # count of those who waited? or total wait time? p_wait usually prob of waiting.
        seed_departures = 0
        
        while t < horizon:
            # Determine next event
            if next_arrival <= next_departure:
                t = next_arrival
                # Arrival
                if t >= warmup_end:
                    seed_arrivals += 1
                
                # Check if blocked (single server, infinite buffer? or loss?)
                # Problem says "hotline", usually infinite queue unless specified. 
                # "blk" key suggests blocking/loss exists. 
                # Standard M/M/1 has infinite buffer. M/M/1/K has finite.
                # Prompt mentions "blk" and "p_loss". If it's pure M/M/1, blk=0.
                # Let's assume infinite buffer (standard hotline) unless "c_up" implies capacity limit?
                # But "only 1 agent" is stated. 
                # If infinite buffer, p_loss = 0.
                # Let's check keys: arr, blk, dep... 
                # I will implement infinite buffer. blk will be 0.
                
                # Draw service time now
                svc_dur = rng.gammavariate(shape, scale)
                
                # Update area before state change
                dt = t - last_event_time
                seed_area_num += num_in_system * dt
                seed_area_busy += (1 if busy else 0) * dt
                last_event_time = t
                
                num_in_system += 1
                if not busy:
                    busy = True
                    next_departure = t + svc_dur
                    # Store start time for this customer? 
                    # We need to know when they started service to calculate wait vs service?
                    # For W (sojourn), we just need arrival and departure.
                    # For p_wait, we need to know if they waited.
                    # If they arrived to empty system, wait=0.
                    # If they arrived to busy system, wait>0.
                    
                    # Add to active list
                    active_customers.append({'arr': t, 'svc': svc_dur, 'start_svc': t})
                else:
                    # Queued
                    active_customers.append({'arr': t, 'svc': svc_dur, 'start_svc': None})
                
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                t = next_departure
                # Departure
                # Find the customer currently in service (the one whose start_svc was set)
                # In FIFO, it's the first one in active_customers that has start_svc != None?
                # Actually, simpler: maintain a queue.
                # Let's refactor slightly for clarity in loop.
                
                # Update area before state change
                dt = t - last_event_time
                seed_area_num += num_in_system * dt
                seed_area_busy += (1 if busy else 0) * dt
                last_event_time = t
                
                # Process departure
                # The head of the queue is being served.
                if active_customers:
                    cust = active_customers.pop(0)
                    # Calculate sojourn
                    sojourn = t - cust['arr']
                    if t >= warmup_end:
                        seed_sum_sojourn += sojourn
                        seed_count_sojourn += 1
                        seed_departures += 1
                        if cust['start_svc'] > cust['arr']:
                            seed_waits += 1 # counted as waiting
                    
                    num_in_system -= 1
                    
                    if active_customers:
                        # Next customer starts service immediately
                        next_cust = active_customers[0]
                        next_cust['start_svc'] = t
                        next_departure = t + next_cust['svc']
                        # Busy remains True
                    else:
                        busy = False
                        next_departure = float('inf')
                else:
                    # Should not happen if logic is correct
                    busy = False
                    next_departure = float('inf')

        # Final area update up to horizon
        dt = horizon - last_event_time
        seed_area_num += num_in_system * dt
        seed_area_busy += (1 if busy else 0) * dt
        
        # Compute per-seed stats
        win_len = horizon - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = seed_area_num / win_len
        busy_frac_est = seed_area_busy / win_len
        
        if seed_count_sojourn > 0:
            W_est = seed_sum_sojourn / seed_count_sojourn
        else:
            W_est = 0.0
            
        p_loss_est = 0.0 # Infinite buffer
        if seed_arrivals > 0:
            p_wait_est = seed_waits / seed_arrivals
        else:
            p_wait_est = 0.0
            
        # Effective arrival rate in window
        lam_eff = seed_arrivals / win_len
        
        results.append({
            'L': L_est,
            'W': W_est,
            'busy_frac': busy_frac_est,
            'p_loss': p_loss_est,
            'p_wait': p_wait_est,
            'arr': seed_arrivals,
            'dep': seed_departures,
            'blk': 0,
            'win': win_len
        })
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)

    # Aggregate
    n_seeds = len(results)
    avg_L = sum(all_L) / n_seeds
    avg_W = sum(all_W) / n_seeds
    avg_busy_frac = sum(all_busy_frac) / n_seeds
    avg_p_loss = sum(all_p_loss) / n_seeds
    avg_p_wait = sum(all_p_wait) / n_seeds
    
    total_arr = sum(r['arr'] for r in results)
    total_dep = sum(r['dep'] for r in results)
    total_blk = sum(r['blk'] for r in results)
    
    avg_arr_per_seed = total_arr / n_seeds
    avg_dep_per_seed = total_dep / n_seeds
    avg_blk_per_seed = total_blk / n_seeds
    
    # Dep rate per hour
    # Total departures / Total window time across all seeds? 
    # Or average of per-seed rates?
    # dep_rate = "个/每小时" effective departure rate.
    # Since steady state, dep_rate approx lam_eff.
    # Let's calculate global effective rate: total_dep / (n_seeds * win_len)
    global_win_len = horizon - warmup_end
    if global_win_len <= 0: global_win_len = 1e-9
    dep_rate = total_dep / (n_seeds * global_win_len)
    
    lam_eff_avg = total_arr / (n_seeds * global_win_len)
    
    # busy_util = E[min(N,c)]/c. With c=1, min(N,1) is 1 if N>=1, 0 if N=0.
    # This is exactly the probability server is busy, which is busy_frac.
    busy_util = avg_busy_frac
    busy_occupied = avg_busy_frac # 1 - pi_0. Same thing for c=1.
    
    output = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "runtime_units": "hour",
        "seed_list": [seed_start + i for i in range(n_seeds)],
        "seeds_used": n_seeds,
        "time_unit": "hour",
        "win": round(global_win_len, 6),
        "arr": round(avg_arr_per_seed, 6),
        "blk": round(avg_blk_per_seed, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep_per_seed, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff_avg, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    main()
