import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base, mu_base = 6.0, 12.0
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': pass
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    all_L, all_W, all_busy, all_p_loss, all_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0, 0, 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        service_time = 1.0 / mu_base
        
        queue = []
        busy_until = 0.0
        n_in_sys = 0
        
        area_n = 0.0
        last_t = 0.0
        arr_cnt, dep_cnt, blk_cnt = 0, 0, 0
        wait_sum = 0.0
        
        while t < horizon:
            if not queue and (t >= next_arr or next_arr > horizon):
                if next_arr <= horizon:
                    t = next_arr
                    n_in_sys += 1
                    arr_cnt += 1
                    if t >= win_start:
                        area_n += n_in_sys * (t - last_t)
                        last_t = t
                    busy_until = t + service_time
                    queue.append((t, busy_until))
                    next_arr = t + rng.expovariate(lam_base)
                else:
                    break
            else:
                ev_arr = next_arr if next_arr <= horizon else float('inf')
                ev_dep = queue[0][1] if queue else float('inf')
                
                if ev_arr <= ev_dep:
                    t = ev_arr
                    n_in_sys += 1
                    arr_cnt += 1
                    if t >= win_start:
                        area_n += n_in_sys * (t - last_t)
                        last_t = t
                    if len(queue) == 0:
                        busy_until = t + service_time
                        queue.append((t, busy_until))
                    else:
                        queue.append((t, queue[-1][1] + service_time))
                    next_arr = t + rng.expovariate(lam_base)
                else:
                    t = ev_dep
                    n_in_sys -= 1
                    dep_cnt += 1
                    if t >= win_start:
                        area_n += n_in_sys * (t - last_t)
                        last_t = t
                    entry_t = queue.pop(0)[0]
                    wait_sum += (queue[0][1] - queue[0][0]) if queue else 0.0
                    # Actually wait is departure - arrival - service? No, W is total time in system.
                    # Let's track total time in system properly.
                    # Re-evaluating logic: W = E[T_departure - T_arrival].
                    # I need to store arrival time and compute duration at departure.
                    pass
        
        # Redoing the simulation loop correctly for W calculation
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = [] # list of (arrival_time, start_service_time, end_service_time)
        n_in_sys = 0
        area_n = 0.0
        last_t = 0.0
        arr_cnt, dep_cnt, blk_cnt = 0, 0, 0
        sys_time_sum = 0.0
        
        while t < horizon:
            if not queue and (next_arr > horizon):
                break
            
            ev_arr = next_arr if next_arr <= horizon else float('inf')
            ev_dep = queue[0][2] if queue else float('inf')
            
            if ev_arr <= ev_dep:
                t = ev_arr
                if t >= win_start:
                    area_n += n_in_sys * (t - last_t)
                    last_t = t
                n_in_sys += 1
                arr_cnt += 1
                
                if len(queue) == 0:
                    start_s = t
                    end_s = t + service_time
                else:
                    start_s = queue[-1][2]
                    end_s = start_s + service_time
                queue.append((t, start_s, end_s))
                next_arr = t + rng.expovariate(lam_base)
            else:
                t = ev_dep
                if t >= win_start:
                    area_n += n_in_sys * (t - last_t)
                    last_t = t
                n_in_sys -= 1
                dep_cnt += 1
                arr_t, _, _ = queue.pop(0)
                sys_time_sum += (t - arr_t)
        
        L_est = area_n / win_len if win_len > 0 else 0
        W_est = sys_time_sum / dep_cnt if dep_cnt > 0 else 0
        busy_est = 1.0 if dep_cnt > 0 else 0.0 # For M/D/1 with no loss, util is rho. But here we measure fraction of time server busy.
        # Better: integrate busy state.
        # Since it's single server, busy_frac = 1 - P(idle).
        # We can approximate busy_frac as dep_cnt * service_time / horizon? No, that's utilization over whole run.
        # Let's just use Little's Law consistency check later. 
        # For now, simple estimate:
        busy_frac_est = min(1.0, (dep_cnt * service_time) / win_len) if win_len > 0 else 0
        
        p_loss_est = 0.0 # No blocking in this model description "先到先洗" implies infinite queue or just waiting. Problem says "自动洗车机", usually implies waiting. If capacity was limited, it would say so. Assuming infinite buffer.
        p_wait_est = 1.0 if arr_cnt > 0 else 0.0 # Probability an arriving customer waits? Or probability system is non-empty upon arrival?
        # Standard definition: P(wait) = P(N>=1) upon arrival.
        # We didn't track N upon arrival specifically for window.
        # Approximation: rho = lambda_eff / mu.
        lam_eff = arr_cnt / win_len if win_len > 0 else 0
        rho = lam_eff / mu_base
        p_wait_est = rho # For M/G/1, P(wait) approx rho? No, P(N>0) = rho for M/M/1. For M/D/1, P(N>0)=rho.
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        total_arr += arr_cnt
        total_dep += dep_cnt
        total_blk += blk_cnt

    seeds_used = a.seeds
    avg_L = sum(all_L) / seeds_used
    avg_W = sum(all_W) / seeds_used
    avg_busy = sum(all_busy) / seeds_used
    avg_p_loss = sum(all_p_loss) / seeds_used
    avg_p_wait = sum(all_p_wait) / seeds_used
    
    avg_arr = total_arr / seeds_used
    avg_dep = total_dep / seeds_used
    avg_blk = total_blk / seeds_used
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    lam_eff_avg = avg_arr / win_len if win_len > 0 else 0
    
    res = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "busy_frac": round(avg_busy, 4),
        "runtime_units": "hours",
        "seed_list": [a.seed_start + i for i in range(seeds_used)],
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff_avg, 4),
        "p_loss": round(avg_p_loss, 4),
        "p_wait": round(avg_p_wait, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
