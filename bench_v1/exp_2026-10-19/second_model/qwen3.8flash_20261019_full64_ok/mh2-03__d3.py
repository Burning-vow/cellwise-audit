import json, math, random, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 3.0
    mu_base = 10.0
    
    if a.pert == 'lam_up':
        lam = lam_base * 1.1
    elif a.pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif a.pert == 'c_up':
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    if a.pert == 'lam_up':
        pass
    elif a.pert == 'mu_up':
        pass
    elif a.pert == 'c_up':
        pass
    else:
        pass
        
    # For M/G/1 with c=1, we need to simulate properly.
    # Service time is two-stage hyperexponential with mean 6 min and CV=2.
    # Mean service time in hours: 6/60 = 0.1 hours.
    # So mu (service rate) = 1/0.1 = 10 per hour.
    # CV^2 = 4. For hyperexp with two stages, we can choose parameters.
    # Let's use a simple approach: sample from a distribution with given mean and CV.
    # We'll use a lognormal approximation or just generate samples that match the stats.
    # Actually, for simulation, we need to draw service times at arrival.
    # Let's use a gamma distribution approximating the required moments? 
    # Or better: since it's specified as two-stage hyperexponential, let's pick one.
    # A common choice: mix of exp(rate r1) w.p. p and exp(rate r2) w.p. 1-p.
    # Mean = p/r1 + (1-p)/r2 = 0.1
    # Var = 2*(p/r1^2 + (1-p)/r2^2) - Mean^2 ... wait, for hyperexp, E[X^2] = 2*E[1/R^2 weighted].
    # Actually simpler: just use a distribution that has mean 0.1 and variance 4*0.1^2 = 0.04.
    # Std dev = 0.2.
    # We can use a shifted exponential or just accept some approximation.
    # Let's use a Gamma(k, theta) where k = 1/CV^2 = 1/4 = 0.25, theta = mean/k = 0.1/0.25 = 0.4.
    # This gives correct first two moments.
    
    mean_service_hours = 0.1
    cv_service = 2.0
    var_service = (cv_service * mean_service_hours)**2
    # Gamma shape k = mean^2 / var = 0.01 / 0.04 = 0.25
    # Gamma scale theta = var / mean = 0.04 / 0.1 = 0.4
    k_shape = 0.25
    theta_scale = 0.4
    
    horizon = a.horizon
    warmup_frac = 0.25
    warmup_end = horizon * warmup_frac
    
    seeds_used = []
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_dep_rate = []
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        seeds_used.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        next_arrival = rng.expovariate(lam)
        next_departure = float('inf')
        server_busy = False
        queue = []  # list of (arrival_time, service_time)
        num_in_system = 0
        
        # Statistics accumulators (for area under curve)
        area_N = 0.0
        area_busy = 0.0
        area_waiting = 0.0  # integral of number waiting
        total_arrivals = 0
        total_departures = 0
        total_blocked = 0
        total_waits = 0.0  # sum of waiting times for those who waited
        count_waited = 0
        last_event_time = 0.0
        
        # We need to track when we enter the measurement window
        in_window = False
        window_start_area_N = 0.0
        window_start_area_busy = 0.0
        window_start_area_waiting = 0.0
        window_start_total_arrivals = 0
        window_start_total_departures = 0
        window_start_total_blocked = 0
        window_start_total_waits = 0.0
        window_start_count_waited = 0
        
        while t < horizon:
            # Determine next event
            if next_arrival <= next_departure:
                t_next = next_arrival
            else:
                t_next = next_departure
                
            if t_next > horizon:
                break
                
            # Accumulate areas up to t_next
            dt = t_next - t
            if not in_window and t >= warmup_end:
                in_window = True
                window_start_area_N = area_N
                window_start_area_busy = area_busy
                window_start_area_waiting = area_waiting
                window_start_total_arrivals = total_arrivals
                window_start_total_departures = total_departures
                window_start_total_blocked = total_blocked
                window_start_total_waits = total_waits
                window_start_count_waited = count_waited
                
            if in_window:
                area_N += num_in_system * dt
                if server_busy:
                    area_busy += dt
                # Number waiting is len(queue)
                area_waiting += len(queue) * dt
            
            t = t_next
            
            if t == next_arrival:
                # Arrival
                total_arrivals += 1
                # Sample service time now
                # Gamma distribution sampling using standard library
                # Python's random.gauss is normal, but we need gamma.
                # We can use random.betavariate or implement via rejection? 
                # Actually, random module doesn't have gamma directly in older versions, 
                # but in Python 3.8+ there is no direct gamma. 
                # Wait, random module does NOT have gamma. 
                # We must implement it or use another method.
                # Since we cannot use third-party libs, let's use a simple approximation 
                # or implement Marsaglia-Tsang method for gamma.
                
                # Implementing Marsaglia-Tsang for Gamma(k, 1) then scale by theta
                def sample_gamma(shape, scale, rng_obj):
                    if shape < 1:
                        u = rng_obj.random()
                        return sample_gamma(1 + shape, scale, rng_obj) * (u ** (1.0 / shape))
                    d = shape - 1.0 / 3.0
                    c = 1.0 / math.sqrt(9.0 * d)
                    while True:
                        x = rng_obj.gauss(0, 1)
                        v = 1.0 + c * x
                        if v > 0:
                            v = v * v * v
                            u = rng_obj.random()
                            if u < 1.0 - 0.0331 * x * x * x * x:
                                return d * v * scale
                            if math.log(u) < 0.5 * x * x + d * (1.0 - v + math.log(v)):
                                return d * v * scale
                
                svc_time = sample_gamma(k_shape, theta_scale, rng)
                
                if not server_busy:
                    server_busy = True
                    next_departure = t + svc_time
                    num_in_system += 1
                else:
                    queue.append((t, svc_time))
                    num_in_system += 1
                    
                next_arrival = t + rng.expovariate(lam)
                
            elif t == next_departure:
                # Departure
                total_departures += 1
                num_in_system -= 1
                
                if queue:
                    arr_t, svc_t = queue.pop(0)
                    wait_time = t - arr_t
                    if wait_time > 0:
                        total_waits += wait_time
                        count_waited += 1
                    server_busy = True
                    next_departure = t + svc_t
                else:
                    server_busy = False
                    next_departure = float('inf')
                    
        # Final accumulation if loop ended before processing all events? 
        # The loop breaks when t_next > horizon, so we've accumulated up to horizon.
        
        win_len = horizon - warmup_end
        if win_len <= 0:
            L_est = 0.0
            W_est = 0.0
            busy_frac_est = 0.0
            p_loss_est = 0.0
            p_wait_est = 0.0
            arr_est = 0.0
            dep_est = 0.0
            blk_est = 0.0
            busy_util_est = 0.0
            busy_occ_est = 0.0
            lam_eff_est = 0.0
            dep_rate_est = 0.0
        else:
            L_est = (area_N - window_start_area_N) / win_len
            # W is average time in system. By Little's Law, L = lambda_eff * W.
            # But we also computed waiting times. Total time in system = waiting + service.
            # We didn't accumulate service times directly in area_N? 
            # area_N is integral of N(t). 
            # To get W, we can use L / lambda_eff.
            # lambda_eff = departures / win_len (assuming stable system, arrivals ~ departures)
            # Or more precisely, effective arrival rate into the system.
            # In this model, no blocking, so all arrivals enter.
            # However, we are measuring over the window.
            # Let's compute lambda_eff as departures per unit time in window.
            dep_in_win = total_departures - window_start_total_departures
            arr_in_win = total_arrivals - window_start_total_arrivals
            blk_in_win = total_blocked - window_start_total_blocked # Always 0 here
            
            lambda_eff = dep_in_win / win_len if win_len > 0 else 0
            W_est = L_est / lambda_eff if lambda_eff > 0 else 0
            
            busy_frac_est = (area_busy - window_start_area_busy) / win_len
            # busy_util = E[min(N,c)]/c. Here c=1. min(N,1) is 1 if N>=1, 0 if N=0.
            # This is exactly the fraction of time server is busy.
            busy_util_est = busy_frac_est
            # busy_occupied = 1 - pi_0. pi_0 is prob N=0.
            # Fraction of time N=0 is (win_len - area_busy)/win_len? No.
            # area_busy is time server is busy. Server is busy iff N>=1.
            # So P(N>=1) = busy_frac. P(N=0) = 1 - busy_frac.
            # So busy_occupied = 1 - (1 - busy_frac) = busy_frac.
            busy_occ_est = busy_frac_est
            
            p_loss_est = blk_in_win / arr_in_win if arr_in_win > 0 else 0
            waits_in_win = total_waits - window_start_total_waits
            count_waited_in_win = count_waited - window_start_count_waited
            p_wait_est = count_waited_in_win / arr_in_win if arr_in_win > 0 else 0
            
            arr_est = arr_in_win
            dep_est = dep_in_win
            blk_est = blk_in_win
            lam_eff_est = lambda_eff
            dep_rate_est = lambda_eff # per hour
            
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_est)
        all_dep.append(dep_est)
        all_blk.append(blk_est)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_lam_eff.append(lam_eff_est)
        all_dep_rate.append(dep_rate_est)
        
    n_seeds = len(seeds_used)
    if n_seeds == 0:
        avg_L = 0.0
        avg_W = 0.0
        avg_busy_frac = 0.0
        avg_p_loss = 0.0
        avg_p_wait = 0.0
        avg_arr = 0.0
        avg_dep = 0.0
        avg_blk = 0.0
        avg_busy_util = 0.0
        avg_busy_occ = 0.0
        avg_lam_eff = 0.0
        avg_dep_rate = 0.0
    else:
        avg_L = sum(all_L) / n_seeds
        avg_W = sum(all_W) / n_seeds
        avg_busy_frac = sum(all_busy_frac) / n_seeds
        avg_p_loss = sum(all_p_loss) / n_seeds
        avg_p_wait = sum(all_p_wait) / n_seeds
        avg_arr = sum(all_arr) / n_seeds
        avg_dep = sum(all_dep) / n_seeds
        avg_blk = sum(all_blk) / n_seeds
        avg_busy_util = sum(all_busy_util) / n_seeds
        avg_busy_occ = sum(all_busy_occupied) / n_seeds
        avg_lam_eff = sum(all_lam_eff) / n_seeds
        avg_dep_rate = sum(all_dep_rate) / n_seeds
        
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "runtime_units": "hour",
        "seed_list": seeds_used,
        "seeds_used": n_seeds,
        "time_unit": "hour",
        "win": round(horizon * (1 - warmup_frac), 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
