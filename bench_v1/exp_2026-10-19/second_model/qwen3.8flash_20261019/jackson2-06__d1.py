import random, json, math, sys

def main():
    args = {}
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i].startswith('--'):
            k = argv[i][2:]
            v = argv[i+1] if i+1 < len(argv) and not argv[i+1].startswith('--') else None
            args[k] = v
            i += 2
        else:
            i += 1
    seeds_n = int(args.get('seeds', '5'))
    horizon = float(args.get('horizon', '100.0'))
    seed_start = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')

    lam_base = 6.0
    mu1_base = 8.0
    mu2_base = 12.0
    c_base = 0.0

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

    time_unit = 'hour'
    win = horizon * 0.75
    warmup_end = horizon * 0.25

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_dep = []
    all_blk = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []

    for s_idx in range(seeds_n):
        seed_val = seed_start + s_idx
        rng = random.Random(seed_val)
        t = 0.0
        next_arr = -rng.expovariate(lam)
        q1 = []
        q2 = []
        busy1_until = -1.0
        busy2_until = -1.0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        total_wip_area = 0.0
        last_t = 0.0
        events = []
        
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
            
        add_event(next_arr, 'arr')
        
        while t <= horizon:
            if not events:
                break
            events.sort(key=lambda x: x[0])
            ev_time, ev_type, ev_data = events.pop(0)
            if ev_time > horizon:
                break
                
            dt = ev_time - last_t
            wip_now = len(q1) + len(q2) + (1 if busy1_until >= last_t else 0) + (1 if busy2_until >= last_t else 0)
            if last_t >= warmup_end:
                total_wip_area += wip_now * dt
            last_t = ev_time
            
            if ev_type == 'arr':
                if ev_time >= warmup_end:
                    arr_count += 1
                svc1 = rng.expovariate(mu1)
                if busy1_until <= ev_time:
                    start1 = ev_time
                    end1 = ev_time + svc1
                    busy1_until = end1
                    add_event(end1, 'dep1', {'start': start1})
                else:
                    q1.append({'arrival': ev_time, 'svc': svc1})
                next_arr = ev_time + rng.expovariate(lam)
                add_event(next_arr, 'arr')
                
            elif ev_type == 'dep1':
                start1 = ev_data['start']
                if busy2_until <= ev_time:
                    svc2 = rng.expovariate(mu2)
                    start2 = ev_time
                    end2 = ev_time + svc2
                    busy2_until = end2
                    add_event(end2, 'dep2', {'start': start2, 'orig_arr': start1})
                else:
                    q2.append({'entry': ev_time, 'orig_arr': start1})
                    
            elif ev_type == 'dep2':
                orig_arr = ev_data['orig_arr']
                if ev_time >= warmup_end:
                    dep_count += 1
                    stay = ev_time - orig_arr
                    all_W.append(stay)
                if q1:
                    item = q1.pop(0)
                    svc1_rem = item['svc']
                    if busy1_until <= ev_time:
                        start1_new = ev_time
                        end1_new = ev_time + svc1_rem
                        busy1_until = end1_new
                        add_event(end1_new, 'dep1', {'start': start1_new})
                    else:
                        q1.insert(0, item)
                if q2:
                    item2 = q2.pop(0)
                    svc2 = rng.expovariate(mu2)
                    start2_new = ev_time
                    end2_new = ev_time + svc2
                    busy2_until = end2_new
                    add_event(end2_new, 'dep2', {'start': start2_new, 'orig_arr': item2['orig_arr']})
                    
            if ev_time >= warmup_end:
                pass 

        L_est = total_wip_area / win if win > 0 else 0
        W_est = sum(all_W[-dep_count:]) / dep_count if dep_count > 0 else 0
        busy1_time = max(0, min(horizon, busy1_until) - warmup_end) if busy1_until > warmup_end else 0
        busy2_time = max(0, min(horizon, busy2_until) - warmup_end) if busy2_until > warmup_end else 0
        busy_frac_est = (busy1_time + busy2_time) / (2 * win) if win > 0 else 0
        
        p_loss_est = 0.0
        p_wait_est = 0.0
        
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(busy_frac_est)
        per_seed_p_loss.append(p_loss_est)
        per_seed_p_wait.append(p_wait_est)
        all_arr.append(arr_count)
        all_dep.append(dep_count)
        all_blk.append(blk_count)
        seed_list.append(seed_val)

    avg_L = sum(per_seed_L) / len(per_seed_L) if per_seed_L else 0
    avg_W = sum(per_seed_W) / len(per_seed_W) if per_seed_W else 0
    avg_busy = sum(per_seed_busy_frac) / len(per_seed_busy_frac) if per_seed_busy_frac else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    
    dep_rate = avg_dep / win if win > 0 else 0
    lam_eff = dep_rate
    p_loss_avg = avg_blk / avg_arr if avg_arr > 0 else 0
    p_wait_avg = 0.0

    out = {
        "L": round(avg_L, 4),
        "W": round(avg_W, 4),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": time_unit,
        "win": round(win, 4),
        "arr": round(avg_arr, 4),
        "blk": round(avg_blk, 4),
        "busy_frac": round(avg_busy, 4),
        "busy_util": round(avg_busy, 4),
        "dep": round(avg_dep, 4),
        "dep_rate": round(dep_rate, 4),
        "lam_eff": round(lam_eff, 4),
        "p_loss": round(p_loss_avg, 4),
        "p_wait": round(p_wait_avg, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
