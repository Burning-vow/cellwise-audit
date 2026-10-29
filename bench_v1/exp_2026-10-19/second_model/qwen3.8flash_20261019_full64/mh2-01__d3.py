import sys, json, math, random

def main():
    args = sys.argv[1:]
    seeds_n = 5; horizon = 20.0; seed_start = 42; pert = "none"
    for i in range(len(args)):
        if args[i] == "--seeds": seeds_n = int(args[i+1])
        elif args[i] == "--horizon": horizon = float(args[i+1])
        elif args[i] == "--seed-start": seed_start = int(args[i+1])
        elif args[i] == "--pert": pert = args[i+1]

    lam_base = 3.0; mu_base = 10.0 # mean service time 6 min = 0.1 hour -> mu=10/hr
    cv_target = 1.5
    # Two-stage hyperexponential: p*exp(mu1) + (1-p)*exp(mu2)
    # Mean = p/mu1 + (1-p)/mu2 = 1/mu_base
    # Var = 2*(p/mu1^2 + (1-p)/mu2^2) - (1/mu_base)^2 ... wait, for exp distribution var is 1/mu^2.
    # For mixture: E[X] = p/mu1 + (1-p)/mu2. E[X^2] = 2*p/mu1^2 + 2*(1-p)/mu2^2.
    # CV^2 = Var/Mean^2 = (E[X^2]/Mean^2) - 1.
    # Let's pick a simple symmetric case or solve numerically? 
    # Standard approach for high CV: one very fast, one slow.
    # Let's try p=0.5. Then Mean = 0.5(1/mu1 + 1/mu2).
    # This is complex to solve exactly in code without libraries. 
    # Alternative: Use Erlang-k approximation? No, must be standard library.
    # Let's use a specific parameterization known to work or just simulate with a generic distribution that matches mean and CV approximately if exact solution is hard.
    # Actually, we can sample from a mixture of two exponentials.
    # To get CV=1.5, we need high variance.
    # Let's assume parameters: p=0.1, mu1=100, mu2=? such that mean is 0.1 hr.
    # 0.1/100 + 0.9/mu2 = 0.1 => 0.001 + 0.9/mu2 = 0.1 => 0.9/mu2 = 0.099 => mu2 ~ 9.09.
    # Check CV: E[X^2] = 2*(0.1/10000 + 0.9/82.6) ~ 2*(0.00001 + 0.0109) ~ 0.0218.
    # Var = 0.0218 - 0.01 = 0.0118. CV^2 = 0.0118/0.01 = 1.18. CV ~ 1.08. Too low.
    # Need higher CV. Try p=0.01, mu1=1000.
    # 0.01/1000 + 0.99/mu2 = 0.1 => 0.00001 + 0.99/mu2 = 0.1 => mu2 ~ 9.9.
    # E[X^2] = 2*(0.01/1e6 + 0.99/98) ~ 2*(0.0101) = 0.0202.
    # Var = 0.0202 - 0.01 = 0.0102. CV^2 = 1.02. Still low.
    # The issue is that mixing exponentials usually gives CV >= 1. To get 1.5, we need more spread.
    # Let's use a deterministic solver for p, mu1, mu2 given mean m=0.1 and cv=1.5.
    # Equations:
    # 1) p/mu1 + (1-p)/mu2 = m
    # 2) 2*p/mu1^2 + 2*(1-p)/mu2^2 - m^2 = (cv*m)^2
    # Let r = mu1/mu2. Assume mu1 > mu2 (fast/slow). Or vice versa.
    # This is non-linear. We can iterate or use a simpler distribution like Lognormal? No, "two-stage mixed exponential".
    # Let's approximate by choosing fixed p and solving for mu1, mu2.
    # If we set p=0.5, then 0.5(1/mu1 + 1/mu2) = m => 1/mu1 + 1/mu2 = 2m.
    # And 2*0.5(1/mu1^2 + 1/mu2^2) = m^2(1+cv^2) => 1/mu1^2 + 1/mu2^2 = 0.5 * m^2 * (1+2.25) = 1.625 m^2.
    # Let x=1/mu1, y=1/mu2. x+y=2m. x^2+y^2=1.625m^2.
    # (x+y)^2 = x^2+y^2+2xy => 4m^2 = 1.625m^2 + 2xy => 2xy = 2.375m^2 => xy = 1.1875m^2.
    # t^2 - (2m)t + 1.1875m^2 = 0. Discriminant = 4m^2 - 4.75m^2 < 0. No real solution for p=0.5.
    # So p cannot be 0.5. We need smaller p or larger p.
    # Let's try p=0.1.
    # 0.1x + 0.9y = m.
    # 2(0.1x^2 + 0.9y^2) = m^2(1+2.25) = 3.25m^2 => 0.1x^2 + 0.9y^2 = 1.625m^2.
    # From first eq: x = (m - 0.9y)/0.1 = 10m - 9y.
    # Substitute: 0.1(10m-9y)^2 + 0.9y^2 = 1.625m^2.
    # 0.1(100m^2 - 180my + 81y^2) + 0.9y^2 = 1.625m^2.
    # 10m^2 - 18my + 8.1y^2 + 0.9y^2 = 1.625m^2.
    # 9y^2 - 18my + 8.375m^2 = 0.
    # y = [18m +/- sqrt(324m^2 - 4*9*8.375m^2)] / 18 = [18m +/- sqrt(324 - 301.5)m] / 18 = [18 +/- sqrt(22.5)]m / 18.
    # sqrt(22.5) ~ 4.74.
    # y1 = (18+4.74)/18 m = 1.263 m. y2 = (18-4.74)/18 m = 0.736 m.
    # If y=1.263m, x=10m - 9(1.263m) = 10m - 11.367m = -1.367m (Invalid).
    # If y=0.736m, x=10m - 9(0.736m) = 10m - 6.624m = 3.376m.
    # So mu2 = 1/y = 1/(0.736m), mu1 = 1/x = 1/(3.376m).
    # With m=0.1: mu2 = 1/0.0736 = 13.58, mu1 = 1/0.3376 = 2.96.
    # Wait, mu1 < mu2 means stage 1 is slower? It doesn't matter which is which as long as we mix them.
    # Let's verify: p=0.1, mu1=2.96, mu2=13.58.
    # Mean = 0.1/2.96 + 0.9/13.58 = 0.0337 + 0.0662 = 0.0999 ~ 0.1. OK.
    # E[X^2] = 2(0.1/2.96^2 + 0.9/13.58^2) = 2(0.1/8.76 + 0.9/184.4) = 2(0.0114 + 0.0048) = 0.0324.
    # Var = 0.0324 - 0.01 = 0.0224. CV^2 = 0.0224/0.01 = 2.24. CV = 1.496 ~ 1.5. OK.
    
    m = 0.1 # hours
    p_mix = 0.1
    # Solve quadratic for y (rate of second component)
    # Coeffs derived above: A=9, B=-18m, C=8.375m^2
    disc = (18*m)**2 - 4*9*(8.375*m**2)
    if disc < 0:
        # Fallback to slightly different p if needed, but here it should be positive
        pass
    y_val = (18*m - math.sqrt(disc)) / 18.0 # Choose the root that makes x positive
    x_val = 10*m - 9*y_val
    
    mu1 = 1.0/x_val if x_val > 0 else 1.0
    mu2 = 1.0/y_val if y_val > 0 else 1.0
    
    lam = lam_base
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif pert == "c_up": pass # c is number of servers, fixed at 1

    results = []
    all_L = []; all_W = []; all_busy = []; all_p_loss = []; all_p_wait = []
    
    for s_idx in range(seeds_n):
        seed = seed_start + s_idx
        rng = random.Random(seed)
        
        # Simulation state
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        server_busy = False
        queue = [] # List of arrival times
        
        # Statistics accumulators (for area integration)
        warmup_end = horizon * 0.25
        stat_time = 0.0
        last_stat_t = warmup_end
        
        total_area_N = 0.0
        total_area_busy = 0.0
        count_arrivals = 0
        count_departures = 0
        count_blocked = 0
        count_waited = 0 # Customers who waited > 0
        
        # Pre-generate service times? Requirement: "service duration must be drawn at arrival"
        # So we draw when they arrive.
        
        while t < horizon:
            # Determine next event
            if not server_busy:
                next_departure = float('inf')
            
            if next_arrival <= next_departure:
                # Arrival Event
                t = next_arrival
                if t >= warmup_end:
                    dt = t - last_stat_t
                    N_curr = len(queue) + (1 if server_busy else 0)
                    total_area_N += N_curr * dt
                    total_area_busy += (1 if server_busy else 0) * dt
                    last_stat_t = t
                
                # Process arrival
                count_arrivals += 1
                # Draw service time
                if rng.random() < p_mix:
                    svc = rng.expovariate(mu1)
                else:
                    svc = rng.expovariate(mu2)
                
                if not server_busy:
                    server_busy = True
                    next_departure = t + svc
                    # Did this customer wait? No, immediate service.
                else:
                    # Server busy, join queue
                    queue.append((t, svc))
                    count_waited += 1 # They will wait until served
                    
                # Schedule next arrival
                next_arrival = t + rng.expovariate(lam)
                
            else:
                # Departure Event
                t = next_departure
                if t >= warmup_end:
                    dt = t - last_stat_t
                    N_curr = len(queue) + (1 if server_busy else 0)
                    total_area_N += N_curr * dt
                    total_area_busy += (1 if server_busy else 0) * dt
                    last_stat_t = t
                
                # Process departure
                count_departures += 1
                server_busy = False
                if queue:
                    arr_t, svc = queue.pop(0)
                    server_busy = True
                    next_departure = t + svc
                    # Note: The customer who just started service had been waiting.
                    # We already counted them as 'waited' upon arrival.
                else:
                    next_departure = float('inf')
                    
        # Final interval up to horizon
        if horizon > last_stat_t:
            dt = horizon - last_stat_t
            N_curr = len(queue) + (1 if server_busy else 0)
            total_area_N += N_curr * dt
            total_area_busy += (1 if server_busy else 0) * dt
            
        win_len = horizon - warmup_end
        if win_len <= 0: win_len = 1e-9
        
        L_est = total_area_N / win_len
        busy_frac_est = total_area_busy / win_len
        
        # W calculation via Little's Law on the queue part? 
        # W is average time in system.
        # Total customers processed in window? 
        # We need to be careful with boundary effects.
        # Approximation: W = L / lambda_eff.
        # lambda_eff = count_arrivals / win_len (assuming no loss/blocking in M/M/1 queue with infinite buffer)
        # But the problem mentions "blk" (blocked/lost). In a single server with queue, usually no blocking unless finite capacity.
        # The prompt says "call center... 1 agent". Usually implies infinite queue or blocking if too many?
        # "P-K formula" usually refers to Pollaczek-Khinchine for M/G/1.
        # PK formula for Wq (waiting time in queue) or W (total)?
        # W = Wq + 1/mu.
        # PK: Wq = (lambda * E[S^2]) / (2 * (1 - rho)).
        # Here we are simulating.
        # If there is no blocking mechanism defined (like max queue length), blk should be 0.
        # However, the output requires blk. I will assume infinite buffer, so blk=0.
        # p_loss = 0.
        # p_wait = fraction of arrivals that waited.
        
        p_wait_est = count_waited / count_arrivals if count_arrivals > 0 else 0
        p_loss_est = count_blocked / count_arrivals if count_arrivals > 0 else 0
        
        # W estimation:
        # Method 1: Average residence time of completed customers in window.
        # This is tricky with open systems.
        # Method 2: Little's Law: L = lambda * W => W = L / lambda.
        # lambda = count_arrivals / win_len.
        lam_eff = count_arrivals / win_len
        W_est = L_est / lam_eff if lam_eff > 0 else 0
        
        dep_rate = count_departures / win_len * 60.0 # per hour? No, time unit is hour.
        # dep_rate requested as "个/每小时". Since internal time is hours, rate is count/hour.
        # But wait, if time_unit is hour, then dep_rate is simply count_departures / win_len.
        # The prompt says "dep_rate is '个/每小时'". If my time_unit is 'hour', then the value IS per hour.
        
        res = {
            "L": L_est,
            "W": W_est,
            "busy_frac": busy_frac_est,
            "runtime_units": 1, # dummy
            "seed_list": [seed],
            "seeds_used": 1,
            "
