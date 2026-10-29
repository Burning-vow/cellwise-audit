import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    lam_base = 6.0
    mu_base = 10.0
    c = 1
    K = 4
    
    if args.pert == 'lam_up': lam_base *= 1.2
    elif args.pert == 'mu_up': mu_base *= 1.2
    elif args.pert == 'c_up': c += 1; K += 1
    
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start
    
    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    per_seed_arr = []
    per_seed_blk = []
    per_seed_dep = []
    per_seed_busy_util = []
    per_seed_occupied = []
    
    total_L_area = 0.0
    total_W_sum = 0.0
    total_busy_time = 0.0
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_wait_count = 0
    total_min_N_c = 0.0
    
    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        
        events = []
        def push(t, typ, data=None):
            events.append((t, typ, data))
            
        t_now = 0.0
        n_in_sys = 0
        busy_until = -1.0
        
        first_arr = rng.expovariate(lam_base)
        push(first_arr, 'arr')
        
        last_event_t = 0.0
        area_L = 0.0
        sum_W = 0.0
        count_dep = 0
        time_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_wait = 0
        min_N_c_integral = 0.0
        
        while events:
            events.sort(key=lambda x: x[0])
            t, typ, data = events.pop(0)
            
            dt = t - last_event_t
            if dt > 0:
                if last_event_t < win_start and t >= win_start:
                    split_dt_win = win_start - last_event_t
                    split_dt_rest = t - win_start
                    if split_dt_win > 0:
                        pass 
                    if split_dt_rest > 0:
                        area_L += n_in_sys * split_dt_rest
                        if n_in_sys > 0:
                            time_busy += split_dt_rest
                        min_N_c_integral += min(n_in_sys, c) * split_dt_rest
                elif last_event_t >= win_start:
                    area_L += n_in_sys * dt
                    if n_in_sys > 0:
                        time_busy += dt
                    min_N_c_integral += min(n_in_sys, c) * dt
                elif t <= win_start:
                    pass
            
            last_event_t = t
            
            if typ == 'arr':
                count_arr += 1
                service_time = rng.expovariate(mu_base)
                
                if n_in_sys < K:
                    n_in_sys += 1
                    wait_start = t
                    if n_in_sys == 1:
                        start_serv = t
                        end_serv = t + service_time
                        push(end_serv, 'dep', {'start': start_serv, 'wait_start': wait_start})
                    else:
                        start_serv = max(t, busy_until)
                        end_serv = start_serv + service_time
                        push(end_serv, 'dep', {'start': start_serv, 'wait_start': wait_start})
                        if start_serv > t:
                            count_wait += 1
                    busy_until = end_serv
                else:
                    count_blk += 1
                
                next_arr = t + rng.expovariate(lam_base)
                push(next_arr, 'arr')
                
            elif typ == 'dep':
                d_data = data
                n_in_sys -= 1
                count_dep += 1
                w_val = d_data['start'] - d_data['wait_start']
                sum_W += w_val
                if w_val > 0:
                    pass 
                
                if n_in_sys > 0:
                    pass 

        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = sum_W / count_dep if count_dep > 0 else 0.0
        bf_est = time_busy / win_len if win_len > 0 else 0.0
        pl_est = count_blk / count_arr if count_arr > 0 else 0.0
        pw_est = count_wait / count_arr if count_arr > 0 else 0.0
        bu_est = min_N_c_integral / (win_len * c) if win_len > 0 and c > 0 else 0.0
        occ_est = bf_est
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        per_seed_arr.append(count_arr)
        per_seed_blk.append(count_blk)
        per_seed_dep.append(count_dep)
        per_seed_busy_util.append(bu_est)
        per_seed_occupied.append(occ_est)
        
        total_L_area += area_L
        total_W_sum += sum_W
        total_busy_time += time_busy
        total_arr += count_arr
        total_blk += count_blk
        total_dep += count_dep
        total_wait_count += count_wait
        total_min_N_c += min_N_c_integral

    avg_L = total_L_area / (win_len * seeds_used) if win_len > 0 and seeds_used > 0 else 0.0
    avg_W = total_W_sum / total_dep if total_dep > 0 else 0.0
    avg_bf = total_busy_time / (win_len * seeds_used) if win_len > 0 and seeds_used > 0 else 0.0
    avg_pl = total_blk / total_arr if total_arr > 0 else 0.0
    avg_pw = total_wait_count / total_arr if total_arr > 0 else 0.0
    avg_bu = total_min_N_c / (win_len * c * seeds_used) if win_len > 0 and c > 0 and seeds_used > 0 else 0.0
    avg_occ = avg_bf
    
    arr_avg = total_arr / seeds_used if seeds_used > 0 else 0.0
    blk_avg = total_blk / seeds_used if seeds_used > 0 else 0.0
    dep_avg = total_dep / seeds_used if seeds_used > 0 else 0.0
    dep_rate = dep_avg / win_len * 60.0 if win_len > 0 else 0.0
    lam_eff = dep_rate
    
    res = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_loss": round(avg_pl, 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "minute",
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
