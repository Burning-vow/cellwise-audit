import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert

    lam_base = 4.0
    mu1_base = 60.0 / 7.5
    mu2_base = 60.0 / 6.0

    if pert == 'lam_up':
        lam = lam_base * 1.2
        mu1 = mu1_base
        mu2 = mu2_base
    elif pert == 'mu_up':
        lam = lam_base
        mu1 = mu1_base * 1.2
        mu2 = mu2_base * 1.2
    elif pert == 'c_up':
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base
    else:
        lam = lam_base
        mu1 = mu1_base
        mu2 = mu2_base

    time_unit = "hour"
    win = H * 0.75
    warmup_end = H * 0.25

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    seed_list = []

    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        
        queue1 = []
        queue2 = []
        busy1_until = -1.0
        busy2_until = -1.0
        
        n_arr = 0
        n_dep = 0
        n_blk = 0
        
        area_in_sys = 0.0
        total_time_in_sys = 0.0
        
        last_event_time = 0.0
        current_n_in_sys = 0
        
        events = []
        
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
            
        add_event(next_arrival, 'arrival')
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            curr_t, typ, data = events.pop(0)
            
            if curr_t > H:
                break
                
            dt = curr_t - last_event_time
            if last_event_time >= warmup_end:
                area_in_sys += current_n_in_sys * dt
            last_event_time = curr_t
            
            if typ == 'arrival':
                n_arr += 1
                service_time_1 = rng.expovariate(mu1)
                job = {'arrival_time': curr_t, 'service_time_1': service_time_1}
                
                if len(queue1) == 0 and busy1_until <= curr_t:
                    busy1_until = curr_t + service_time_1
                    add_event(busy1_until, 'finish1', job)
                    current_n_in_sys += 1
                else:
                    queue1.append(job)
                    current_n_in_sys += 1
                    
                next_arrival = curr_t + rng.expovariate(lam)
                add_event(next_arrival, 'arrival')
                
            elif typ == 'finish1':
                job = data
                service_time_2 = rng.expovariate(mu2)
                job['service_time_2'] = service_time_2
                
                if len(queue2) == 0 and busy2_until <= curr_t:
                    busy2_until = curr_t + service_time_2
                    add_event(busy2_until, 'finish2', job)
                else:
                    queue2.append(job)
                    
                if queue1:
                    next_job = queue1.pop(0)
                    busy1_until = curr_t + next_job['service_time_1']
                    add_event(busy1_until, 'finish1', next_job)
                else:
                    busy1_until = -1.0
                    
            elif typ == 'finish2':
                job = data
                n_dep += 1
                w_time = curr_t - job['arrival_time']
                if curr_t >= warmup_end:
                    total_time_in_sys += w_time
                
                current_n_in_sys -= 1
                
                if queue2:
                    next_job = queue2.pop(0)
                    busy2_until = curr_t + next_job['service_time_2']
                    add_event(busy2_until, 'finish2', next_job)
                else:
                    busy2_until = -1.0

        L_est = area_in_sys / win if win > 0 else 0.0
        W_est = (total_time_in_sys / n_dep) * 60.0 if n_dep > 0 else 0.0
        
        busy_time_1 = 0.0
        # Recalculate busy fraction properly by tracking intervals or simpler approximation? 
        # For strict correctness, we should have tracked busy times during simulation.
        # Let's re-run a lightweight pass or track it. Tracking is better.
        # Since I didn't track busy time explicitly in the loop above efficiently for fractions,
        # I will approximate using Little's Law consistency check or just report 0 if hard to get exactly without more state.
        # Actually, let's fix the logic to track busy times.
        
        # Re-implementing with busy time tracking for accuracy
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        queue1 = []
        queue2 = []
        busy1_until = -1.0
        busy2_until = -1.0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        area_in_sys = 0.0
        total_time_in_sys = 0.0
        last_event_time = 0.0
        current_n_in_sys = 0
        busy_time_1 = 0.0
        busy_time_2 = 0.0
        events = [(next_arrival, 'arrival', None)]
        
        while events:
            events.sort(key=lambda x: x[0])
            curr_t, typ, data = events.pop(0)
            if curr_t > H: break
            
            dt = curr_t - last_event_time
            if last_event_time >= warmup_end:
                area_in_sys += current_n_in_sys * dt
                if busy1_until > last_event_time:
                    busy_time_1 += min(curr_t, busy1_until) - max(last_event_time, warmup_end) if last_event_time < warmup_end else dt
                # Simplified busy accumulation:
                if busy1_until > last_event_time:
                     b_start = max(last_event_time, warmup_end)
                     b_end = min(curr_t, busy1_until)
                     if b_end > b_start: busy_time_1 += b_end - b_start
                if busy2_until > last_event_time:
                     b_start = max(last_event_time, warmup_end)
                     b_end = min(curr_t, busy2_until)
                     if b_end > b_start: busy_time_2 += b_end - b_start
                     
            last_event_time = curr_t
            
            if typ == 'arrival':
                n_arr += 1
                st1 = rng.expovariate(mu1)
                job = {'at': curr_t, 'st1': st1}
                if len(queue1) == 0 and busy1_until <= curr_t:
                    busy1_until = curr_t + st1
                    events.append((busy1_until, 'finish1', job))
                    current_n_in_sys += 1
                else:
                    queue1.append(job)
                    current_n_in_sys += 1
                na = curr_t + rng.expovariate(lam)
                events.append((na, 'arrival', None))
            elif typ == 'finish1':
                job = data
                st2 = rng.expovariate(mu2)
                job['st2'] = st2
                if len(queue2) == 0 and busy2_until <= curr_t:
                    busy2_until = curr_t + st2
                    events.append((busy2_until, 'finish2', job))
                else:
                    queue2.append(job)
                if queue1:
                    nj = queue1.pop(0)
                    busy1_until = curr_t + nj['st1']
                    events.append((busy1_until, 'finish1', nj))
                else:
                    busy1_until = -1.0
            elif typ == 'finish2':
                job = data
                n_dep += 1
                wt = curr_t - job['at']
                if curr_t >= warmup_end:
                    total_time_in_sys += wt
                current_n_in_sys -= 1
                if queue2:
                    nj = queue2.pop(0)
                    busy2_until = curr_t + nj['st2']
                    events.append((busy2_until, 'finish2', nj))
                else:
                    busy2_until = -1.0

        L_est = area_in_sys / win if win > 0 else 0.0
        W_est = (total_time_in_sys / n_dep) * 60.0 if n_dep > 0 else 0.0
        bf1 = busy_time_1 / win if win > 0 else 0.0
        bf2 = busy_time_2 / win if win > 0 else 0.0
        avg_bf = (bf1 + bf2) / 2.0
        p_loss = n_blk / n_arr if n_arr > 0 else 0.0
        p_wait = 1.0 - (n_dep / n_arr) if n_arr > 0 else 0.0 # Approximation for blocking/loss
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(avg_bf)
        all_p_loss.append(p_loss)
        all_p_wait.append(p_wait)
        all_arr.append(n_arr)
        all_dep.append(n_dep)
        all_blk.append(n_blk)
        seed_list.append(seed)

    seeds_used = len(all_L)
    mean_L = sum(all_L) / seeds_used if seeds_used else 0
    mean_W = sum(all_W) / seeds_used if seeds_used else 0
    mean_bf = sum(all_busy_frac) / seeds_used if seeds_used else 0
    mean_pl = sum(all_p_loss) / seeds_used if seeds_used else 0
    mean_pw = sum(all_p_wait) / seeds_used if seeds_used else 0
    mean_arr = sum(all_arr) / seeds_used if seeds_used else 0
    mean_dep = sum(all_dep) / seeds_used if seeds_used else 0
    mean_blk = sum(all_blk) / seeds_used if seeds_used else 0
    
    dep_rate = mean_dep / win if win > 0 else 0
    lam_eff = dep_rate
    
    result = {
        "L": round(mean_L, 4),
        "W": round(mean_W, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(mean_arr, 4),
        "blk": round(mean_blk, 4),
        "busy_frac": round(mean_bf, 4),
        "busy_util": round(mean_bf, 4),
        "dep": round(mean_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(mean_pl, 4),
        "p_wait": round(mean_pw, 4),
        "per_seed_L": [round(x, 4) for x in all_L],
        "per_seed_W": [round(x, 4) for x in all_W],
        "per_seed_busy_frac": [round(x, 4) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in all_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
