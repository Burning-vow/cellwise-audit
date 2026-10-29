import argparse, json, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 8.0
    mu_base = 10.0 # 6 min service -> 10 per hour
    c = 1
    
    if a.pert == 'lam_up': lam = lam_base * 1.2
    elif a.pert == 'mu_up': mu = mu_base * 1.2; lam = lam_base
    elif a.pert == 'c_up': c = 2; lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    horizon = a.horizon
    warmup = horizon * 0.25
    win_len = horizon - warmup
    
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
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        
        queue = []
        serving = False
        serv_end = 0.0
        
        area_N = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        time_busy = 0.0
        time_total_win = 0.0
        
        while t < horizon:
            if not serving and queue:
                cust = queue.pop(0)
                serving = True
                serv_dur = 6.0 / 60.0 # hours
                serv_end = t + serv_dur
                next_dep = serv_end
            
            events = []
            if next_arr < horizon: events.append(('arr', next_arr))
            if serving and next_dep < horizon: events.append(('dep', next_dep))
            
            if not events: break
            
            ev_type, ev_time = min(events, key=lambda x: x[1])
            
            dt = ev_time - t
            if t >= warmup:
                n_now = len(queue) + (1 if serving else 0)
                area_N += n_now * dt
                if serving: time_busy += dt
                time_total_win += dt
            
            t = ev_time
            
            if ev_type == 'arr':
                if t >= warmup: count_arr += 1
                if serving or len(queue) > 0:
                    queue.append(t)
                else:
                    serving = True
                    serv_dur = 6.0 / 60.0
                    serv_end = t + serv_dur
                    next_dep = serv_end
                
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                if t >= warmup:
                    count_dep += 1
                    arr_time = queue.pop(0) if queue else None 
                    # Wait, logic error: if we started service immediately upon arrival when idle, 
                    # the customer isn't in queue. We need to track start time of current service.
                    # Let's refactor slightly inside loop.
                    pass
                serving = False
                next_dep = float('inf')
                
                if queue:
                    cust_arr_t = queue.pop(0)
                    serving = True
                    serv_dur = 6.0 / 60.0
                    serv_end = t + serv_dur
                    next_dep = serv_end
                    if t >= warmup:
                        w = serv_end - cust_arr_t
                        sum_W += w
                else:
                    # Check if the one just finished was counted correctly?
                    # The departure event corresponds to the service that ended at t.
                    # Who was being served? We lost their arrival time if we didn't store it.
                    pass

        # Re-implementing loop cleanly with state tracking for W calculation
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        queue = [] # stores arrival times
        serving = False
        serv_start_t = 0.0
        serv_end_t = 0.0
        
        area_N = 0.0
        count_arr = 0
        count_dep = 0
        count_blk = 0
        sum_W = 0.0
        time_busy = 0.0
        time_total_win = 0.0
        
        while t < horizon:
            # Determine next event
            events = []
            if next_arr <= horizon: events.append((next_arr, 'arr'))
            if serving and next_dep <= horizon: events.append((next_dep, 'dep'))
            
            if not events: break
            
            ev_time, ev_type = min(events, key=lambda x: x[0])
            
            dt = ev_time - t
            if t >= warmup:
                n_now = len(queue) + (1 if serving else 0)
                area_N += n_now * dt
                if serving: time_busy += dt
                time_total_win += dt
            
            t = ev_time
            
            if ev_type == 'arr':
                if t >= warmup: count_arr += 1
                if serving or len(queue) > 0:
                    queue.append(t)
                else:
                    serving = True
                    serv_start_t = t
                    serv_end_t = t + 6.0/60.0
                    next_dep = serv_end_t
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                if t >= warmup:
                    count_dep += 1
                    w = serv_end_t - serv_start_t
                    sum_W += w
                
                serving = False
                next_dep = float('inf')
                
                if queue:
                    arr_t = queue.pop(0)
                    serving = True
                    serv_start_t = t
                    serv_end_t = t + 6.0/60.0
                    next_dep = serv_end_t
        
        L_est = area_N / time_total_win if time_total_win > 0 else 0
        W_est = sum_W / count_dep if count_dep > 0 else 0
        bf_est = time_busy / time_total_win if time_total_win > 0 else 0
        pl_est = count_blk / count_arr if count_arr > 0 else 0 # blk is always 0 here as no capacity limit mentioned other than FCFS infinite queue? "自动洗车机" usually implies single server, infinite queue unless specified. Problem says "场内平均车辆数", implies queue exists. No blocking mentioned. So blk=0.
        pw_est = 0.0 # Probability of waiting. If queue length > 0 on arrival.
        
        # Recalculate p_wait properly during simulation would be better, but approximating via Little's Law or direct count?
        # Direct count: On arrival, if system busy (serving or queue non-empty), they wait.
        # I missed counting waits in the loop above. Let's assume standard M/M/1 behavior where P(wait) = rho.
        # But let's stick to empirical. I'll add a counter for arrivals that join queue or find server busy.
        
        # Since I can't easily re-run without rewriting, I will estimate p_wait from L and W relations or just set based on theory if empirical missing.
        # Actually, let's look at the code structure again. I need to output valid JSON.
        # For this specific problem (M/D/1 essentially, fixed service), P(wait) = lambda * E[S] = rho.
        # Empirical p_wait: Count arrivals where (serving OR queue not empty).
        
        # I will re-calculate p_wait empirically by adding a flag in the loop.
        # Since I am generating code now, I will include the counter.
        
        # Resetting variables for final clean implementation below
        pass 

    # Final Clean Implementation
    results = []
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        queue = []
        serving = False
        serv_start_t = 0.0
        serv_end_t = 0.0
        
        area_N = 0.0
        count_arr = 0
        count_dep = 0
        count_wait = 0
        sum_W = 0.0
        time_busy = 0.0
        time_total_win = 0.0
        
        while t < horizon:
            events = []
            if next_arr <= horizon: events.append((next_arr, 'arr'))
            if serving and next_dep <= horizon: events.append((next_dep, 'dep'))
            if not events: break
            
            ev_time, ev_type = min(events, key=lambda x: x[0])
            dt = ev_time - t
            
            if t >= warmup:
                n_now = len(queue) + (1 if serving else 0)
                area_N += n_now * dt
                if serving: time_busy += dt
                time_total_win += dt
            
            t = ev_time
            
            if ev_type == 'arr':
                if t >= warmup:
                    count_arr += 1
                    if serving or len(queue) > 0:
                        count_wait += 1
                
                if serving or len(queue) > 0:
                    queue.append(t)
                else:
                    serving = True
                    serv_start_t = t
                    serv_end_t = t + 6.0/60.0
                    next_dep = serv_end_t
                next_arr = t + rng.expovariate(lam)
                
            elif ev_type == 'dep':
                if t >= warmup:
                    count_dep += 1
                    sum_W += serv_end_t - serv_start_t
                
                serving = False
                next_dep = float('inf')
                
                if queue:
                    arr_t = queue.pop(0)
                    serving = True
                    serv_start_t = t
                    serv_end_t = t + 6.0/60.0
                    next_dep = serv_end_t
        
        L_est = area_N / time_total_win if time_total_win > 0 else 0
        W_est = sum_W / count_dep if count_dep > 0 else 0
        bf_est = time_busy / time_total_win if time_total_win > 0 else 0
        p_wait_est = count_wait / count_arr if count_arr > 0 else 0
        p_loss_est = 0.0 # Infinite queue assumed
        
        results.append({
            'L': L_est, 'W': W_est, 'busy_frac': bf_est,
            'p_wait': p_wait_est, 'p_loss': p_loss_est,
            'arr': count_arr, 'dep': count_dep, 'blk': 0,
            'busy_util': bf_est, 'busy_occupied': bf_est # c=1
        })
        
    avg_L = sum(r['L'] for r in results) / len(results)
    avg_W = sum(r['W'] for r in results) / len(results)
    avg_bf = sum(r['busy_frac'] for r in results) / len(results)
    avg_pw = sum(r['p_wait'] for r in results) / len(results)
    avg_pl = sum(r['p_loss'] for r in results) / len(results)
    avg_arr = sum(r['arr'] for r in results) / len(results)
    avg_dep = sum(r['dep'] for r in results) / len(results)
    avg_blk = sum(r['blk'] for r in results) / len(results)
    avg_bu = sum(r['busy_util'] for r in results) / len(results)
    avg_bo = sum(r['busy_occupied'] for r in results) / len(results)
    
    dep_rate = avg_dep / win_len if win_len > 0 else 0
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "runtime_units": "hour",
        "seed_list": [a.seed_start + i for i in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(avg_arr / win_len, 6) if win_len > 0 else 0,
        "p_loss": round(avg_pl, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(r['L'], 6) for r in results],
        "per_seed_W": [round(r['W'], 6) for r in results],
        "per_seed_busy_frac": [round(r['busy_frac'], 6) for r in results],
        "per_seed_p_loss": [round(r['p_loss'], 6) for r in results],
        "per_seed_p_wait": [round(r['p_wait'], 6) for r in results]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
