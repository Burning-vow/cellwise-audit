import sys, json, math, random
from collections import deque

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith('--'):
            k = sys.argv[i][2:]
            v = sys.argv[i+1] if i+1 < len(sys.argv) else None
            args[k] = v
            i += 2
        else:
            i += 1
    
    seeds_n = int(args.get('seeds', '5'))
    horizon = float(args.get('horizon', '100.0'))
    seed_start = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    
    lam_base = 4.0 / 60.0
    mu_base = 1.0 / 5.0
    
    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = 2
    else:
        lam = lam_base
        mu = mu_base
        c = 1
        
    time_unit = "minute"
    win_len = horizon * 0.75
    warmup_end = horizon * 0.25
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    all_busy_util = []
    all_dep_rate = []
    all_lam_eff = []
    all_p_loss = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    
    for s_idx in range(seeds_n):
        current_seed = seed_start + s_idx
        rng = random.Random(current_seed)
        
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = []
        queue = deque()
        busy_until = 0.0
        num_in_system = 0
        total_time_in_system = 0.0
        arrivals_count = 0
        departures_count = 0
        blocked_count = 0
        wait_events = 0
        busy_time_accum = 0.0
        last_event_t = 0.0
        state_changes = []
        
        while t < horizon:
            if not queue and (busy_until <= t or num_in_system == 0):
                if next_arrival > horizon:
                    break
                dt = next_arrival - t
                if t >= warmup_end:
                    pass 
                t = next_arrival
                if t >= warmup_end:
                    arrivals_count += 1
                    st = rng.expovariate(mu)
                    queue.append((t, st))
                    num_in_system += 1
                    if num_in_system > 0:
                        busy_until = max(busy_until, t) + st
                        if busy_until > t:
                            pass
                next_arrival = t + rng.expovariate(lam)
                continue
            
            if queue:
                arr_t, svc_t = queue[0]
                start_svc = max(arr_t, busy_until)
                end_svc = start_svc + svc_t
                
                if end_svc > horizon:
                    break
                    
                dt_to_next = end_svc - t
                if next_arrival < end_svc:
                    dt_to_next = next_arrival - t
                    event_type = 'arrival'
                else:
                    event_type = 'departure'
                    
                if t + dt_to_next > horizon:
                    break
                    
                prev_num = num_in_system
                if t >= warmup_end:
                    dur = min(t + dt_to_next, horizon) - max(t, warmup_end)
                    if dur > 0:
                        if prev_num > 0:
                            busy_time_accum += dur
                        total_time_in_system += prev_num * dur
                        
                t += dt_to_next
                
                if event_type == 'arrival':
                    if t >= warmup_end:
                        arrivals_count += 1
                        st = rng.expovariate(mu)
                        queue.append((t, st))
                        num_in_system += 1
                        if num_in_system == 1:
                            busy_until = t + st
                    next_arrival = t + rng.expovariate(lam)
                else:
                    if t >= warmup_end:
                        departures_count += 1
                        if len(queue) > 0:
                            q_arr_t, _ = queue.popleft()
                            if t > q_arr_t:
                                wait_events += 1
                        num_in_system -= 1
                        if num_in_system > 0 and queue:
                            nxt_arr_t, nxt_svc_t = queue[0]
                            busy_until = max(nxt_arr_t, busy_until) + nxt_svc_t
                        else:
                            busy_until = 0.0
                            
        if t >= horizon:
             final_t = horizon
        else:
             final_t = t
             
        if final_t > warmup_end:
            w_dur = final_t - warmup_end
            L_est = total_time_in_system / w_dur
            W_est = total_time_in_system / departures_count if departures_count > 0 else 0
            bf_est = busy_time_accum / w_dur
            pw_est = wait_events / arrivals_count if arrivals_count > 0 else 0
            pl_est = blocked_count / arrivals_count if arrivals_count > 0 else 0
            bu_est = busy_time_accum / w_dur
            dr_est = departures_count / (w_dur / 60.0) if w_dur > 0 else 0
            le_est = arrivals_count / (w_dur / 60.0) if w_dur > 0 else 0
            
            all_L.append(L_est)
            all_W.append(W_est)
            all_busy_frac.append(bf_est)
            all_p_wait.append(pw_est)
            all_arr.append(arrivals_count)
            all_dep.append(departures_count)
            all_blk.append(blocked_count)
            all_busy_util.append(bu_est)
            all_dep_rate.append(dr_est)
            all_lam_eff.append(le_est)
            all_p_loss.append(pl_est)
            
            per_seed_L.append(L_est)
            per_seed_W.append(W_est)
            per_seed_busy_frac.append(bf_est)
            per_seed_p_loss.append(pl_est)
            per_seed_p_wait.append(pw_est)
            seed_list.append(current_seed)
            
    n_seeds = len(seed_list)
    if n_seeds == 0:
        print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_wait":0,"runtime_units":"minute","seed_list":[],"seeds_used":0,"time_unit":"minute","win":0,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_loss":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[]}))
        return

    avg_L = sum(all_L)/n_seeds
    avg_W = sum(all_W)/n_seeds
    avg_bf = sum(all_busy_frac)/n_seeds
    avg_pw = sum(all_p_wait)/n_seeds
    avg_arr = sum(all_arr)/n_seeds
    avg_dep = sum(all_dep)/n_seeds
    avg_blk = sum(all_blk)/n_seeds
    avg_bu = sum(all_busy_util)/n_seeds
    avg_dr = sum(all_dep_rate)/n_seeds
    avg_le = sum(all_lam_eff)/n_seeds
    avg_pl = sum(all_p_loss)/n_seeds
    
    res = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "minute",
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_bu, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dr, 6),
        "lam_eff": round(avg_le, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
