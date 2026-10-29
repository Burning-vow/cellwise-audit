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

    lam_base = 6.0
    mu_base = 12.0
    c = 1
    K = 6

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 2
    else:
        lam = lam_base
        mu = mu_base

    time_unit = 'hour'
    win = H * 0.75
    warmup = H * 0.25

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
    seeds_used_list = []

    for i in range(N_seeds):
        seed = seed_start + i
        rng = random.Random(seed)
        t = 0.0
        next_arrival = rng.expovariate(lam)
        service_times = []
        queue = []
        in_service = None
        n_in_system = 0
        arrivals = 0
        blocks = 0
        departures = 0
        total_wait_time = 0.0
        total_service_time = 0.0
        busy_time = 0.0
        last_event_time = 0.0
        area_L = 0.0
        area_busy = 0.0
        area_wait = 0.0
        count_wait = 0
        events = []
        
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
        
        add_event(next_arrival, 'arrival')
        
        while True:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            et, typ, data = events.pop(0)
            
            if et > H:
                break
            
            dt = et - last_event_time
            if last_event_time >= warmup and et <= H:
                seg_win = min(et, H) - max(last_event_time, warmup)
                if seg_win > 0:
                    area_L += n_in_system * seg_win
                    if n_in_system > 0:
                        area_busy += seg_win
                    if len(queue) > 0 or (in_service is not None and len(queue)==0 and n_in_system>0):
                         pass
                    # p_wait: fraction of time someone is waiting? Or probability a customer waits?
                    # Usually p_wait is prob that an arriving customer has to wait.
                    # But here we need area-based or event-based?
                    # Let's compute p_wait as proportion of customers who waited.
                    # We'll track it separately.
            
            last_event_time = et
            
            if typ == 'arrival':
                if last_event_time >= warmup:
                    arrivals += 1
                
                if n_in_system < K:
                    st = rng.expovariate(mu)
                    queue.append((et, st))
                    n_in_system += 1
                    
                    if in_service is None:
                        start_t, svc_dur = queue.pop(0)
                        in_service = (start_t, svc_dur, et)
                        end_t = et + svc_dur
                        add_event(end_t, 'departure', (start_t, svc_dur))
                        if last_event_time >= warmup:
                            w = et - start_t
                            total_wait_time += w
                            if w > 0:
                                count_wait += 1
                else:
                    if last_event_time >= warmup:
                        blocks += 1
                
                na = rng.expovariate(lam)
                add_event(et + na, 'arrival')
                
            elif typ == 'departure':
                start_t, svc_dur = data
                if last_event_time >= warmup:
                    departures += 1
                    total_service_time += svc_dur
                
                n_in_system -= 1
                in_service = None
                
                if queue:
                    s_t, s_dur = queue.pop(0)
                    in_service = (s_t, s_dur, et)
                    end_t = et + s_dur
                    add_event(end_t, 'departure', (s_t, s_dur))
                    if last_event_time >= warmup:
                        w = et - s_t
                        total_wait_time += w
                        if w > 0:
                            count_wait += 1

        if last_event_time < H:
             dt_final = H - last_event_time
             if last_event_time >= warmup:
                 area_L += n_in_system * dt_final
                 if n_in_system > 0:
                     area_busy += dt_final
        
        L_est = area_L / win if win > 0 else 0
        W_est = total_wait_time / departures if departures > 0 else 0
        busy_frac_est = area_busy / win if win > 0 else 0
        p_loss_est = blocks / arrivals if arrivals > 0 else 0
        p_wait_est = count_wait / departures if departures > 0 else 0
        busy_util_est = (area_busy / win) / c if win > 0 and c > 0 else 0
        dep_rate_est = departures / win if win > 0 else 0
        lam_eff_est = arrivals / win if win > 0 else 0
        
        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arrivals)
        all_blk.append(blocks)
        all_dep.append(departures)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        seeds_used_list.append(seed)

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
        "runtime_units": time_unit,
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
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
        "per_seed_p_wait": per_seed_p_wait,
        "busy_occupied": avg_busy_frac
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
