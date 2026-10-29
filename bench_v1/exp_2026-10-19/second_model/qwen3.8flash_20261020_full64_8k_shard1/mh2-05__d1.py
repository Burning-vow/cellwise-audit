import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed-start
    pert = args.pert

    # Parameters in minutes
    lam_base = 3.0 / 60.0  # calls per minute
    mu_base = 1.0 / 6.0    # service rate per minute (mean 6 min)
    
    # Perturbations
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        # Not directly applicable to single server queue parameters unless we change distribution shape
        # But problem says "perturbation only changes parameters not structure". 
        # For M/G/1 with fixed mean and CV, changing c might imply changing the mix? 
        # However, P-K formula depends on rho and C_s^2. If we just scale mu or lambda, that's covered.
        # Let's assume c_up doesn't change lam/mu for this specific model interpretation or is ignored if no direct param.
        # Actually, usually c refers to number of servers, but here c=1 fixed. 
        # Let's stick to none/lam_up/mu_up as primary. c_up might be a distractor or implies changing variance?
        # The prompt says "two-stage mixed exponential... mean 6, CV 3". This defines the service time dist.
        # We will simulate using the defined mean and CV.
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    # Service Time Distribution: Two-stage Mixed Exponential
    # Mean E[S] = 6, Var(S) = (CV*E[S])^2 = (3*6)^2 = 324
    # A mixture of two exponentials with rates r1, r2 and weights p, 1-p.
    # E[S] = p/r1 + (1-p)/r2 = 6
    # E[S^2] = 2p/r1^2 + 2(1-p)/r2^2 = Var + Mean^2 = 324 + 36 = 360
    # We need to solve for p, r1, r2. There are infinite solutions. 
    # Standard approach: pick one component to be fast, one slow.
    # Let's try symmetric-ish or simple values. 
    # Actually, for simulation, we can just sample from a general distribution matching moments if we don't want to solve exactly.
    # But "two-stage mixed exponential" suggests a specific structure. 
    # Let's use a common parameterization: Phase-type approximation or just solve numerically?
    # Simpler: Use a Gamma distribution? No, must be mixed exp.
    # Let's fix r1 and r2 and solve for p? Or fix p?
    # Let's assume equal weights p=0.5 for simplicity if possible, or find valid params.
    # If p=0.5: 0.5/r1 + 0.5/r2 = 6 => 1/r1 + 1/r2 = 12
    # 2*(0.5/r1^2 + 0.5/r2^2) = 360 => 1/r1^2 + 1/r2^2 = 360
    # Let x=1/r1, y=1/r2. x+y=12, x^2+y^2=360.
    # (x+y)^2 = x^2+y^2+2xy => 144 = 360 + 2xy => 2xy = -216 => xy = -108. Impossible for positive rates.
    # So p != 0.5.
    # Let's try a different approach. Just generate samples from a distribution with given mean and CV.
    # Since exact mixed exp parameters are hard to derive uniquely without more constraints, and the problem states 
    # "P-K formula gives W and L regardless of which two-stage dist", we can approximate the service time sampling.
    # However, to be rigorous, let's pick a valid set.
    # Let r1 = 1/2 (mean 2), r2 = ?
    # p/0.5 + (1-p)/r2 = 6 => 2p + (1-p)/r2 = 6
    # 2p/0.25 + 2(1-p)/r2^2 = 360 => 8p + 2(1-p)/r2^2 = 360
    # From first: (1-p)/r2 = 6-2p => 1-p = r2(6-2p)
    # Substitute into second: 8p + 2*r2(6-2p)/r2^2 = 360 => 8p + 2(6-2p)/r2 = 360
    # 8p + (12-4p)/r2 = 360
    # Let's pick p=0.9. Then 7.2 + (12-3.6)/r2 = 360 => 7.2 + 8.4/r2 = 360 => 8.4/r2 = 352.8 => r2 = 8.4/352.8 ≈ 0.0238
    # Check mean: 0.9/0.5 + 0.1/0.0238 = 1.8 + 4.2 = 6. OK.
    # Check var: E[S^2] = 2*0.9/0.25 + 2*0.1/(0.0238^2) = 7.2 + 0.2/0.000566 = 7.2 + 353 = 360.2. Close enough.
    # Let's refine.
    # We'll define a function to sample service time.
    
    def sample_service_time(rng):
        # Using the derived parameters: p=0.9, r1=0.5, r2=0.0238
        # To be safer, let's use a generic method for mixed exponential if needed, 
        # but since we only need mean and CV for P-K, and we are simulating, we just need consistent sampling.
        # Let's use the calculated values.
        if rng.random() < 0.9:
            return rng.expovariate(0.5)
        else:
            return rng.expovariate(0.0238)

    results = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    
    warmup_ratio = 0.25
    win_len = H * (1 - warmup_ratio)
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        # Event simulation
        # State: next_arrival_time, next_departure_time, server_status (0=idle, 1=busy)
        # Queue: list of customers waiting
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        server_busy = False
        queue = []
        
        # Statistics accumulators for the window [H*warmup, H]
        # Area under curve for number in system (L)
        area_N = 0.0
        # Count of arrivals/departures/blocks in window
        cnt_arr_win = 0
        cnt_dep_win = 0
        cnt_blk_win = 0
        # Sum of sojourn times for completed services in window
        sum_sojaurn_win = 0.0
        # Number of completions in window
        cnt_comp_win = 0
        
        # Track last event time for integration
        last_t = 0.0
        current_N = 0 # Number in system (in service + waiting)
        
        # We need to integrate N over time.
        # Events: Arrival, Departure
        
        while t < H:
            # Determine next event
            if next_arr <= next_dep:
                # Arrival
                t_event = next_arr
                if t_event > H: break
                
                # Integrate area up to t_event
                dt = t_event - last_t
                area_N += current_N * dt
                last_t = t_event
                t = t_event
                
                # Process arrival
                if t >= H * warmup_ratio:
                    cnt_arr_win += 1
                
                # Check capacity? Problem doesn't specify finite buffer. Assume infinite queue.
                # "Blocked" usually means lost due to full buffer. If infinite, blk=0.
                # But output requires blk. Maybe there's a limit? 
                # "Customer service hotline... 1 agent". Usually implies infinite queue unless stated.
                # However, `blk` is requested. If infinite queue, blk should be 0.
                # Let's assume infinite queue for now. If blk>0 expected, maybe max queue length?
                # Prompt doesn't specify max queue. I will assume infinite, so blk=0.
                
                # Add to queue or start service
                if not server_busy:
                    server_busy = True
                    st = sample_service_time(rng)
                    next_dep = t + st
                    # Customer starts immediately, sojourn time will be st
                    # We need to track individual customer arrival time to compute sojourn
                    # Store (arrival_time, service_duration) in a variable for the one in service
                    cust_in_service = {'arr': t, 'dur': st}
                    current_N += 1
                else:
                    queue.append({'arr': t})
                    current_N += 1
                
                # Schedule next arrival
                next_arr = t + rng.expovariate(lam)
                
            else:
                # Departure
                t_event = next_dep
                if t_event > H: 
                    # Integrate remaining time to H
                    dt = H - last_t
                    area_N += current_N * dt
                    last_t = H
                    t = H
                    break
                
                dt = t_event - last_t
                area_N += current_N * dt
                last_t = t_event
                t = t_event
                
                # Process departure
                if t >= H * warmup_ratio:
                    cnt_dep_win += 1
                    
                # Calculate sojourn time for departing customer
                # Who departs? The one in service.
                # We stored cust_in_service when it started.
                # But wait, if queue was empty, we started service. If queue had people, we finished one and started next.
                # Logic: When departure happens, the person in service leaves.
                # Then check queue.
                
                # Retrieve info about the person leaving
                # We need to know their arrival time.
                # We stored cust_in_service['arr'] when they started service.
                # Is this correct? Yes, because they started service at some point.
                # Wait, if they waited in queue, their arrival time is earlier.
                # We need to store arrival time of the person currently in service.
                # When a new person enters service, we record their original arrival time.
                
                # Correction: In the arrival block, if server busy, we append to queue.
                # When server becomes free, we pop from queue and start service.
                # We need to handle the transition properly.
                
                # Let's restructure slightly.
                # Variable: `current_cust` holds dict with 'arr' (original arrival time) and 'start_serv' (time service began)
                # Actually, sojourn = depart_time - original_arrival_time.
                
                # In previous code:
                # If idle: cust_in_service = {'arr': t, 'dur': st}. Here arr is arrival time. Correct.
                # If busy: queue.append({'arr': t}).
                # On departure:
                #   Person leaves. Their arrival time is cust_in_service['arr'].
                #   Sojourn = t - cust_in_service['arr'].
                #   Then, if queue not empty:
                #       next_cust = queue.pop(0)
                #       st = sample_service_time(rng)
                #       cust_in_service = {'arr': next_cust['arr'], 'dur': st}
                #       next_dep = t + st
                #       server_busy remains True
                #       current_N decreases by 1 (one left) then increases by 0 (one moves from queue to service)?
                #       No, current_N counts total in system. One leaves, so N--.
                #       The one moving from queue to service is still in system. So N-- is correct.
                #   Else:
                #       server_busy = False
                #       next_dep = inf
                #       current_N -= 1
                
                # Need to ensure `cust_in_service` is initialized correctly.
                
                # Let's trace variables again.
                # Initialize: server_busy=False, queue=[], cust_in_service=None
                
                # Inside loop:
                # ...
                
                # Departure logic:
                if t >= H * warmup_ratio:
                    # Record sojourn for the one leaving
                    # cust_in_service must exist
                    sojaurn = t - cust_in_service['arr']
                    sum_sojaurn_win += sojaurn
                    cnt_comp_win += 1
                
                # Remove from system
                current_N -= 1
                
                # Start next if available
                if len(queue) > 0:
                    next_cust = queue.pop(0)
                    st = sample_service_time(rng)
                    cust_in_service = {'arr': next_cust['arr'], 'dur': st}
                    next_dep = t + st
                    # Server stays busy
                else:
                    server_busy = False
                    next_dep = float('inf')
                    cust_in_service = None

        # End of simulation for this seed
        
        # Calculate metrics for this seed
        if win_len > 0:
            L_seed = area_N / win_len
            if cnt_comp_win > 0:
                W_seed = sum_sojaurn_win / cnt_comp_win
            else:
                W_seed = 0.0
            
            # Busy fraction: E[min(N,1)] / 1. 
            # We integrated N. We need integral of min(N,1).
            # We didn't track that separately. 
            # Alternative: busy_util = fraction of time server was busy.
            # We can track time server was busy.
            pass
        
        # Re-run tracking for busy time? 
        # It's easier to track `time_busy` during the loop.
        
        # Let's refactor the loop to include time_busy accumulation.
        
        # Resetting for clarity in final code generation below.
        
        # Final aggregation
        results.append({
            'L': L_seed,
            'W': W_seed,
            'busy_frac': 0.0, # Placeholder
            'p_loss': 0.0,
            'p_wait': 0.0
        })

    # Since I cannot easily edit the thought process to rewrite the whole script perfectly in one go without running it,
    # I will write the clean version directly in the output block, ensuring all requirements are met.
    
    # Key fixes for the final code:
    # 1. Track `area_min_N` for busy_frac.
    # 2. Handle `blk` (assume 0 for infinite queue).
    # 3. Compute averages across seeds.
    # 4. JSON output format.

if __name__ == "__main__":
    # Actual implementation follows in the solution block
    pass
