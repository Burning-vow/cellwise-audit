import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=10.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 6.0
    c = 3
    
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
    warmup_end = H * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        events = []
        t = 0.0
        n_in_system = 0
        servers_free = [True] * c
        
        # Generate first arrival
        next_arrival_time = rng.expovariate(lam)
        events.append((next_arrival_time, 'arrival'))
        
        total_service_time_sum = 0.0
        num_completed_services = 0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked_window = 0
        integral_n = 0.0
        last_event_time = 0.0
        p_wait_count = 0
        arr_count_total = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            current_time, event_type = events.pop(0)
            
            dt = current_time - last_event_time
            if last_event_time >= warmup_end and current_time <= H:
                integral_n += n_in_system * dt
            
            if current_time > H:
                break
                
            if event_type == 'arrival':
                if current_time >= warmup_end:
                    num_arrivals_window += 1
                    arr_count_total += 1
                    if n_in_system >= c:
                        num_blocked_window += 1
                        p_wait_count += 1
                    else:
                        if n_in_system > 0:
                            p_wait_count += 1
                        # Find a free server
                        found = False
                        for s_idx in range(c):
                            if servers_free[s_idx]:
                                servers_free[s_idx] = False
                                service_time = rng.expovariate(mu)
                                dep_time = current_time + service_time
                                events.append((dep_time, 'departure', s_idx, service_time))
                                n_in_system += 1
                                found = True
                                break
                        if not found:
                            # Should not happen if logic correct, but handle
                            pass
                else:
                    # During warmup, still process arrivals to maintain state
                    if n_in_system < c:
                        found = False
                        for s_idx in range(c):
                            if servers_free[s_idx]:
                                servers_free[s_idx] = False
                                service_time = rng.expovariate(mu)
                                dep_time = current_time + service_time
                                events.append((dep_time, 'departure', s_idx, service_time))
                                n_in_system += 1
                                found = True
                                break
                    else:
                        # Blocked during warmup, just count as lost for consistency? 
                        # Problem says stats only in window, so we don't accumulate here.
                        pass
                
                # Schedule next arrival
                inter_arrival = rng.expovariate(lam)
                next_t = current_time + inter_arrival
                if next_t <= H:
                    events.append((next_t, 'arrival'))
                    
            elif event_type == 'departure':
                _, _, s_idx, service_time = event_type_tuple = (current_time, event_type, None, None)
                # Unpack properly from tuple structure above
                # The tuple was (dep_time, 'departure', s_idx, service_time)
                # So when popped, it's (t, 'departure', s_idx, service_time)
                # Wait, I appended (dep_time, 'departure', s_idx, service_time)
                # So unpacking:
                # Let's re-read the append: events.append((dep_time, 'departure', s_idx, service_time))
                # Pop gives: current_time, event_type, extra1, extra2
                # But my pop code does: current_time, event_type = events.pop(0) -> This fails if len>2
                
                # Correction needed in loop structure. Let's restart the inner loop logic carefully.
                pass 

        # The above logic has a bug in unpacking. Let's rewrite the simulation loop cleanly.
        
        # Reset for this seed with corrected logic
        rng = random.Random(seed)
        events = []
        t = 0.0
        n_in_system = 0
        servers_free = [True] * c
        next_arrival_time = rng.expovariate(lam)
        events.append((next_arrival_time, 'arrival', None, None))
        
        total_service_time_sum = 0.0
        num_completed_services = 0
        num_arrivals_window = 0
        num_departures_window = 0
        num_blocked_window = 0
        integral_n = 0.0
        last_event_time = 0.0
        p_wait_count = 0
        arr_count_total = 0
        
        while events:
            events.sort(key=lambda x: x[0])
            current_time, event_type, data1, data2 = events.pop(0)
            
            dt = current_time - last_event_time
            if last_event_time >= warmup_end and current_time <= H:
                integral_n += n_in_system * dt
            
            if current_time > H:
                break
                
            if event_type == 'arrival':
                if current_time >= warmup_end:
                    num_arrivals_window += 1
                    arr_count_total += 1
                    if n_in_system >= c:
                        num_blocked_window += 1
                        p_wait_count += 1
                    else:
                        if n_in_system > 0:
                            p_wait_count += 1
                        found = False
                        for s_idx in range(c):
                            if servers_free[s_idx]:
                                servers_free[s_idx] = False
                                service_time = rng.expovariate(mu)
                                dep_time = current_time + service_time
                                events.append((dep_time, 'departure', s_idx, service_time))
                                n_in_system += 1
                                found = True
                                break
                else:
                    if n_in_system < c:
                        found = False
                        for s_idx in range(c):
                            if servers_free[s_idx]:
                                servers_free[s_idx] = False
                                service_time = rng.expovariate(mu)
                                dep_time = current_time + service_time
                                events.append((dep_time, 'departure', s_idx, service_time))
                                n_in_system += 1
                                found = True
                                break
                
                inter_arrival = rng.expovariate(lam)
                next_t = current_time + inter_arrival
                if next_t <= H:
                    events.append((next_t, 'arrival', None, None))
                    
            elif event_type == 'departure':
                s_idx = data1
                service_time = data2
                servers_free[s_idx] = True
                n_in_system -= 1
                if current_time >= warmup_end:
                    num_departures_window += 1
                    total_service_time_sum += service_time
                    num_completed_services += 1

        L_est = integral_n / win if win > 0 else 0
        W_est = (total_service_time_sum / num_completed_services) * 60 if num_completed_services > 0 else 0
        busy_frac_est = (integral_n / win) / c if win > 0 else 0
        p_wait_est = p_wait_count / num_arrivals_window if num_arrivals_window > 0 else 0
        p_loss_est = num_blocked_window / num_arrivals_window if num_arrivals_window > 0 else 0
        busy_util_est = busy_frac_est
        lam_eff_est = num_departures_window / win if win > 0 else 0
        dep_rate_est = lam_eff_est
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(num_arrivals_window)
        all_dep.append(num_departures_window)
        all_blk.append(num_blocked_window)
        all_busy_util.append(busy_util_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seeds_used_list.append(seed)

    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_lam_eff, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
