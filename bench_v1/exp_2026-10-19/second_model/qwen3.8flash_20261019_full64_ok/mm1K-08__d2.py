import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert

    lam_base = 6.0
    mu_base = 12.0
    c = 1
    K = 6

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base / 1.1
    elif pert == 'c_up':
        lam = lam_base
    else:
        lam = lam_base

    mu = mu_base

    time_unit = "hour"
    win = H

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    total_arr = 0
    total_blk = 0
    total_dep = 0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_service_time = 0.0
    total_customers_served = 0

    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end = -1.0
        busy = False
        last_event_time = 0.0
        area_N = 0.0
        area_busy = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_sum = 0.0
        served_count = 0
        customers_in_system = 0
        current_N = 0

        while True:
            if not queue and (service_end < 0 or service_end > H):
                if next_arr >= H:
                    break
                dt = next_arr - t
                if dt > 0:
                    area_N += current_N * dt
                    if busy:
                        area_busy += dt
                    t += dt
                # Arrival
                if len(queue) + (1 if busy else 0) < K:
                    queue.append(t)
                    arr_count += 1
                    current_N += 1
                    if not busy:
                        busy = True
                        svc_dur = rng.expovariate(mu)
                        service_end = t + svc_dur
                        dep_count += 1
                        served_count += 1
                        wait_sum += 0.0
                        # Start service immediately
                        # But we need to handle departure event properly
                        # Let's restructure with event list approach for clarity within constraints
                        pass
                else:
                    blk_count += 1
                    arr_count += 1
                next_arr = t + rng.expovariate(lam)
                continue

            # Determine next event time
            events = []
            if next_arr < H:
                events.append(('arr', next_arr))
            if service_end >= 0 and service_end < H:
                events.append(('dep', service_end))
            
            if not events:
                break
            
            min_type, min_t = min(events, key=lambda x: x[1])
            
            dt = min_t - t
            if dt > 0:
                area_N += current_N * dt
                if busy:
                    area_busy += dt
                t += dt

            if min_type == 'arr':
                if len(queue) + (1 if busy else 0) < K:
                    queue.append(t)
                    arr_count += 1
                    current_N += 1
                    if not busy:
                        busy = True
                        svc_dur = rng.expovariate(mu)
                        service_end = t + svc_dur
                        dep_count += 1
                        served_count += 1
                        wait_sum += 0.0
                else:
                    blk_count += 1
                    arr_count += 1
                next_arr = t + rng.expovariate(lam)
            elif min_type == 'dep':
                if queue:
                    arrival_time = queue.pop(0)
                    current_N -= 1
                    wait_sum += (t - arrival_time)
                    svc_dur = rng.expovariate(mu)
                    service_end = t + svc_dur
                    dep_count += 1
                    served_count += 1
                else:
                    busy = False
                    service_end = -1.0
                    current_N -= 1

        L_est = area_N / H if H > 0 else 0.0
        W_est = wait_sum / served_count if served_count > 0 else 0.0
        busy_frac_est = area_busy / H if H > 0 else 0.0
        p_loss_est = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_est = (served_count - sum(1 for _ in range(served_count))) # This logic is flawed for p_wait
        
        # Recalculate p_wait: fraction of served customers who waited
        # We didn't track individual waits well enough for exact count of waiters vs non-waiters easily without more state
        # Let's approximate or fix tracking. 
        # Actually, let's just use the ratio of waiting time to total time? No, p_wait is prob a customer waits.
        # Let's add a counter for customers who had wait > 0.
        
        # Re-run simulation logic with better tracking for p_wait
        # To keep code short, I'll adjust the loop above mentally but here I must output correct code.
        # Let's rewrite the inner loop slightly to track waiters.
        
        # Since I cannot edit previous lines, I will assume the provided structure needs to be robust.
        # Let's restart the generation with a cleaner single-pass implementation that fits constraints.
        
        # Resetting variables for final clean implementation below
        pass

    # The above draft has issues. Here is the corrected full implementation.
    
    import random, json, math, argparse

    def run_sim(seed, H, lam, mu, K):
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end = -1.0
        busy = False
        area_N = 0.0
        area_busy = 0.0
        arr_count = 0
        blk_count = 0
        dep_count = 0
        wait_sum = 0.0
        served_count = 0
        waiter_count = 0
        current_N = 0

        while True:
            events = []
            if next_arr < H:
                events.append(('arr', next_arr))
            if service_end >= 0 and service_end < H:
                events.append(('dep', service_end))
            
            if not events:
                break
            
            min_type, min_t = min(events, key=lambda x: x[1])
            dt = min_t - t
            if dt > 0:
                area_N += current_N * dt
                if busy:
                    area_busy += dt
                t += dt

            if min_type == 'arr':
                if len(queue) + (1 if busy else 0) < K:
                    queue.append(t)
                    arr_count += 1
                    current_N += 1
                    if not busy:
                        busy = True
                        svc_dur = rng.expovariate(mu)
                        service_end = t + svc_dur
                        dep_count += 1
                        served_count += 1
                        # Waited 0
                else:
                    blk_count += 1
                    arr_count += 1
                next_arr = t + rng.expovariate(lam)
            elif min_type == 'dep':
                if queue:
                    arrival_time = queue.pop(0)
                    current_N -= 1
                    w = t - arrival_time
                    wait_sum += w
                    if w > 1e-9:
                        waiter_count += 1
                    svc_dur = rng.expovariate(mu)
                    service_end = t + svc_dur
                    dep_count += 1
                    served_count += 1
                else:
                    busy = False
                    service_end = -1.0
                    current_N -= 1
        
        L = area_N / H if H > 0 else 0.0
        W_min = (wait_sum / served_count * 60.0) if served_count > 0 else 0.0
        bf = area_busy / H if H > 0 else 0.0
        pl = blk_count / arr_count if arr_count > 0 else 0.0
        pw = waiter_count / served_count if served_count > 0 else 0.0
        return L, W_min, bf, pl, pw, arr_count, blk_count, dep_count, served_count, area_busy

    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=1)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N = args.seeds
    H = args.horizon
    S = args.seed_start
    pert = args.pert

    lam_base = 6.0
    mu_base = 12.0
    K = 6

    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        lam = lam_base / 1.1
    elif pert == 'c_up':
        lam = lam_base
    else:
        lam = lam_base
    
    mu = mu_base

    results = []
    for i in range(N):
        res = run_sim(S+i, H, lam, mu, K)
        results.append(res)

    if not results:
        print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_loss":0,"runtime_units":"hour","seed_list":[],"seeds_used":0,"time_unit":"hour","win":H}))
        return

    avg_L = sum(r[0] for r in results) / N
    avg_W = sum(r[1] for r in results) / N
    avg_bf = sum(r[2] for r in results) / N
    avg_pl = sum(r[3] for r in results) / N
    avg_pw = sum(r[4] for r in results) / N
    avg_arr = sum(r[5] for r in results) / N
    avg_blk = sum(r[6] for r in results) / N
    avg_dep = sum(r[7] for r in results) / N
    avg_serv = sum(r[8] for r in results) / N
    
    dep_rate = avg_dep / H if H > 0 else 0.0
    lam_eff = avg_arr / H if H > 0 else 0.0
    busy_util = avg_bf # For M/M/1/c, E[min(N,c)]/c where c=1 is P(N>=1) which is busy_frac
    
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_bf, 6),
        "p_loss": round(avg_pl, 6),
        "runtime_units": "hour",
        "seed_list": [S+i for i in range(N)],
        "seeds_used": N,
        "time_unit": "hour",
        "win": H,
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(r[0], 6) for r in results],
        "per_seed_W": [round(r[1], 6) for r in results],
        "per_seed_busy_frac": [round(r[2], 6) for r in results],
        "per_seed_p_loss": [round(r[3], 6) for r in results],
        "per_seed_p_wait": [round(r[4], 6) for r in results]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
