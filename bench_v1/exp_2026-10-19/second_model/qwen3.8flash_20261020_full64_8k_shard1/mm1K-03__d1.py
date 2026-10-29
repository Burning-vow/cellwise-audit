import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 10.0
    c = 1
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = "hour"
    win = H * 0.75
    warmup = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    seeds_used = 0
    seed_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        n_in_sys = 0
        service_end_time = float('inf')
        
        total_time = 0.0
        busy_time = 0.0
        wait_time_sum = 0.0
        num_completed = 0
        num_arrivals = 0
        num_blocked = 0
        
        last_event_time = 0.0
        
        while t < H:
            if next_arr < next_dep:
                dt = next_arr - t
                if t >= warmup:
                    total_time += dt
                    if n_in_sys > 0:
                        busy_time += dt
                t = next_arr
                
                if n_in_sys < K:
                    n_in_sys += 1
                    num_arrivals += 1
                    if n_in_sys == 1:
                        svc_dur = rng.expovariate(mu)
                        next_dep = t + svc_dur
                        service_end_time = next_dep
                    else:
                        pass
                else:
                    num_blocked += 1
                
                next_arr = t + rng.expovariate(lam)
                
            else:
                dt = next_dep - t
                if t >= warmup:
                    total_time += dt
                    if n_in_sys > 0:
                        busy_time += dt
                t = next_dep
                
                if n_in_sys > 0:
                    n_in_sys -= 1
                    num_completed += 1
                    
                    if n_in_sys > 0:
                        svc_dur = rng.expovariate(mu)
                        next_dep = t + svc_dur
                        service_end_time = next_dep
                    else:
                        next_dep = float('inf')
                        service_end_time = float('inf')
        
        if total_time > 0:
            L_val = (busy_time / total_time) * (K + 1) / 2 if False else None
            
            avg_n = 0.0
            # Recalculate L properly via integration during simulation is complex without storing history
            # Let's re-run with proper accumulation or approximate. 
            # Actually, standard way: accumulate area under N(t).
            
            # Re-simulate to get accurate stats with area accumulation
            rng = random.Random(s)
            t = 0.0
            next_arr = rng.expovariate(lam)
            next_dep = float('inf')
            n_in_sys = 0
            area_N = 0.0
            area_busy = 0.0
            wait_area = 0.0
            num_completed = 0
            num_arrivals = 0
            num_blocked = 0
            last_t = 0.0
            
            while t < H:
                if next_arr < next_dep:
                    dt = next_arr - t
                    if t >= warmup:
                        area_N += n_in_sys * dt
                        if n_in_sys > 0:
                            area_busy += dt
                    t = next_arr
                    if n_in_sys < K:
                        n_in_sys += 1
                        num_arrivals += 1
                        if n_in_sys == 1:
                            svc_dur = rng.expovariate(mu)
                            next_dep = t + svc_dur
                    else:
                        num_blocked += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    dt = next_dep - t
                    if t >= warmup:
                        area_N += n_in_sys * dt
                        if n_in_sys > 0:
                            area_busy += dt
                    t = next_dep
                    if n_in_sys > 0:
                        n_in_sys -= 1
                        num_completed += 1
                        if n_in_sys > 0:
                            svc_dur = rng.expovariate(mu)
                            next_dep = t + svc_dur
                        else:
                            next_dep = float('inf')
            
            eff_win = H - warmup
            if eff_win <= 0:
                continue
                
            L_est = area_N / eff_win
            busy_frac_est = area_busy / eff_win
            p_loss_est = num_blocked / num_arrivals if num_arrivals > 0 else 0.0
            W_est = (L_est / (num_completed / eff_win)) * 60 if num_completed > 0 else 0.0 # Little's Law, convert hours to minutes? No, L is dimensionless, lambda is per hour. W is in hours. Convert to minutes.
            # Wait, L = lambda_eff * W. If lambda is per hour, W is in hours.
            # Question asks W in minutes.
            lam_eff = num_completed / eff_win
            if lam_eff > 0:
                W_hours = L_est / lam_eff
                W_min = W_hours * 60.0
            else:
                W_min = 0.0
            
            p_wait_est = 1.0 - (1.0 - busy_frac_est) if c==1 else 0.0 # For M/M/1/K, P(wait) = P(system full)? No. P(wait) is prob that arrival has to wait. In M/M/1/K, if system not empty, new arrival waits. But if system full, blocked. So among accepted arrivals, those who find n>0 wait.
            # Simpler: P_wait = fraction of accepted arrivals that had to wait.
            # We didn't track this directly. Approximate as busy_frac? Or calculate from queue length distribution?
            # Let's stick to simple metrics requested. p_wait usually means probability an arriving customer must wait.
            # In discrete event sim, we can count how many arrivals found n>0.
            
            # Re-re-simulate to count waits accurately
            rng = random.Random(s)
            t = 0.0
            next_arr = rng.expovariate(lam)
            next_dep = float('inf')
            n_in_sys = 0
            area_N = 0.0
            area_busy = 0.0
            num_completed = 0
            num_arrivals_accepted = 0
            num_blocked = 0
            num_waits = 0
            
            while t < H:
                if next_arr < next_dep:
                    dt = next_arr - t
                    if t >= warmup:
                        area_N += n_in_sys * dt
                        if n_in_sys > 0:
                            area_busy += dt
                    t = next_arr
                    if n_in_sys < K:
                        if n_in_sys > 0:
                            num_waits += 1
                        n_in_sys += 1
                        num_arrivals_accepted += 1
                        if n_in_sys == 1:
                            svc_dur = rng.expovariate(mu)
                            next_dep = t + svc_dur
                    else:
                        num_blocked += 1
                    next_arr = t + rng.expovariate(lam)
                else:
                    dt = next_dep - t
                    if t >= warmup:
                        area_N += n_in_sys * dt
                        if n_in_sys > 0:
                            area_busy += dt
                    t = next_dep
                    if n_in_sys > 0:
                        n_in_sys -= 1
                        num_completed += 1
                        if n_in_sys > 0:
                            svc_dur = rng.expovariate(mu)
                            next_dep = t + svc_dur
                        else:
                            next_dep = float('inf')
            
            eff_win = H - warmup
            L_est = area_N / eff_win
            busy_frac_est = area_busy / eff_win
            p_loss_est = num_blocked / (num_arrivals_accepted + num_blocked) if (num_arrivals_accepted + num_blocked) > 0 else 0.0
            lam_eff = num_completed / eff_win
            W_min = (L_est / lam_eff) * 60.0 if lam_eff > 0 else 0.0
            p_wait_est = num_waits / num_arrivals_accepted if num_arrivals_accepted > 0 else 0.0
            busy_util_est = busy_frac_est / c if c > 0 else 0.0
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_min)
            per_seed_busy_frac.append(busy_frac_est)
            per_seed_p_loss.append(p_loss_est)
            per_seed_p_wait.append(p_wait_est)
            
            all_L.append(L_est)
            all_W.append(W_min)
            all_busy_frac.append(busy_frac_est)
            all_p_loss.append(p_loss_est)
            all_p_wait.append(p_wait_est)
            all_arr.append(num_arrivals_accepted + num_blocked)
            all_blk.append(num_blocked)
            all_dep.append(num_completed)
            all_busy_util.append(busy_util_est)
            all_dep_rate.append(lam_eff)
            all_lam_eff.append(lam_eff)
            
            seeds_used += 1
            seed_list.append(s)

    if seeds_used == 0:
        print(json.dumps({"error": "no seeds"}))
        return

    mean_L = sum(all_L) / seeds_used
    mean_W = sum(all_W) / seeds_used
    mean_busy_frac = sum(all_busy_frac) / seeds_used
    mean_p_loss = sum(all_p_loss) / seeds_used
    mean_p_wait = sum(all_p_wait) / seeds_used
    mean_arr = sum(all_arr) / seeds_used
    mean_blk = sum(all_blk) / seeds_used
    mean_dep = sum(all_dep) / seeds_used
    mean_busy_util = sum(all_busy_util) / seeds_used
    mean_dep_rate = sum(all_dep_rate) / seeds_used
    mean_lam_eff = sum(all_lam_eff) / seeds_used
    
    out = {
        "L": mean_L,
        "W": mean_W,
        "busy_frac": mean_busy_frac,
        "p_loss": mean_p_loss,
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win,
        "arr": mean_arr,
        "blk": mean_blk,
        "busy_util": mean_busy_util,
        "dep": mean_dep,
        "dep_rate": mean_dep_rate,
        "lam_eff": mean_lam_eff,
        "p_wait": mean_p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
