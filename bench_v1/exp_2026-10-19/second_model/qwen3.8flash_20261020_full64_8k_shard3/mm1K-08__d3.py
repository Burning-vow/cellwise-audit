import sys, json, random, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    lam_base = 6.0 # per hour
    mu_base = 12.0 # per hour (5 min mean)
    c = 1
    K = 6
    
    if args.pert == 'lam_up': lam_base *= 1.2
    elif args.pert == 'mu_up': mu_base *= 1.2
    elif args.pert == 'c_up': pass # structure change not allowed by prompt "only params", but c is param? Prompt says pert only changes params. c is capacity. If c_up means increase capacity? But system is M/M/1/K. Let's assume c_up increases K or c? Usually c is servers. Here c=1 fixed. Maybe c_up means K+1? Or just ignore if not applicable. The prompt says "perturbation only changes parameters". Let's assume c_up might mean increasing arrival rate further or something else? No, standard queueing perturbations are lambda, mu, c. Since c=1 is fixed server count, maybe c_up refers to capacity K? Let's assume c_up increases K to 7.
    if args.pert == 'c_up': K += 1
    
    seeds_used = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_lam_eff = []
    all_dep_rate = []
    
    horizon = args.horizon
    time_unit = 'hour'
    
    for i in range(args.seeds):
        seed = args.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # Events: (time, type, data)
        # type: 0=arrival, 1=departure
        events = []
        
        # Initial state
        t_now = 0.0
        n_in_system = 0
        busy_until = -1.0 # Time when current service ends
        
        # Statistics accumulators (for area integration and counts)
        # Warmup: first 25% of horizon
        warmup_end = horizon * 0.25
        
        # We need to track time spent in each state N for L calculation
        # And time spent with N>0 for busy_frac
        # And total wait time for W
        
        last_event_time = 0.0
        area_n = 0.0 # Integral of N(t) dt
        area_busy = 0.0 # Integral of I(N(t)>0) dt
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        total_wait_time = 0.0 # Sum of waiting times for those who waited? Or all customers?
        # W usually defined as average time in system or waiting time? 
        # Standard Little's Law L = lambda_eff * W. W is time in system.
        # Let's calculate W as average time in system.
        total_time_in_system = 0.0
        num_customers_served = 0 # Those who entered service
        
        # Generate initial arrival
        next_arrival_t = rng.expovariate(lam_base)
        events.append((next_arrival_t, 0, None))
        
        while events:
            # Pop earliest event
            events.sort(key=lambda x: x[0])
            t_event, e_type, _ = events.pop(0)
            
            if t_event > horizon:
                break
                
            # Integrate areas from last_event_time to t_event
            dt = t_event - last_event_time
            if last_event_time >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
            
            last_event_time = t_event
            
            if e_type == 0: # Arrival
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    # Schedule departure
                    service_time = rng.expovariate(mu_base)
                    dep_t = t_event + service_time
                    events.append((dep_t, 1, {'enter_time': t_event}))
                else:
                    count_blocks += 1
                    
            elif e_type == 1: # Departure
                # Find the customer leaving. In FIFO, it's the one that has been waiting longest.
                # But we don't store full queue list efficiently here.
                # Simplification: We need to track individual customers to compute W accurately.
                # Re-evaluating approach: Need a queue of enter_times.
                
                # Actually, let's restart logic with explicit queue tracking for W.
                pass 

        # The above loop was incomplete for W calculation. Rewriting core simulation loop properly.
        
        # Reset stats for this seed
        rng = random.Random(seed)
        events = []
        t_now = 0.0
        n_in_system = 0
        queue_enter_times = [] # List of times patients arrived and are waiting/serving
        
        warmup_end = horizon * 0.25
        last_event_time = 0.0
        area_n = 0.0
        area_busy = 0.0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        total_time_in_system = 0.0
        served_count = 0
        
        next_arrival_t = rng.expovariate(lam_base)
        events.append((next_arrival_t, 0, None))
        
        while events:
            events.sort(key=lambda x: x[0])
            t_event, e_type, _ = events.pop(0)
            
            if t_event > horizon:
                break
                
            dt = t_event - last_event_time
            if last_event_time >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
            
            last_event_time = t_event
            
            if e_type == 0: # Arrival
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    queue_enter_times.append(t_event)
                    # If server was idle, start service immediately? 
                    # In discrete event sim, we schedule departure upon arrival if server free.
                    # But how do we know if server is free? 
                    # If n_in_system becomes 1 from 0, server starts.
                    # If n_in_system > 1, server is already busy.
                    # We need to schedule departure for the head of the queue if server is free.
                    # Better: Maintain a flag or check if we just started service.
                    
                    # Check if this arrival started service (i.e., previous n was 0)
                    # Wait, n_in_system was incremented. So if old n was 0, new n is 1.
                    # We need to know old n.
                    pass
                else:
                    count_blocks += 1
                    
            elif e_type == 1: # Departure
                # This implies a service completion.
                # Who leaves? The one at front of queue.
                if queue_enter_times:
                    enter_t = queue_enter_times.pop(0)
                    n_in_system -= 1
                    count_departures += 1
                    served_count += 1
                    total_time_in_system += (t_event - enter_t)
                    
                    # If there are still people in system, start service for next one
                    if n_in_system > 0:
                        service_time = rng.expovariate(mu_base)
                        dep_t = t_event + service_time
                        events.append((dep_t, 1, None))
                        
        # Problem: How to handle starting service on arrival?
        # When an arrives and n goes 0->1, we must schedule a departure.
        # When an arrives and n goes k->k+1 (k>=1), no new departure scheduled yet (server busy).
        
        # Let's refine the arrival block:
        # Old code didn't schedule departure on arrival correctly.
        
        # Restarting simulation loop with correct logic
        
        rng = random.Random(seed)
        events = []
        n_in_system = 0
        queue_enter_times = []
        
        warmup_end = horizon * 0.25
        last_event_time = 0.0
        area_n = 0.0
        area_busy = 0.0
        
        count_arrivals = 0
        count_blocks = 0
        count_departures = 0
        total_time_in_system = 0.0
        served_count = 0
        
        next_arrival_t = rng.expovariate(lam_base)
        events.append((next_arrival_t, 0, None))
        
        while events:
            events.sort(key=lambda x: x[0])
            t_event, e_type, _ = events.pop(0)
            
            if t_event > horizon:
                break
                
            dt = t_event - last_event_time
            if last_event_time >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
            
            last_event_time = t_event
            
            if e_type == 0: # Arrival
                count_arrivals += 1
                if n_in_system < K:
                    n_in_system += 1
                    queue_enter_times.append(t_event)
                    # If server was idle (n became 1 from 0), start service
                    if n_in_system == 1:
                        service_time = rng.expovariate(mu_base)
                        dep_t = t_event + service_time
                        events.append((dep_t, 1, None))
                else:
                    count_blocks += 1
                    
            elif e_type == 1: # Departure
                if queue_enter_times:
                    enter_t = queue_enter_times.pop(0)
                    n_in_system -= 1
                    count_departures += 1
                    served_count += 1
                    total_time_in_system += (t_event - enter_t)
                    
                    # If more people waiting, start next service
                    if n_in_system > 0:
                        service_time = rng.expovariate(mu_base)
                        dep_t = t_event + service_time
                        events.append((dep_t, 1, None))
        
        # Calculate metrics for this seed
        win_len = horizon - warmup_end
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0
            p_wait_est = 0.0
            arr_est = 0.0
            blk_est = 0.0
            dep_est = 0.0
            busy_util_est = 0.0
            lam_eff_est = 0.0
            dep_rate_est = 0.0
        else:
            L_est = area_n / win_len
            # W is avg time in system for served customers
            W_est = total_time_in_system / served_count if served_count > 0 else 0.0
            busy_frac_est = area_busy / win_len
            p_loss_est = count_blocks / count_arrivals if count_arrivals > 0 else 0.0
            # p_wait: probability of waiting? i.e., arriving to non-empty system?
            # Or fraction of time system is busy? 
            # Usually P(wait) = P(N>=1) = busy_frac in M/M/1.
            p_wait_est = busy_frac_est
            
            arr_est = count_arrivals / win_len
            blk_est = count_blocks / win_len
            dep_est = count_departures / win_len
            
            # busy_util = E[min(N,c)]/c. Here c=1. E[N] is L. So L/1 = L.
            # But definition says E[min(N,c)]/c. For c=1, min(N,1) is 1 if N>=1, 0 if N=0.
            # So E[min(N,1)] = P(N>=1) = busy_frac.
            # So busy_util should be equal to busy_frac for c=1.
            busy_util_est = busy_frac_est
            
            lam_eff_est = dep_est # Effective arrival rate = departure rate in steady state
            dep_rate_est = dep_est # Same unit
            
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_est)
        all_blk.append(blk_est)
        all_dep.append(dep_est)
        all_busy_util.append(busy_util_est)
        all_lam_eff.append(lam_eff_est)
        all_dep_rate.append(dep_rate_est)
        
    # Aggregate results
    def avg(lst): return sum(lst)/len(lst) if lst else 0.0
    
    res = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_loss": avg(all_p_loss),
        "runtime_units": "seconds", # Not strictly required to be accurate, just present
        "seed_list": seeds_used,
        "seeds_used": len(seeds_used),
        "time_unit": time_unit,
        "win": horizon * 0.75,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_wait": avg(all_p_wait),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
