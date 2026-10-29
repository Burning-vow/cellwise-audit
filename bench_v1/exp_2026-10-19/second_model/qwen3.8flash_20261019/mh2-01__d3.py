import json, math, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 3.0
    mu_base = 10.0
    c_base = 1
    
    if args.pert == 'lam_up': lam_base *= 1.1
    elif args.pert == 'mu_up': mu_base *= 1.1
    elif args.pert == 'c_up': c_base += 1
    
    horizon = args.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    win_len = horizon - warmup_end
    
    seeds_used = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_lost_time = 0.0 # Not strictly needed for L/W but good for checks if needed
    
    for i in range(args.seeds):
        seed_val = args.seed_start + i
        rng = random.Random(seed_val)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = [] # List of tuples: (arrival_time, service_duration)
        server_free_at = 0.0
        is_server_busy = False
        
        # State variables for integration
        last_event_time = 0.0
        current_N = 0 # Number in system (waiting + serving)
        current_busy = 0 # 1 if server busy, 0 otherwise
        
        # Accumulators for this seed within the window [warmup_end, horizon]
        seed_area_N = 0.0
        seed_area_busy = 0.0
        seed_count_arr = 0
        seed_count_dep = 0
        seed_count_blk = 0
        seed_sum_W = 0.0 # Sum of sojourn times for completed customers in window? 
                         # Wait, W is average time in system. Usually calculated as Total Time In System / Total Departures.
                         # But we need to handle customers present at end of window.
                         # Standard DE approach: Integrate N(t) over window to get L.
                         # For W: Little's Law L = lambda_eff * W. Or sum of sojourn times of those who departed in window?
                         # The prompt asks for "Average processing duration W".
                         # Let's accumulate sojourn time for each departure that happens in the window.
                         # And also account for partial time for those still in system?
                         # Usually, for steady state estimates, we use L and effective arrival rate.
                         # However, direct measurement of W is often sum(sojourn)/count(departed).
                         # Let's stick to integrating N for L, and calculating W via Little's law or direct sum.
                         # Given the request for per_seed_W, let's calculate it as (Total Sojourn Time of Departed in Window) / (Count Departed in Window).
                         # If count is 0, W is undefined/0.
                         
        seed_total_sojourn_departed = 0.0
        
        while t < horizon:
            # Determine next event time
            arr_t = next_arr if next_arr <= horizon else float('inf')
            dep_t = float('inf')
            if is_server_busy:
                # We don't know exact dep time until we pop from queue? 
                # No, we schedule events.
                pass
            
            # Better approach: Event-driven with priority queue or simple simulation loop
            # Since single server, we can just track next_arrival and next_departure.
            
            # Recalculate next_departure based on current state
            # If server is busy, when does it finish?
            # We need to store the completion time of the current service.
            
            # Let's refactor the loop structure slightly for clarity in code generation.
            # Variables:
            # t: current time
            # next_arr: time of next arrival
            # next_dep: time of next departure (if any)
            # queue: list of (arrival_time, service_duration) waiting
            # current_service_end: time when current service ends
            
            # Initialize for first iteration logic inside loop is tricky.
            # Let's use a standard event loop.
            
            # Reset for new seed logic flow
            pass 

        # Re-implementing the inner loop properly
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        server_status = 0 # 0 idle, 1 busy
        current_service_end = 0.0
        
        last_integ_t = 0.0
        curr_N = 0
        curr_busy = 0
        
        s_area_N = 0.0
        s_area_busy = 0.0
        s_arr = 0
        s_dep = 0
        s_blk = 0
        s_sojourn_sum = 0.0
        
        while t < horizon:
            # Calculate next event time
            cand_arr = next_arr
            cand_dep = current_service_end if server_status == 1 else float('inf')
            
            next_t = min(cand_arr, cand_dep)
            
            if next_t > horizon:
                break
                
            # Integrate area up to next_t
            dt = next_t - last_integ_t
            if last_integ_t >= warmup_end:
                # Only integrate if the interval overlaps with the window
                # Actually, simpler: check if last_integ_t is in window or next_t is in window
                # But since we step through events, we can just add dt * value if the segment is in window.
                # To be precise:
                start_seg = max(last_integ_t, warmup_end)
                end_seg = min(next_t, horizon)
                if start_seg < end_seg:
                    seg_len = end_seg - start_seg
                    s_area_N += curr_N * seg_len
                    s_area_busy += curr_busy * seg_len
            
            t = next_t
            
            # Process Event
            if abs(t - cand_arr) < 1e-9:
                # Arrival
                if last_integ_t >= warmup_end or t >= warmup_end: # Count arrivals in window
                    if t >= warmup_end:
                        s_arr += 1
                
                # Generate service time now
                # Two-stage hyperexponential with mean 6 min (0.1 hr), CV 1.5
                # Mean m = 0.1. Var = (CV*m)^2 = (1.5*0.1)^2 = 0.0225.
                # H2: p1*lambda1 + p2*lambda2 = 1/mu_mean? No, mean = p1/mu1 + p2/mu2.
                # Let's use a simple approximation or exact H2 fit.
                # Common H2 fit for CV>1:
                # Let alpha = 1/CV^2. Here alpha = 1/2.25 = 0.444.
                # This is complex to derive inline.
                # Alternative: Use Gamma distribution? Prompt says "Two-stage mixed exponential".
                # Let's implement a generic H2 sampler.
                # Parameters for H2 with mean M and CV C:
                # Let k = sqrt(C^2 - 1) ... wait, for H2, CV >= 1/sqrt(2)? No, H2 can do any CV >= 1?
                # Actually, Erlang has CV < 1. Exponential CV=1. H2 allows CV > 1.
                # Formula:
                # Let p = 0.5. Let mu1, mu2 such that...
                # Simpler: Use a known parameterization.
                # Let r = sqrt(CV^2 - 1). If CV=1, r=0.
                # Here CV=1.5, r=sqrt(1.25)=1.118.
                # Let lambda1 = 1/(M*(1+r)), lambda2 = 1/(M*(1-r))? No, denominators must be positive.
                # Standard H2:
                # Choose p such that...
                # Let's use a simpler method: Sample from Exp(mean=M) if CV=1.
                # For CV=1.5, we can mix two exponentials.
                # Let's pick weights w1, w2 and rates mu1, mu2.
                # Mean = w1/mu1 + w2/mu2 = M
                # E[X^2] = 2*w1/mu1^2 + 2*w2/mu2^2 = M^2 * (1+CV^2)
                # Let w1=w2=0.5.
                # 0.5/mu1 + 0.5/mu2 = M => 1/mu1 + 1/mu2 = 2M
                # 1/mu1^2 + 1/mu2^2 = 2*M^2*(1+CV^2)
                # Let x=1/mu1, y=1/mu2.
                # x+y = 2M
                # x^2+y^2 = 2*M^2*(1+CV^2)
                # (x+y)^2 = x^2+y^2+2xy => 4M^2 = 2M^2(1+CV^2) + 2xy
                # xy = (4M^2 - 2M^2 - 2M^2*CV^2)/2 = M^2(1-CV^2)
                # If CV > 1, xy is negative -> impossible for real positive rates.
                # So equal weights don't work for CV > 1.
                
                # Try different weights.
                # Let's use a pre-calculated set or a robust sampler.
                # For CV=1.5, Mean=0.1hr.
                # Let's try: p=0.1, mu1=1/(0.1*0.5)=20? No.
                # Let's use the formula:
                # Let z = sqrt(CV^2 - 1).
                # mu1 = 1/(M*(1+z)), mu2 = 1/(M*(1-z)) -- fails if z>=1.
                # Here z = sqrt(1.25) ~ 1.118 > 1.
                
                # Correct H2 parameterization for CV > 1:
                # Let p = 0.5.
                # Let lambda1 = 1/(M * (1 + sqrt(CV^2-1))) ? No.
                
                # Let's just use a Gamma distribution approximation? No, prompt specifies H2.
                # Let's find valid parameters.
                # We need x,y > 0.
                # x+y = 2M/p?
                # Let's fix p=0.2.
                # Mean = 0.2*x + 0.8*y = M
                # E[X^2] = 2*0.2*x^2 + 2*0.8*y^2 = M^2(1+CV^2)
                # This is getting too long for inline calculation.
                
                # Simplification: The prompt says "P-K formula gives W and L... independent of specific two-stage distribution".
                # It implies we can simulate ANY distribution with correct Mean and CV.
                # I will use a Lognormal or Gamma? No, "Mixed Exponential".
                # I'll use a hardcoded H2 approximation that works for CV=1.5.
                # One common choice:
                # Let alpha = 1/CV^2 = 1/2.25 = 0.444.
                # This is for Coxian?
                
                # Let's use a simple trick: Mix Exp(M/2) and Exp(M/2) doesn't change CV.
                # Mix Exp(M*k) and Exp(M/k) with weights?
                
                # Okay, I will generate a service time using a Gamma distribution with shape k=1/CV^2 and scale theta=M*CV^2?
                # Gamma CV = 1/sqrt(k). So k = 1/CV^2 = 1/2.25 = 0.444.
                # Mean = k*theta = M => theta = M/k = 0.1/0.444 = 0.225.
                # Is Gamma a "two-stage mixed exponential"? Technically no, but it matches Mean and CV.
                # The prompt says "as long as mean and CV are fixed... P-K formula...".
                # It might accept Gamma as a proxy for the "random model" description if strict H2 sampling is too verbose.
                # BUT, "service duration must be drawn...".
                # Let's try to implement a basic H2 sampler.
                # For CV=1.5, M=0.1.
                # Let p=0.1.
                # Solve for mu1, mu2.
                # 0.1/mu1 + 0.9/mu2 = 0.1
                # 0.1/mu1^2 + 0.9/mu2^2 = 0.1^2 * (1+1.5^2) = 0.01 * 3.25 = 0.0325
                
                # Let u=1/mu1, v=1/mu2.
                # 0.1u + 0.9v = 0.1 => u + 9v = 1 => u = 1-9v
                # 0.1u^2 + 0.9v^2 = 0.0325
                # 0.1(1-9v)^2 + 0.9v^2 = 0.0325
                # 0.1(1 - 18v + 81v^2) + 0.9v^2 = 0.0325
                # 0.1 - 1.8v + 8.1v^2 + 0.9v^2 = 0.0325
                # 9v^2 - 1.8v + 0.0675 = 0
                # Divide by 9: v^2 - 0.2v + 0.0075 = 0
                # Roots: v = [0.2 +/- sqrt(0.04 - 0.03)] / 2 = [0.2 +/- 0.1] / 2
                # v1 = 0.15, v2 = 0.05
                # If v=0.15, u = 1 - 1.35 = -0.35 (Invalid)
                # If v=0.05, u = 1 - 0.45 = 0.55 (Valid)
                # So mu1 = 1/0.55 = 1.818, mu2 = 1/0.05 = 20.
                # Check: 0.1/1.818 + 0.9/20 = 0.055 + 0.045 = 0.1. OK.
                # Check Var: 2*0.1/1.818^2 + 2*0.9/20^2 = 0.2/3.305 + 1.8/400 = 0.0605 + 0.0045 = 0.065.
                # Target E[X^2] = 0.0325? Wait.
                # My equation was 0.1u^2 + 0.9v^2 = 0.0325.
                # 0.1(0.55^2) + 0.9(0.05^2) = 0.1(0.3025) + 0.9(0.0025) = 0.03025 + 0.00225 = 0.0325. OK.
                # So parameters: p=0.1, rate1=1.81818..., rate2=20.0.
                
                # Sampling:
                if rng.random() < 0.1:
                    serv_dur = rng.expovariate(1.8181818)
                else:
                    serv_dur = rng.expovariate(20.0)
                    
                # Add to queue or start service
                if server_status == 0:
                    server_status = 1
                    current_service_end = t + serv_dur
                    curr_N += 1
                    curr_busy = 1
                else:
                    queue.append((t, serv_dur))
                    curr_N += 1
                    # Check capacity? Single seat, infinite queue assumed unless blocked.
                    # "Blocked" usually means loss system. But "Call center" usually queues.
                    # Output requires "blk". If infinite queue, blk=0.
