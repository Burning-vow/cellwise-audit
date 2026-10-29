import sys, json, random, math
from collections import deque

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if i+1 < len(argv):
            args[argv[i].lstrip('-')] = argv[i+1]
    
    seeds_n = int(args.get('seeds', '5'))
    horizon = float(args.get('horizon', '100.0'))
    seed_start = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    
    lam_base = 9.0
    mu_base = 60.0 / 5.0
    
    if pert == 'lam_up': lam_base *= 1.2
    elif pert == 'mu_up': mu_base *= 1.2
    elif pert == 'c_up': pass 
    
    time_unit = 'hour'
    win_len = horizon * 0.75
    warmup_end = horizon * 0.25
    
    all_L_area = 0.0
    all_W_sum = 0.0
    all_busy_time = 0.0
    all_arr = 0
    all_blk = 0
    all_dep = 0
    all_wait_count = 0
    
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    used_seeds = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        used_seeds.append(current_seed)
        rng = random.Random(current_seed)
        
        t = 0.0
        queue = deque()
        service_end = -1.0
        server_busy = False
        
        next_arr_t = rng.expovariate(lam_base)
        
        L_area = 0.0
        W_sum = 0.0
        busy_time = 0.0
        arr_cnt = 0
        blk_cnt = 0
        dep_cnt = 0
        wait_cnt = 0
        
        last_event_t = 0.0
        last_N = 0
        
        while t < horizon:
            if not server_busy and queue:
                cust = queue.popleft()
                dur = cust['dur']
                service_end = t + dur
                server_busy = True
                continue
            
            events = []
            if next_arr_t <= horizon:
                events.append(('arr', next_arr_t))
            if server_busy:
                events.append(('dep', service_end))
            
            if not events:
                break
                
            ev_type, ev_t = min(events, key=lambda x: x[1])
            
            dt = ev_t - last_event_t
            if last_event_t >= warmup_end:
                L_area += last_N * dt
                if last_N > 0:
                    busy_time += dt
            
            t = ev_t
            last_event_t = t
            
            if ev_type == 'arr':
                if t >= warmup_end:
                    arr_cnt += 1
                if len(queue) + (1 if server_busy else 0) < 4:
                    dur = rng.expovariate(mu_base)
                    queue.append({'arrival': t, 'dur': dur})
                    if t >= warmup_end:
                        if server_busy or len(queue) > 1: 
                            pass 
                else:
                    if t >= warmup_end:
                        blk_cnt += 1
                next_arr_t = t + rng.expovariate(lam_base)
                
            elif ev_type == 'dep':
                if t >= warmup_end:
                    dep_cnt += 1
                    if queue:
                        cust = queue[0]
                        w = t - cust['arrival']
                        W_sum += w
                        if w > 0:
                            wait_cnt += 1
                server_busy = False
                if queue:
                    cust = queue.popleft()
                    dur = cust['dur']
                    service_end = t + dur
                    server_busy = True
            
            N_now = len(queue) + (1 if server_busy else 0)
            last_N = N_now

        if last_event_t < horizon:
             dt = horizon - last_event_t
             if last_event_t >= warmup_end:
                 L_area += last_N * dt
                 if last_N > 0:
                     busy_time += dt

        eff_win = max(0.0, horizon - warmup_end)
        if eff_win > 0:
            l_val = L_area / eff_win
            b_val = busy_time / eff_win
            p_loss_val = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
            p_wait_val = wait_cnt / dep_cnt if dep_cnt > 0 else 0.0
            w_val = W_sum / dep_cnt if dep_cnt > 0 else 0.0
        else:
            l_val = b_val = p_loss_val = p_wait_val = w_val = 0.0
            
        per_seed_L.append(l_val)
        per_seed_W.append(w_val)
        per_seed_busy_frac.append(b_val)
        per_seed_p_loss.append(p_loss_val)
        per_seed_p_wait.append(p_wait_val)
        
        all_L_area += L_area
        all_W_sum += W_sum
        all_busy_time += busy_time
        all_arr += arr_cnt
        all_blk += blk_cnt
        all_dep += dep_cnt
        all_wait_count += wait_cnt

    total_eff_win = seeds_n * max(0.0, horizon - warmup_end)
    
    final_L = all_L_area / total_eff_win if total_eff_win > 0 else 0.0
    final_W = all_W_sum / all_dep if all_dep > 0 else 0.0
    final_busy_frac = all_busy_time / total_eff_win if total_eff_win > 0 else 0.0
    final_p_loss = all_blk / all_arr if all_arr > 0 else 0.0
    final_p_wait = all_wait_count / all_dep if all_dep > 0 else 0.0
    
    avg_arr = all_arr / seeds_n
    avg_blk = all_blk / seeds_n
    avg_dep = all_dep / seeds_n
    dep_rate = avg_dep / max(0.001, horizon - warmup_end) if horizon > warmup_end else 0.0
    lam_eff = dep_rate
    
    c = 1
    busy_util = final_busy_frac / c
    
    out = {
        "L": round(final_L, 6),
        "W": round(final_W, 6),
        "busy_frac": round(final_busy_frac, 6),
        "p_loss": round(final_p_loss, 6),
        "runtime_units": time_unit,
        "seed_list": used_seeds,
        "seeds_used": seeds_n,
        "time_unit": time_unit,
        "win": round(horizon - warmup_end, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(final_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
