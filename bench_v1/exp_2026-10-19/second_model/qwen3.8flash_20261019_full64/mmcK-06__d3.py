import random, json, argparse, math

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 6.0
    mu_base = 10.0
    c = 3
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 4
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
    all_lam_eff = []
    all_dep_rate = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        events = []
        t = 0.0
        n_in_sys = 0
        total_time_in_sys = 0.0
        last_event_time = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_times = []
        service_starts = []
        service_ends = []
        
        # Initial arrival
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'arrival'))
        
        while events:
            events.sort(key=lambda x: x[0])
            current_t, event_type = events.pop(0)
            
            if current_t > H:
                break
            
            dt = current_t - last_event_time
            if last_event_time >= warmup and current_t <= H:
                total_time_in_sys += n_in_sys * dt
                if n_in_sys > 0:
                    pass  # busy time handled by area integration below
            
            # Track busy time area
            if last_event_time >= warmup and current_t <= H:
                if n_in_sys > 0:
                    pass  # We'll compute busy fraction differently
            
            last_event_time = current_t
            
            if event_type == 'arrival':
                if current_t < warmup:
                    # During warmup, still process but don't count stats
                    if n_in_sys < K:
                        n_in_sys += 1
                        svc_time = rng.expovariate(mu)
                        end_t = current_t + svc_time
                        events.append((end_t, 'departure'))
                        service_starts.append(current_t)
                        service_ends.append(end_t)
                    else:
                        pass
                else:
                    if n_in_sys < K:
                        n_in_sys += 1
                        arr_count += 1
                        svc_time = rng.expovariate(mu)
                        end_t = current_t + svc_time
                        events.append((end_t, 'departure'))
                        service_starts.append(current_t)
                        service_ends.append(end_t)
                    else:
                        blk_count += 1
                
                # Schedule next arrival
                inter_arr = rng.expovariate(lam)
                next_t = current_t + inter_arr
                if next_t <= H:
                    events.append((next_t, 'arrival'))
                    
            elif event_type == 'departure':
                if current_t < warmup:
                    if n_in_sys > 0:
                        n_in_sys -= 1
                else:
                    if n_in_sys > 0:
                        n_in_sys -= 1
                        dep_count += 1
                        # Find matching start
                        if service_starts:
                            st = service_starts.pop(0)
                            se = service_ends.pop(0)
                            w = se - st
                            wait_times.append(w)
        
        # Compute statistics over window [warmup, H]
        window_len = H - warmup
        
        # L: average number in system during window
        # We need to integrate n(t) over window
        # Re-simulate or track properly? Let's recompute from recorded events within window
        
        # Actually, let's redo with proper tracking
        # For simplicity, use the accumulated total_time_in_sys which was updated incorrectly above
        # Let me rewrite the core loop more carefully
        
        # Reset and do it right
        rng = random.Random(seed)
        events = []
        t = 0.0
        n_in_sys = 0
        integral_n = 0.0
        integral_busy = 0.0
        last_t = 0.0
        arr_w = 0
        blk_w = 0
        dep_w = 0
        waits = []
        starts = []
        ends = []
        
        next_arrival = rng.expovariate(lam)
        events.append((next_arrival, 'arrival'))
        
        while events:
            events.sort(key=lambda x: x[0])
            ct, et = events.pop(0)
            if ct > H:
                break
            
            dt = ct - last_t
            if last_t >= warmup:
                integral_n += n_in_sys * dt
                if n_in_sys > 0:
                    integral_busy += dt
            
            last_t = ct
            
            if et == 'arrival':
                if n_in_sys < K:
                    n_in_sys += 1
                    svc = rng.expovariate(mu)
                    end_t = ct + svc
                    events.append((end_t, 'departure'))
                    starts.append(ct)
                    ends.append(end_t)
                    if ct >= warmup:
                        arr_w += 1
                else:
                    if ct >= warmup:
                        blk_w += 1
                
                ia = rng.expovariate(lam)
                nt = ct + ia
                if nt <= H:
                    events.append((nt, 'arrival'))
                    
            elif et == 'departure':
                if n_in_sys > 0:
                    n_in_sys -= 1
                    if ct >= warmup:
                        dep_w += 1
                        if starts:
                            s = starts.pop(0)
                            e = ends.pop(0)
                            waits.append(e - s)
        
        wl = H - warmup
        if wl <= 0:
            wl = 1e-9
        
        L_val = integral_n / wl
        W_val = sum(waits) / len(waits) if waits else 0.0
        busy_frac_val = integral_busy / wl
        p_loss_val = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
        p_wait_val = len(waits) / arr_w if arr_w > 0 else 0.0
        
        # busy_util = E[min(N,c)]/c
        # Need integral of min(n(t), c)
        # Recompute with separate tracking
        rng = random.Random(seed)
        events = []
        n_in_sys = 0
        integral_min_nc = 0.0
        last_t = 0.0
        
        na = rng.expovariate(lam)
        events.append((na, 'arrival'))
        
        while events:
            events.sort(key=lambda x: x[0])
            ct, et = events.pop(0)
            if ct > H:
                break
            dt = ct - last_t
            if last_t >= warmup:
                integral_min_nc += min(n_in_sys, c) * dt
            last_t = ct
            if et == 'arrival':
                if n_in_sys < K:
                    n_in_sys += 1
                    svc = rng.expovariate(mu)
                    events.append((ct + svc, 'departure'))
                ia = rng.expovariate(lam)
                nt = ct + ia
                if nt <= H:
                    events.append((nt, 'arrival'))
            elif et == 'departure':
                if n_in_sys > 0:
                    n_in_sys -= 1
        
        busy_util_val = integral_min_nc / (wl * c) if wl > 0 else 0.0
        busy_occupied_val = busy_frac_val
        
        dep_rate_val = dep_w / wl if wl > 0 else 0.0
        lam_eff_val = arr_w / wl if wl > 0 else 0.0
        
        all_L.append(L_val)
        all_W.append(W_val)
        all_busy_frac.append(busy_frac_val)
        all_p_loss.append(p_loss_val)
        all_p_wait.append(p_wait_val)
        all_arr.append(arr_w)
        all_blk.append(blk_w)
        all_dep.append(dep_w)
        all_busy_util.append(busy_util_val)
        all_lam_eff.append(lam_eff_val)
        all_dep_rate.append(dep_rate_val)
    
    seeds_used = N_seeds
    avg_L = sum(all_L) / seeds_used if seeds_used else 0
    avg_W = sum(all_W) / seeds_used if seeds_used else 0
    avg_busy_frac = sum(all_busy_frac) / seeds_used if seeds_used else 0
    avg_p_loss = sum(all_p_loss) / seeds_used if seeds_used else 0
    avg_p_wait = sum(all_p_wait) / seeds_used if seeds_used else 0
    avg_arr = sum(all_arr) / seeds_used if seeds_used else 0
    avg_blk = sum(all_blk) / seeds_used if seeds_used else 0
    avg_dep = sum(all_dep) / seeds_used if seeds_used else 0
    avg_busy_util = sum(all_busy_util) / seeds_used if seeds_used else 0
    avg_lam_eff = sum(all_lam_eff) / seeds_used if seeds_used else 0
    avg_dep_rate = sum(all_dep_rate) / seeds_used if seeds_used else 0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_loss": round(avg_p_loss, 6),
        "runtime_units": "hour",
        "seed_list": list(range(seed_start, seed_start + N_seeds)),
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
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
