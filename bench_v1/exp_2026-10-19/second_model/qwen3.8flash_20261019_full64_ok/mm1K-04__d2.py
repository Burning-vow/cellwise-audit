import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=42)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert
    
    lam_base = 8.0
    mu_base = 60.0 / 5.0
    c = 1
    K = 4
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base
        mu = mu_base * 1.1
    elif pert == 'c_up':
        lam = lam_base
        mu = mu_base
        c = 2
        K = 5
    else:
        lam = lam_base
        mu = mu_base
        
    if pert != 'mu_up' and pert != 'c_up':
        mu = mu_base

    time_unit = "hour"
    
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
    used_seeds_list = []
    
    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = {} 
        queue = [] 
        num_in_system = 0
        busy_until = -1.0
        
        warmup_end = H * 0.25
        
        area_L = 0.0
        area_busy = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        sum_W = 0.0
        count_waited = 0
        
        last_event_time = 0.0
        
        while True:
            if next_arrival < (busy_until if num_in_system > 0 else float('inf')):
                event_time = next_arrival
                event_type = 'arrival'
            else:
                event_time = busy_until
                event_type = 'departure'
                
            if event_time > H:
                break
                
            dt = event_time - last_event_time
            
            if last_event_time >= warmup_end:
                area_L += num_in_system * dt
                if num_in_system > 0:
                    area_busy += dt
                    
            if event_type == 'arrival':
                if num_in_system < K:
                    num_in_system += 1
                    st = rng.expovariate(mu)
                    service_times[len(queue)] = st 
                    queue.append((event_time, st))
                    if num_in_system == 1:
                        busy_until = event_time + st
                    if last_event_time >= warmup_end:
                        count_arr += 1
                else:
                    if last_event_time >= warmup_end:
                        count_blk += 1
                next_arrival = event_time + rng.expovariate(lam)
            else:
                if queue:
                    arr_t, svc_t = queue.pop(0)
                    wait_time = max(0, busy_until - arr_t)
                    total_time = svc_t + wait_time
                    if last_event_time >= warmup_end:
                        sum_W += total_time
                        count_dep += 1
                        if wait_time > 1e-9:
                            count_waited += 1
                    num_in_system -= 1
                    if num_in_system > 0:
                        next_svc = queue[0][1]
                        busy_until = event_time + next_svc
                    else:
                        busy_until = -1.0
                        
            last_event_time = event_time
            
        win_len = H - warmup_end
        if win_len <= 0:
            continue
            
        L_est = area_L / win_len
        W_est = sum_W / count_dep if count_dep > 0 else 0.0
        bf_est = area_busy / win_len
        pl_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0.0
        pw_est = count_waited / count_dep if count_dep > 0 else 0.0
        bu_est = (area_L / win_len) / c if c > 0 else 0.0
        dr_est = count_dep / win_len
        le_est = count_arr / win_len
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(bf_est)
        all_p_loss.append(pl_est)
        all_p_wait.append(pw_est)
        all_arr.append(count_arr)
        all_blk.append(count_blk)
        all_dep.append(count_dep)
        all_busy_util.append(bu_est)
        all_dep_rate.append(dr_est)
        all_lam_eff.append(le_est)
        
        seeds_used += 1
        used_seeds_list.append(s)

    if seeds_used == 0:
        print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_loss":0,"runtime_units":"hour","seed_list":[],"seeds_used":0,"time_unit":"hour","win":0,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_wait":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[]}))
        return

    avg_L = sum(all_L)/seeds_used
    avg_W = sum(all_W)/seeds_used
    avg_bf = sum(all_busy_frac)/seeds_used
    avg_pl = sum(all_p_loss)/seeds_used
    avg_pw = sum(all_p_wait)/seeds_used
    avg_arr = sum(all_arr)/seeds_used
    avg_blk = sum(all_blk)/seeds_used
    avg_dep = sum(all_dep)/seeds_used
    avg_bu = sum(all_busy_util)/seeds_used
    avg_dr = sum(all_dep_rate)/seeds_used
    avg_le = sum(all_lam_eff)/seeds_used
    
    res = {
        "L": avg_L,
        "W": avg_W,
        "busy_frac": avg_bf,
        "p_loss": avg_pl,
        "runtime_units": time_unit,
        "seed_list": used_seeds_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": H * 0.75,
        "arr": avg_arr,
        "blk": avg_blk,
        "busy_util": avg_bu,
        "dep": avg_dep,
        "dep_rate": avg_dr,
        "lam_eff": avg_le,
        "p_wait": avg_pw,
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
