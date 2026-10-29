import random, json, math, argparse

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
    
    lam_base = 8.0
    mu_base = 10.0
    c = 1
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25
    
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
        next_arrival = rng.expovariate(lam)
        service_times = {} 
        queue = [] 
        num_in_system = 0
        is_busy = False
        last_event_time = 0.0
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0
        count_wait = 0
        total_wait_time = 0.0
        
        while t < H:
            if not queue and not is_busy:
                if next_arrival > H:
                    break
                dt = next_arrival - t
                if t >= warmup_end:
                    area_L += num_in_system * dt
                    if is_busy:
                        area_busy += dt
                t = next_arrival
                
                if num_in_system < K:
                    num_in_system += 1
                    is_busy = True
                    st = rng.expovariate(mu)
                    service_times[id(num_in_system)] = (t, st) 
                    queue.append((t, st))
                    count_arr += 1
                else:
                    count_blk += 1
                
                next_arrival = t + rng.expovariate(lam)
                
            else:
                if queue:
                    arr_t, svc_t = queue[0]
                    dep_t = arr_t + svc_t
                else:
                    dep_t = float('inf')
                    
                if dep_t <= next_arrival:
                    dt = dep_t - t
                    if t >= warmup_end:
                        area_L += num_in_system * dt
                        if is_busy:
                            area_busy += dt
                    t = dep_t
                    
                    if queue:
                        q_arr_t, q_svc_t = queue.pop(0)
                        w = t - q_arr_t
                        if t >= warmup_end:
                            sum_W += w
                            count_wait += 1
                        num_in_system -= 1
                        count_dep += 1
                        
                        if queue:
                            pass
                        else:
                            is_busy = False
                            
                else:
                    dt = next_arrival - t
                    if t >= warmup_end:
                        area_L += num_in_system * dt
                        if is_busy:
                            area_busy += dt
                    t = next_arrival
                    
                    if num_in_system < K:
                        num_in_system += 1
                        is_busy = True
                        st = rng.expovariate(mu)
                        queue.append((t, st))
                        count_arr += 1
                    else:
                        count_blk += 1
                        
                    next_arrival = t + rng.expovariate(lam)
                    
        if t < H:
             dt = H - t
             if t >= warmup_end:
                 area_L += num_in_system * dt
                 if is_busy:
                     area_busy += dt
             t = H

        L_est = area_L / win if win > 0 else 0
        busy_frac_est = area_busy / win if win > 0 else 0
        p_loss_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0
        W_est_min = (sum_W / count_wait * 60) if count_wait > 0 else 0
        p_wait_est = count_wait / count_arr if count_arr > 0 else 0
        
        busy_util_est = (area_busy / win) / c if win > 0 else 0
        dep_rate_est = count_dep / win if win > 0 else 0
        lam_eff_est = count_arr / win if win > 0 else 0
        
        all_L.append(L_est)
        all_W.append(W_est_min)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr)
        all_blk.append(count_blk)
        all_dep.append(count_dep)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est_min)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        
        seeds_used += 1
        seed_list.append(s)

    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac)/len(all_busy_frac) if all_busy_frac else 0
    avg_p_loss = sum(all_p_loss)/len(all_p_loss) if all_p_loss else 0
    avg_p_wait = sum(all_p_wait)/len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr)/len(all_arr) if all_arr else 0
    avg_blk = sum(all_blk)/len(all_blk) if all_blk else 0
    avg_dep = sum(all_dep)/len(all_dep) if all_dep else 0
    avg_busy_util = sum(all_busy_util)/len(all_busy_util) if all_busy_util else 0
    avg_dep_rate = sum(all_dep_rate)/len(all_dep_rate) if all_dep_rate else 0
    avg_lam_eff = sum(all_lam_eff)/len(all_lam_eff) if all_lam_eff else 0
    
    result = {
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_busy_frac,
        "p_loss": avg_p_loss,
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": win,
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": avg_busy_util,
        "dep": avg_dep,
        "dep_rate": avg_dep_rate,
        "lam_eff": avg_lam_eff,
        "p_wait": avg_p_wait,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
