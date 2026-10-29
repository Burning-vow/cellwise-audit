import sys, json, math, random
from collections import deque

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if i+1 < len(argv):
            args[argv[i].lstrip('-')] = argv[i+1]
    
    N = int(args.get('seeds', 10))
    H = float(args.get('horizon', 100.0)) # hours
    S = int(args.get('seed-start', 42))
    pert = args.get('pert', 'none')
    
    lam_base = 5.0 # per hour
    mu_base = 10.0 # per hour (6 min mean)
    cv_base = 2.0
    
    lam = lam_base
    mu = mu_base
    cv = cv_base
    
    if pert == 'lam_up': lam *= 1.1
    elif pert == 'mu_up': mu *= 1.1
    elif pert == 'c_up': pass # c is fixed at 1
    
    time_unit = "hour"
    horizon = H
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    
    seed_list = []
    
    for k in range(N):
        seed = S + k
        rng = random.Random(seed)
        
        # Two-stage hyperexponential parameters
        # Mean = p*1/mu1 + (1-p)*1/mu2 = 1/mu
        # Var = p*(2/mu1^2 - 2/mu1*mean + mean^2) ... simpler: E[X^2] = Var + Mean^2
        # For Hyperexp: E[X^2] = 2*p/mu1^2 + 2*(1-p)/mu2^2
        # CV^2 = (E[X^2] - Mean^2) / Mean^2 => E[X^2] = Mean^2 * (1 + CV^2)
        
        mean_service = 1.0 / mu
        var_service = (cv * mean_service)**2
        e_x2 = var_service + mean_service**2
        
        # Solve for mu1, mu2, p. Let's fix p=0.5 for simplicity or solve generally.
        # Standard approach: choose mu1 > mu > mu2. 
        # Let's use a simple parameterization: mu1 = alpha * mu, mu2 = beta * mu.
        # This might be complex to solve exactly for arbitrary CV with standard lib only without scipy.
        # Alternative: Use Erlang-k approximation? No, prompt says two-stage mixed exponential.
        # Let's pick specific values that satisfy the moments approximately or solve numerically.
        # Actually, for simulation, we just need to sample from it.
        # We can define the distribution by its CDF inverse or rejection sampling?
        # Simpler: Define mu1 and mu2 such that they match moments.
        # Let p = 0.5.
        # 0.5/mu1 + 0.5/mu2 = 1/mu
        # 0.5/mu1^2 + 0.5/mu2^2 = (1+CV^2)/(2*mu^2) ? No.
        # E[X^2] = 2 * (0.5/mu1^2 + 0.5/mu2^2) = 1/mu1^2 + 1/mu2^2
        # So: 1/mu1 + 1/mu2 = 2/mu
        #       1/mu1^2 + 1/mu2^2 = 2 * (1+CV^2) / mu^2
        
        # Let u = 1/mu1, v = 1/mu2.
        # u + v = 2/mu
        # u^2 + v^2 = 2(1+CV^2)/mu^2
        # (u+v)^2 = u^2 + v^2 + 2uv => 4/mu^2 = 2(1+CV^2)/mu^2 + 2uv
        # 2uv = 4/mu^2 - 2(1+CV^2)/mu^2 = (2 - 2CV^2)/mu^2
        # uv = (1-CV^2)/mu^2
        
        # If CV > 1, uv < 0, which implies one of u,v is negative? Impossible for rates.
        # Wait, variance of mixture: Var(X) = E[Var(X|stage)] + Var(E[X|stage])
        # The formula above assumes X is Exp(mu_i).
        # If CV > 1, we need high variability.
        # Let's check: if CV=2, CV^2=4. uv = (1-4)/mu^2 = -3/mu^2. Negative product means roots are real but signs differ?
        # Actually, for hyperexponential, we usually have distinct positive rates.
        # Maybe my moment matching equations are slightly off or I should allow different p.
        # Let's try a robust method: Sample from Exp(mu1) with prob p, Exp(mu2) with prob 1-p.
        # We need to find mu1, mu2, p.
        # Let's assume p=0.5 again.
        # If CV > 1, the system is unstable or requires very long tails.
        # Let's just implement a generic sampler for a given set of parameters derived from CV.
        # A common choice for CV>1 is to make one component very slow.
        # Let's solve for mu1, mu2 assuming p=0.5.
        # If discriminant is negative, adjust p.
        
        # Let's use a simpler approach: Generate service times using a Gamma distribution approximating the moments?
        # Prompt says "two-stage mixed exponential".
        # Let's calculate coefficients.
        # Let s1 = 1/mu1, s2 = 1/mu2.
        # s1+s2 = 2/mu
        # s1^2+s2^2 = 2(1+CV^2)/mu^2
        # Discriminant D = (s1-s2)^2 = 2(s1^2+s2^2) - (s1+s2)^2
        # D = 4(1+CV^2)/mu^2 - 4/mu^2 = 4*CV^2/mu^2
        # So |s1-s2| = 2*CV/mu
        # s1 = (2/mu + 2*CV/mu)/2 = (1+CV)/mu
        # s2 = (2/mu - 2*CV/mu)/2 = (1-CV)/mu
        
        # If CV > 1, s2 becomes negative. This implies the second rate mu2 is negative?
        # This happens because a mixture of two exponentials with equal weights cannot achieve CV > sqrt(2)?
        # Max CV for 2-stage hyperexp is actually unbounded if p approaches 0 or 1?
        # With p=0.5, max CV is limited.
        # To get CV=2, we need unequal probabilities.
        # Let's pick p such that we can have positive rates.
        # Let's try p=0.1.
        # Mean = 0.1/mu1 + 0.9/mu2 = 1/mu
        # E[X^2] = 2*(0.1/mu1^2 + 0.9/mu2^2) = (1+CV^2)/mu^2
        
        # This is getting complicated to solve analytically in code without libraries.
        # Alternative: Use a Phase-Type representation or just approximate with a single exponential if CV was 1, but CV=2.
        # Let's use a known trick: 
        # Choose mu1 = mu / (1 + CV) and mu2 = mu / (1 - CV) doesn't work for CV>1.
        # Let's choose mu1 = mu/2 and mu2 = mu/10?
        # Let's just simulate with a general sampler.
        # We will pre-calculate parameters for CV=2.
        # One valid solution for CV=2:
        # Let p = 0.5. Not possible as seen.
        # Let p = 0.2.
        # 0.2/mu1 + 0.8/mu2 = 1/mu
        # 0.2/mu1^2 + 0.8/mu2^2 = (1+4)/(2*mu^2) = 2.5/mu^2
        
        # Let x = mu/mu1, y = mu/mu2.
        # 0.2x + 0.8y = 1
        # 0.2x^2 + 0.8y^2 = 2.5
        
        # From first eq: x = (1 - 0.8y)/0.2 = 5 - 4y
        # Sub into second: 0.2(5-4y)^2 + 0.8y^2 = 2.5
        # 0.2(25 - 40y + 16y^2) + 0.8y^2 = 2.5
        # 5 - 8y + 3.2y^2 + 0.8y^2 = 2.5
        # 4y^2 - 8y + 2.5 = 0
        # y = (8 +/- sqrt(64 - 40))/8 = (8 +/- sqrt(24))/8 = 1 +/- sqrt(6)/4
        # sqrt(6) ~ 2.45.
        # y1 = 1 + 0.612 = 1.612 -> mu2 = mu/1.612
        # y2 = 1 - 0.612 = 0.388 -> mu2 = mu/0.388
        # Corresponding x:
        # If y=1.612, x = 5 - 4(1.612) = 5 - 6.448 = -1.448 (Invalid rate)
        # If y=0.388, x = 5 - 4(0.388) = 5 - 1.552 = 3.448 (Valid)
        
        # So we have a valid solution with p=0.2.
        # mu1 = mu / 3.448
        # mu2 = mu / 0.388
        
        # Let's hardcode these factors for CV=2.
        # Factor1 = 3.448, Factor2 = 0.388, Prob1 = 0.2
        
        f1 = 3.448
        f2 = 0.388
        p_stage1 = 0.2
        
        mu1 = mu / f1
        mu2 = mu / f2
        
        def sample_service():
            if rng.random() < p_stage1:
                return rng.expovariate(mu1)
            else:
                return rng.expovariate(mu2)
                
        # Simulation State
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        
        queue = deque() # waiting customers
        server_free_time = 0.0 # when current service ends
        
        # Statistics accumulators (for warmup removal)
        # Warmup: first 25% of horizon
        warmup_end = 0.25 * horizon
        
        # Area integrals
        area_N = 0.0
        last_t = 0.0
        current_N = 0 # number in system (in service + waiting)
        
        # Counts
        count_arr = 0
        count_dep = 0
        count_blk = 0 # Losses (if any, here infinite buffer so 0 losses unless specified? "blk" suggests blocking. M/M/1/K? Prompt says "call center", usually infinite buffer or finite. "p_loss" implies loss. But "queue" implies waiting. If capacity is not specified, assume infinite buffer => p_loss=0. However, output asks for blk. Let's assume infinite buffer, so blk=0.)
        # Wait, "blk" is defined as rejected/lost. In M/M/1, no loss. So blk=0.
        
        total_wait_time = 0.0 # Sum of waiting times for completed services
        
        # Event loop
        while t < horizon:
            # Determine next event time
            next_event = min(next_arrival, next_departure)
            
            if next_event > horizon:
                break
            
            dt = next_event - t
            if dt > 0:
                area_N += current_N * dt
                t = next_event
            
            # Process Arrival
            if abs(t - next_arrival) < 1e-9:
                count_arr += 1
                # Service time sampled now
                svc_time = sample_service()
                
                if current_N == 0:
                    # Start service immediately
                    current_N = 1
                    next_departure = t + svc_time
                    # Waiting time is 0
                else:
                    # Join queue
                    queue.append((t, svc_time))
                    current_N += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            # Process Departure
            elif abs(t - next_departure) < 1e-9:
                count_dep += 1
                current_N -= 1
                
                if queue:
                    arr_time, svc_time = queue.popleft()
                    wait_time = t - arr_time
                    total_wait_time += wait_time
                    current_N += 1 # Back to 1 (the new one starts service)
                    next_departure = t + svc_time
                else:
                    next_departure = float('inf')
            
            # Reset logic for warmup? 
            # We accumulate stats over whole run, then subtract warmup part?
            # Or reset accumulators at warmup_end?
            # Easier: Run full sim, store history? Too much memory.
            # Better: Check if t >= warmup_end. If so, start accumulating.
            # But we need to handle events crossing boundary.
            # Strategy: Accumulate everything, but also track state at warmup_end?
            # Simplest: Just ignore stats before warmup_end.
            # We need to know how many arrivals/departures happened BEFORE warmup_end to subtract them?
            # Or just reset counters when t crosses warmup_end.
            
            if t >= warmup_end and last_t < warmup_end:
                # Crossing boundary
                # Recalculate area_N contribution up to this point?
                # We integrated area_N continuously.
                # We need to subtract the area accumulated during warmup.
                # Let's keep separate accumulators for post-warmup.
                pass
            
            # Refactored accumulation:
            # We'll maintain `post_warmup` flags.
            
            # Update last_t
            last_t = t
            
        # End of simulation loop needs careful handling of final interval
        if t < horizon:
             dt = horizon - t
             area_N += current_N * dt
             t = horizon

        # Since I didn't implement the split accumulation inside the loop properly in the draft above,
        # let's rewrite the loop structure to support warmup exclusion cleanly.
        
        # RESTARTING LOGIC FOR CLEAN WARMUP HANDLING
        
        # Re-initialize for this seed
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        queue = deque()
        current_N = 0
        
        # Post-warmup accumulators
        pw_area_N = 0.0
        pw_count_arr = 0
        pw_count_dep = 0
        pw_total_wait = 0.0
        pw_last_t = 0.0
        pw_started = False
        
        # Pre-warmup accumulators (to discard)
        # Actually, we just don't add to PW until t >= warmup_end.
        
        while t < horizon:
            next_event = min(next_arrival, next_departure)
            if next_event > horizon:
                break
            
            dt = next_event - t
            if dt > 0:
                if t >= warmup_end:
                    pw_area_N += current_N * dt
                t = next_event
            
            # Handle Arrival
            if abs(t - next_arrival) < 1e-9:
                if t >= warmup_end:
                    pw_count_arr += 1
                
                svc_time = sample_service()
                
                if current_N == 0:
                    current_N = 1
                    next_departure = t + svc_time
                else:
                    queue.append((t, svc_time))
                    current_N += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            # Handle Departure
            elif abs(t - next_departure) < 1e-9:
                if t >= warmup_end:
                    pw_count_dep += 1
                
                current_N -= 1
                
                if queue:
                    arr_time, svc_time = queue.popleft()
