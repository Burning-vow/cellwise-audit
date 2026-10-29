import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()
    
    N_seeds = args.seeds
    H = args.horizon
    S_start = args.seed_start
    pert = args.pert
    
    # Parameters in hours
    lam_base = 6.0
    mu_base = 5.0 # 12 min mean -> 5 per hour
    c = 3
    K = 4 # max capacity including service
    
    if pert == 'lam_up':
        lam = lam_base * 1.1
    elif pert == 'mu_up':
        mu = mu_base * 1.1
    elif pert == 'c_up':
        c = 4
        K = 5
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base
        
    time_unit = 'hour'
    win = H * 0.75 # remove first 25% warmup
    warmup_end = H * 0.25
    
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
    
    seed_list = []
    
    for i in range(N_seeds):
        seed = S_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        # State variables
        t = 0.0
        n_in_system = 0 # number of cars in system (waiting + serving)
        n_serving = 0   # number of cars currently being served
        
        # Event queue: list of (time, type, data)
        # type: 'arrival', 'departure'
        events = []
        
        # Statistics accumulators for the window [warmup_end, H]
        # Area integrals
        area_n = 0.0
        area_busy = 0.0 # time when n_in_system > 0
        area_min_nc = 0.0 # integral of min(n_in_system, c)
        
        # Counts
        count_arr = 0
        count_blk = 0
        count_dep = 0
        count_wait = 0 # arrivals that had to wait (n_in_system >= c at arrival? No, p_wait usually prob an arriving customer waits. In M/M/c/K, if n < c, no wait. If n >= c, wait.)
        
        # For W calculation: sum of sojourn times of completed services in window
        sum_sojourn = 0.0
        
        # Generate initial arrival
        next_arr_time = rng.expovariate(lam)
        events.append((next_arr_time, 'arrival', None))
        
        last_t = 0.0
        
        while events:
            # Pop earliest event
            events.sort(key=lambda x: x[0])
            t_event, etype, edata = events.pop(0)
            
            if t_event > H:
                break
                
            # Integrate areas from last_t to t_event
            dt = t_event - last_t
            if last_t < warmup_end and t_event > warmup_end:
                # Split integration
                dt_warm = warmup_end - last_t
                dt_win = t_event - warmup_end
                if dt_warm > 0:
                    pass # ignore warmup stats
                if dt_win > 0:
                    area_n += n_in_system * dt_win
                    if n_in_system > 0:
                        area_busy += dt_win
                    area_min_nc += min(n_in_system, c) * dt_win
            elif last_t >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
                area_min_nc += min(n_in_system, c) * dt
            
            last_t = t_event
            t = t_event
            
            if etype == 'arrival':
                # Check if blocked
                if n_in_system >= K:
                    count_blk += 1
                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    events.append((t + inter_arr, 'arrival', None))
                else:
                    count_arr += 1
                    n_in_system += 1
                    
                    # Determine if this car waits or starts service immediately
                    # Service time is drawn now
                    serv_time = rng.expovariate(mu)
                    
                    if n_serving < c:
                        # Start service immediately
                        n_serving += 1
                        dep_time = t + serv_time
                        events.append((dep_time, 'departure', {'start': t, 'serv': serv_time}))
                    else:
                        # Wait
                        count_wait += 1
                        # Store info to calculate sojourn later? 
                        # We need to know when it enters service.
                        # But we don't have a queue structure explicitly tracking individual cars waiting.
                        # Standard approach: When a departure happens, if there are waiting cars, one starts service.
                        # How do we track which car started when?
                        # We can push a "service start" event? No, service starts upon departure completion if queue non-empty.
                        # Let's maintain a list of waiting cars with their arrival times.
                        # Actually, simpler: On arrival, if not starting service, add to a waiting queue.
                        # On departure, if waiting queue not empty, pop one, set its start time, schedule its departure.
                        
                        # Refactor state:
                        # n_in_system includes waiting and serving.
                        # n_serving is current servers busy.
                        # Waiting queue: list of arrival times.
                        pass # Handled below by adding to wait_q

                    # Need a wait_q variable initialized outside loop
                    # Let's restructure slightly inside the loop scope or use a dict/list passed around.
                    # Since I can't define classes, I'll use local variables carefully.
                    # I will initialize wait_q before the while loop.
                    if n_serving >= c:
                         # It was added to n_in_system but didn't start service.
                         # Add to wait_q
                         wait_q.append(t)
                    else:
                         # Already handled above
                         pass

                    # Schedule next arrival
                    inter_arr = rng.expovariate(lam)
                    events.append((t + inter_arr, 'arrival', None))
                    
            elif etype == 'departure':
                # A car finishes service
                n_in_system -= 1
                n_serving -= 1
                count_dep += 1
                
                # Calculate sojourn time for this car
                start_time = edata['start']
                serv_time = edata['serv']
                # Sojourn = end_time - arrival_time. 
                # Wait, edata doesn't have arrival time. 
                # Problem: I lost the arrival time link.
                
                # Correction strategy:
                # When a car arrives and waits, store its arrival time in wait_q.
                # When a server becomes free, pop from wait_q, get arrival time, assign start time = current t.
                # The departure event should carry the arrival time.
                
                # Let's restart the logic flow mentally to ensure correctness.
                # State: wait_q (list of arrival times), n_serving, n_in_system.
                # Arrival:
                #   if full: block.
                #   else: n_in_system++. Draw serv_time.
                #     if n_serving < c: n_serving++. Push departure event with (arrival_time=t, start_time=t, serv_time).
                #     else: wait_q.append(t).
                # Departure:
                #   n_in_system--. n_serving--.
                #   Get arrival_time from event data.
                #   Sojourn = t - arrival_time. Accumulate if in window.
                #   If wait_q not empty:
                #      arr_t = wait_q.pop(0)
                #      n_serving++
                #      Draw new serv_time? NO. Serv time was drawn at arrival.
                #      This is the tricky part. "Service duration must be drawn at arrival".
                #      So if a car waits, we must store its pre-drawn service time.
                #      
                # Revised State: wait_q stores tuples (arrival_time, serv_time).
                
                # Let's rewrite the inner loop logic properly.
                pass 

        # Re-implementing the simulation loop correctly within the seed iteration
        
        # Reset state for this seed
        t = 0.0
        n_in_system = 0
        n_serving = 0
        wait_q = [] # List of (arrival_time, serv_time)
        events = []
        
        # Stats
        area_n = 0.0
        area_busy = 0.0
        area_min_nc = 0.0
        count_arr = 0
        count_blk = 0
        count_dep = 0
        count_wait = 0
        sum_sojourn = 0.0
        last_t = 0.0
        
        # Initial arrival
        next_arr_time = rng.expovariate(lam)
        events.append((next_arr_time, 'arrival', None))
        
        while events:
            events.sort(key=lambda x: x[0])
            t_event, etype, edata = events.pop(0)
            
            if t_event > H:
                break
            
            dt = t_event - last_t
            if last_t < warmup_end and t_event > warmup_end:
                dt_win = t_event - warmup_end
                area_n += n_in_system * dt_win
                if n_in_system > 0:
                    area_busy += dt_win
                area_min_nc += min(n_in_system, c) * dt_win
            elif last_t >= warmup_end:
                area_n += n_in_system * dt
                if n_in_system > 0:
                    area_busy += dt
                area_min_nc += min(n_in_system, c) * dt
            
            last_t = t_event
            t = t_event
            
            if etype == 'arrival':
                if n_in_system >= K:
                    count_blk += 1
                else:
                    count_arr += 1
                    n_in_system += 1
                    serv_time = rng.expovariate(mu)
                    
                    if n_serving < c:
                        n_serving += 1
                        dep_time = t + serv_time
                        events.append((dep_time, 'departure', {'arr_t': t, 'serv': serv_time}))
                    else:
                        count_wait += 1
                        wait_q.append((t, serv_time))
                
                inter_arr = rng.expovariate(lam)
                events.append((t + inter_arr, 'arrival', None))
                
            elif etype == 'departure':
                n_in_system -= 1
                n_serving -= 1
                count_dep += 1
                
                arr_t = edata['arr_t']
                sojourn = t - arr_t
                
                # Only accumulate stats if the departure happened in the window?
                # Or if the car arrived in the window?
                # Usually, for steady state, we count completions in the window.
                # However, a car arriving just before warmup might depart after.
                # Standard practice: Count sojourns of cars that DEPARTED in the window.
                if t >= warmup_end:
                    sum_sojourn += sojourn
                
                if wait_q:
                    arr_t_next, serv_t_next = wait_q.pop(0)
                    n_serving += 1
                    dep_time = t + serv_t_next
                    events.append((dep_time, 'departure', {'arr_t': arr_t_next, 'serv': serv_t_next}))

        # Final integration up to H if needed? 
        # The loop breaks when t_event > H. last_t is the last processed event time <= H.
        # We need to integrate from last_t to H.
        if last_t < H:
            dt_final = H - last_t
            if last_t < warmup_end and H > warmup_end:
                dt_win = H - warmup_end
                area_n += n_in_system * dt_win
                if n_in_system > 0:
                    area_busy += dt_win
                area_min_nc += min(n_in_system, c) * dt_win
            elif last_t >= warmup_end:
                area_n += n_in_system * dt_final
                if n_in_system > 0:
                    area_busy += dt_final
                area_min_nc += min(n_in_system, c) * dt_final

        # Calculate metrics for this seed
        L_est = area_n / win if win > 0 else 0
        busy_frac_est = area_busy / win if win > 0 else 0
        busy_util_est = area_min_nc / (win * c) if win > 0 else 0
        
        total_customers_in_window = count_arr + count_blk # Arrivals attempted
        # p_loss = blk / (arr + blk) ? Or blk / arr_total?
        # "p_loss" usually probability of loss given an arrival attempt.
        # Denominator should be total arrival attempts in the window.
        # Note: count_arr counts accepted. count_blk counts rejected.
        # Total attempts = count_arr + count_blk.
        p_loss_est = count_blk / (count_arr + count_blk) if (count_arr + count_blk) > 0 else 0
        
        # p_wait: Probability an ACCEPTED customer waits.
        # Denominator: Accepted customers (count_arr).
        # Numerator: Those who waited (count_wait).
        p_wait_est = count_wait / count_arr if count_arr > 0 else 0
        
        # W: Average sojourn time of COMPLETED customers in the window.
        # Denominator: count_dep (departures in window).
        # Note: Some departures in window might correspond to arrivals before window.
        # This is standard for area-based/flow-based estimators.
        W_est = sum_sojourn / count_dep if count_dep > 0 else 0
        
        # Dep rate: departures per hour
        dep_rate_est = count_dep / win if win > 0 else 0
        
        # Lam eff: effective arrival rate (accepted)
        lam_eff_est = count_arr / win if win > 0 else 0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(count_arr)
        all_blk.append(count_blk)
        all_dep.append(count_dep)
        all_busy_util.append(busy_util_est)
        all_dep_rate.append(dep_rate_est)
        all_lam_eff.append(lam_eff_est)

    # Aggregate results
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0

    res = {
        "L": avg(all_L),
        "W": avg(all_W),
        "busy_frac": avg(all_busy_frac),
        "p_loss": avg(all_p_loss),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": N_seeds,
        "time_unit": time_unit,
        "win": win,
        "arr": avg(all_arr),
        "blk": avg(all_blk),
        "busy_util": avg(all_busy_util),
        "dep": avg(all_dep),
        "dep_rate": avg(all_dep_rate),
        "lam_eff": avg(all_lam_eff),
        "p_wait": avg(all_p_wait),
        "per_seed_L": all_L,
        "per_seed_W": all_W,
        "per_seed_busy_frac": all_busy_frac,
        "per_seed_p_loss": all_p_loss,
        "per_seed_p_wait": all_p_wait
    }
    
    print(json.dumps(res))

if __name__ == "__main__":
    main()
