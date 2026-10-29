import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base, c = 8.0, 10.0, 2
    if a.pert == "lam_up": lam_base *= 1.2
    elif a.pert == "mu_up": mu_base *= 1.2
    elif a.pert == "c_up": c += 1
    H = float(a.horizon); warmup = 0.25 * H; win = H - warmup
    seeds_used = a.seeds; seed_list = [a.seed_start + i for i in range(seeds_used)]
    all_L, all_W, all_busy_frac, all_p_wait, all_arr, all_dep, all_blk = [], [], [], [], [], [], []
    all_busy_util, all_lam_eff, all_p_loss, all_dep_rate = [], [], [], []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0; N = 0; busy = 0; arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        wait_sum = 0.0; service_sum = 0.0; area_N = 0.0; area_minNc = 0.0
        last_t = 0.0; events = []
        next_arr = rng.expovariate(lam_base)
        while True:
            # find next event time
            cand_times = []
            if next_arr < H: cand_times.append(("arr", next_arr))
            for ev in events:
                if ev[0] < H: cand_times.append(ev)
            if not cand_times: break
            cand_times.sort(key=lambda x: x[1])
            etype, etime = cand_times[0]
            # integrate areas up to etime
            dt = etime - last_t
            if last_t >= warmup:
                area_N += N * dt
                area_minNc += min(N, c) * dt
            last_t = etime
            if etype == "arr":
                arr_cnt += 1
                svc_time = rng.expovariate(mu_base)
                if N < c:
                    busy += 1
                    N += 1
                    events.append((etime + svc_time, "dep"))
                else:
                    N += 1
                    # customer waits; we track arrival time for waiting calc
                    # store (arrival_time, service_time) in a queue
                    # For simplicity, use a list as FIFO queue of (arr_t, svc_t)
                    pass
                # Actually let's restructure: maintain a queue of customers
                # Let me redo with proper queue logic
                # Remove this and restart the loop properly
                break
            elif etype == "dep":
                dep_cnt += 1
                busy -= 1
                N -= 1
                events.remove((etime, "dep"))
            # This approach is getting messy. Let me rewrite cleanly.
            break
        # Clean rewrite below
        rng = random.Random(s)
        t = 0.0; N = 0; busy = 0; arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        wait_sum = 0.0; total_service = 0.0; area_N = 0.0; area_minNc = 0.0
        last_t = 0.0
        queue = []  # list of (arrival_time, service_duration)
        next_arr = rng.expovariate(lam_base)
        dep_events = []  # list of departure times
        
        while t < H:
            # determine next event
            next_dep = dep_events[0] if dep_events else float('inf')
            next_ev_time = min(next_arr, next_dep)
            if next_ev_time > H:
                # integrate remaining time
                dt = H - last_t
                if last_t >= warmup:
                    area_N += N * dt
                    area_minNc += min(N, c) * dt
                break
            # integrate from last_t to next_ev_time
            dt = next_ev_time - last_t
            if last_t >= warmup:
                area_N += N * dt
                area_minNc += min(N, c) * dt
            last_t = next_ev_time
            t = next_ev_time
            
            if next_ev_time <= next_arr and next_ev_time <= next_dep:
                # arrival
                arr_cnt += 1
                svc_dur = rng.expovariate(mu_base)
                if len(queue) == 0 and busy < c:
                    # start service immediately
                    busy += 1
                    dep_events.append(t + svc_dur)
                    dep_events.sort()
                    wait_sum += 0.0
                    total_service += svc_dur
                else:
                    # join queue
                    queue.append((t, svc_dur))
                    N += 1
                next_arr = t + rng.expovariate(lam_base)
            else:
                # departure
                dep_cnt += 1
                busy -= 1
                dep_events.pop(0)
                if queue:
                    arr_t, svc_dur = queue.pop(0)
                    wait_sum += (t - arr_t)
                    total_service += svc_dur
                    busy += 1
                    dep_events.append(t + svc_dur)
                    dep_events.sort()
                N -= 1
        
        L_est = area_N / win if win > 0 else 0.0
        W_est = (wait_sum + total_service) / arr_cnt if arr_cnt > 0 else 0.0
        busy_frac_est = area_minNc / (win * c) if win > 0 and c > 0 else 0.0
        busy_util_est = busy_frac_est
        p_wait_est = sum(1 for _ in [])  # need to count arrivals that found queue non-empty or all servers busy
        # Recalculate p_wait: count arrivals where at arrival time, number in system >= c
        # We didn't track this directly. Let me add tracking.
        # Redo with p_wait tracking
        rng = random.Random(s)
        t = 0.0; N = 0; busy = 0; arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        wait_sum = 0.0; total_service = 0.0; area_N = 0.0; area_minNc = 0.0
        last_t = 0.0; p_wait_count = 0
        queue = []
        next_arr = rng.expovariate(lam_base)
        dep_events = []
        
        while t < H:
            next_dep = dep_events[0] if dep_events else float('inf')
            next_ev_time = min(next_arr, next_dep)
            if next_ev_time > H:
                dt = H - last_t
                if last_t >= warmup:
                    area_N += N * dt
                    area_minNc += min(N, c) * dt
                break
            dt = next_ev_time - last_t
            if last_t >= warmup:
                area_N += N * dt
                area_minNc += min(N, c) * dt
            last_t = next_ev_time
            t = next_ev_time
            
            if next_ev_time <= next_arr and next_ev_time <= next_dep:
                arr_cnt += 1
                svc_dur = rng.expovariate(mu_base)
                if N >= c:
                    p_wait_count += 1
                if len(queue) == 0 and busy < c:
                    busy += 1
                    dep_events.append(t + svc_dur)
                    dep_events.sort()
                    wait_sum += 0.0
                    total_service += svc_dur
                else:
                    queue.append((t, svc_dur))
                    N += 1
                next_arr = t + rng.expovariate(lam_base)
            else:
                dep_cnt += 1
                busy -= 1
                dep_events.pop(0)
                if queue:
                    arr_t, svc_dur = queue.pop(0)
                    wait_sum += (t - arr_t)
                    total_service += svc_dur
                    busy += 1
                    dep_events.append(t + svc_dur)
                    dep_events.sort()
                N -= 1
        
        L_est = area_N / win if win > 0 else 0.0
        W_est = (wait_sum + total_service) / arr_cnt if arr_cnt > 0 else 0.0
        busy_frac_est = area_minNc / (win * c) if win > 0 and c > 0 else 0.0
        p_wait_est = p_wait_count / arr_cnt if arr_cnt > 0 else 0.0
        p_loss_est = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
        lam_eff_est = arr_cnt / win if win > 0 else 0.0
        dep_rate_est = dep_cnt / win if win > 0 else 0.0
        
        all_L.append(L_est); all_W.append(W_est); all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est); all_arr.append(arr_cnt); all_dep.append(dep_cnt)
        all_blk.append(blk_cnt); all_busy_util.append(busy_frac_est)
        all_lam_eff.append(lam_eff_est); all_p_loss.append(p_loss_est)
        all_dep_rate.append(dep_rate_est)
    
    avg_L = sum(all_L)/len(all_L) if all_L else 0.0
    avg_W = sum(all_W)/len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac)/len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_wait = sum(all_p_wait)/len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr)/len(all_arr) if all_arr else 0.0
    avg_dep = sum(all_dep)/len(all_dep) if all_dep else 0.0
    avg_blk = sum(all_blk)/len(all_blk) if all_blk else 0.0
    avg_busy_util = sum(all_busy_util)/len(all_busy_util) if all_busy_util else 0.0
    avg_lam_eff = sum(all_lam_eff)/len(all_lam_eff) if all_lam_eff else 0.0
    avg_p_loss = sum(all_p_loss)/len(all_p_loss) if all_p_loss else 0.0
    avg_dep_rate = sum(all_dep_rate)/len(all_dep_rate) if all_dep_rate else 0.0
    
    result = {
        "L": round(avg_L, 6), "W": round(avg_W, 6), "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6), "runtime_units": "minute", "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour", "win": round(win, 6),
        "arr": round(avg_arr, 6), "blk": round(avg_blk, 6), "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6), "dep_rate": round(avg_dep_rate, 6), "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6), "per_seed_L": [round(x,6) for x in all_L],
        "per_seed_W": [round(x,6) for x in all_W], "per_seed_busy_frac": [round(x,6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x,6) for x in all_p_loss], "per_seed_p_wait": [round(x,6) for x in all_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
