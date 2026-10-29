import random, json, math, sys

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 10.0
    c = 2
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 3
    else:
        lam = lam_base
        mu = mu_base
    
    time_unit = "hour"
    warmup_frac = 0.25
    win_len = H * (1 - warmup_frac)
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        
        events = []
        t_now = 0.0
        n_in_sys = 0
        busy_servers = 0
        
        next_arrival_time = rng.expovariate(lam)
        events.append((next_arrival_time, 'arrival'))
        
        total_time_weighted_n = 0.0
        last_event_time = 0.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        service_sum = 0.0
        p_wait_count = 0
        p_wait_total = 0
        
        warmup_end = H * warmup_frac
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            t_next, etype = events.pop(0)
            
            if t_next > H:
                break
            
            dt = t_next - last_event_time
            if last_event_time >= warmup_end or t_next <= warmup_end:
                pass
            if last_event_time < warmup_end and t_next > warmup_end:
                dt_warm = warmup_end - last_event_time
                dt_stat = t_next - warmup_end
                total_time_weighted_n += n_in_sys * dt_stat
            elif last_event_time >= warmup_end:
                total_time_weighted_n += n_in_sys * dt
            last_event_time = t_next
            
            if etype == 'arrival':
                arr_count += 1
                if t_next >= warmup_end:
                    p_wait_total += 1
                    if n_in_sys >= c:
                        p_wait_count += 1
                
                if n_in_sys < c:
                    svc_time = rng.expovariate(mu)
                    dep_time = t_next + svc_time
                    events.append((dep_time, 'departure'))
                    n_in_sys += 1
                    busy_servers += 1
                    if t_next >= warmup_end:
                        wait_sum += 0.0
                        service_sum += svc_time
                else:
                    if n_in_sys >= c:
                        blk_count += 1
                        if t_next >= warmup_end:
                            pass
                    else:
                        pass
                    n_in_sys += 1
                    if t_next >= warmup_end:
                        wait_sum += 0.0
                        service_sum += 0.0
                
                next_arrival_time = t_next + rng.expovariate(lam)
                events.append((next_arrival_time, 'arrival'))
                
            elif etype == 'departure':
                dep_count += 1
                n_in_sys -= 1
                busy_servers -= 1
                
                if n_in_sys > 0 and busy_servers < c:
                    pass
                
                if t_next >= warmup_end:
                    pass
                    
        L_est = total_time_weighted_n / win_len if win_len > 0 else 0.0
        W_est = (wait_sum + service_sum) / dep_count if dep_count > 0 else 0.0
        busy_util_est = (total_time_weighted_n / win_len) / c if win_len > 0 else 0.0
        p_wait_est = p_wait_count / p_wait_total if p_wait_total > 0 else 0.0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
        dep_rate_est = dep_count / win_len if win_len > 0 else 0.0
        lam_eff_est = dep_count / win_len if win_len > 0 else 0.0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_util_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_blk.append(blk_count)
        all_dep.append(dep_count)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        all_p_loss.append(p_loss_est)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_util_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
    
    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0.0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0.0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0.0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": [seed_start + i for i in range(N_seeds)],
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
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
