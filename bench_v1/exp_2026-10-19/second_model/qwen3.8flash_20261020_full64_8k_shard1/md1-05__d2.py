import random, json, argparse, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=100.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    N_seeds = args.seeds
    H = args.horizon
    seed_start = args.seed_start
    pert = args.pert

    lam_base = 8.0
    mu_base = 10.0
    c_base = 1

    if pert == 'lam_up':
        lam = lam_base * 1.2
    elif pert == 'mu_up':
        mu = mu_base * 1.2
    elif pert == 'c_up':
        c = c_base + 1
    else:
        lam = lam_base
        mu = mu_base
        c = c_base

    time_unit = "hour"
    win = H * 0.75
    warmup = H * 0.25

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
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seeds_used_list = []

    for i in range(N_seeds):
        s = seed_start + i
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end_times = []
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        total_time_in_system = 0.0
        area_N = 0.0
        last_event_time = 0.0
        current_N = 0
        busy_periods_area = 0.0
        occupied_periods_area = 0.0
        wait_count = 0
        loss_count = 0
        arr_count_total = 0
        dep_count_total = 0

        while t < H:
            if not queue and not service_end_times:
                if next_arr > H:
                    break
                t = next_arr
                next_arr += rng.expovariate(lam)
                if t >= warmup:
                    arrivals_in_window += 1
                arr_count_total += 1
                if len(service_end_times) < c:
                    service_time = 6.0 / 60.0
                    end_t = t + service_time
                    service_end_times.append(end_t)
                    queue.append((t, end_t))
                else:
                    blocked_in_window += 1 if t >= warmup else 0
                    loss_count += 1
                continue

            events = []
            if next_arr <= H:
                events.append(('arr', next_arr))
            if service_end_times:
                min_serv = min(service_end_times)
                if min_serv <= H:
                    events.append(('dep', min_serv))
            
            if not events:
                break
            
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]

            dt = etime - last_event_time
            if last_event_time >= warmup:
                area_N += current_N * dt
                busy_periods_area += (min(current_N, c) / c) * dt if c > 0 else 0
                occupied_periods_area += (1 if current_N > 0 else 0) * dt
            last_event_time = etime

            if etype == 'arr':
                t = etime
                next_arr += rng.expovariate(lam)
                if t >= warmup:
                    arrivals_in_window += 1
                arr_count_total += 1
                if len(service_end_times) < c:
                    service_time = 6.0 / 60.0
                    end_t = t + service_time
                    service_end_times.append(end_t)
                    queue.append((t, end_t))
                    current_N += 1
                else:
                    if t >= warmup:
                        blocked_in_window += 1
                    loss_count += 1
            elif etype == 'dep':
                t = etime
                idx = service_end_times.index(t)
                start_t, end_t = queue.pop(idx)
                service_end_times.pop(idx)
                current_N -= 1
                if t >= warmup:
                    departures_in_window += 1
                    total_time_in_system += (end_t - start_t)
                    if start_t < end_t - 6.0/60.0: 
                        pass
                    # Check if waited: arrival time vs service start time
                    # In this simple FCFS with single server or parallel servers, 
                    # we need to track when service actually started.
                    # My model above assumes immediate service if slot available.
                    # If slot not available, it's blocked. So no waiting queue?
                    # Problem says "先到先洗", implies a queue might form if c>1 or if we allow waiting.
                    # But standard M/M/c/K or M/M/c with infinite buffer allows waiting.
                    # The prompt says "blocked/rejected". This suggests finite capacity or blocking after delay?
                    # "自动洗车机... 车辆按泊松流到达... 请给出稳态平均停留时间 W ... 与场内平均车辆数 L"
                    # Usually, if it's a single machine, cars wait in line.
                    # Let's re-read carefully: "blk 是窗口内平均每种子被拒绝/丢失的人数".
                    # If there is an infinite queue, blk should be 0.
                    # If there is a finite capacity, blk > 0.
                    # The problem doesn't specify capacity limit explicitly other than the machine itself.
                    # However, typical discrete event sim problems with "blocked" imply a system capacity.
                    # Let's assume infinite queue first, then check if blk makes sense.
                    # If infinite queue, p_loss = 0.
                    # Let's look at parameters: lam=8/hr, mu=10/hr (6min). rho=0.8. Stable.
                    # If infinite queue, L = rho/(1-rho) = 4, W = 1/(mu-lam) = 0.5 hr = 30 min.
                    # If finite capacity K, then losses occur.
                    # The prompt asks for "p_loss". If it's always 0, that's fine.
                    # But let's implement a general queue where cars wait.
                    
                    # Correction on logic:
                    # I used `queue` list to store (arrival_time, scheduled_end_time).
                    # When a car arrives, if slots < c, it starts immediately.
                    # If slots >= c, it is BLOCKED (lost).
                    # This means NO WAITING QUEUE. Capacity = c.
                    # Is this correct? "先到先洗" usually implies waiting.
                    # But "blk" field exists. If waiting was allowed, blk would be 0 unless capacity is limited.
                    # Given "auto car wash", often there's space for only one car.
                    # Let's stick to Capacity = c (no waiting room).
                    # If waiting room was intended, problem would likely specify max queue length.
                    # With C=c, rho=0.8, P(loss) = P(N=c) = rho^c(1-rho)/(1-rho^(c+1)). For c=1, P(loss)=rho^2/(1+rho)? No.
                    # M/M/1/1: P0 = 1/(1+rho), P1 = rho/(1+rho). Loss prob = P1 = rho/(1+rho) = 0.8/1.8 = 0.44.
                    # Wait, if c=1, and car arrives when busy, it leaves.
                    # Effective lambda = lam * (1 - P_loss).
                    # Let's verify this interpretation.
                    # If this is wrong, and waiting is allowed, then blk=0.
                    # Let's assume standard M/M/c with infinite buffer first?
                    # But then why ask for blk?
                    # Maybe "blk" is just 0.
                    # Let's try implementing Infinite Buffer M/M/c.
                    # If Infinite Buffer:
                    # Arrivals join queue. Service starts when server free.
                    # Blocked/Lost = 0.
                    # Let's switch to Infinite Buffer model as it's more common for "W" and "L" questions unless capacity specified.
                    # BUT, the prompt specifically lists "blk" and "p_loss".
                    # If I implement infinite buffer, blk=0, p_loss=0.
                    # If I implement finite buffer (cap=c), blk>0.
                    # Let's look at "busy_frac" definition: E[min(N,c)]/c.
                    # If N can exceed c (waiting), min(N,c) is still c.
                    # If N cannot exceed c (blocking), N <= c.
                    # Both work.
                    # However, "W" (sojourn time) includes waiting time.
                    # If blocking, W is just service time for those served.
                    # If waiting, W = wait + service.
                    # Standard Little's Law applies to both.
                    # Given the ambiguity, and the explicit request for "blk", I will implement a system with **infinite waiting room** but report blk=0/p_loss=0 if no blocking occurs, OR implement a finite capacity.
                    # Actually, most "car wash" simulations assume you can wait.
                    # Let's assume Infinite Queue. Then blk=0.
                    # Why would they ask for blk? To check if you implemented blocking incorrectly? Or maybe the system IS blocking?
                    # "自动洗车机" -> Single bay. Cars arrive. If bay full, do they leave or wait?
                    # Real world: They wait.
                    # Sim world: Often modeled as M/M/1.
                    # Let's go with M/M/c Infinite Buffer.
                    # Then blk = 0, p_loss = 0.
                    # But wait, if I change my code structure now...
                    # Current code: if len(service_end_times) < c: serve, else block.
                    # This is Finite Capacity = c.
                    # Let's keep Finite Capacity = c because it generates non-zero blk, making the stats more interesting/testable.
                    # Also, "busy_frac" = E[min(N,c)]/c. If N<=c always, min(N,c)=N.
                    # If N>c, min(N,c)=c.
                    # If I use Infinite Buffer, N can be > c.
                    # If I use Finite Buffer, N <= c.
                    # The prompt doesn't specify capacity.
                    # However, "p_loss" is requested. If it's always 0, it's trivial.
                    # I will stick to the Finite Capacity (Blocking) model as implemented in the draft, assuming capacity = number of servers.
                    # This matches "M/M/c/c" (Erlang-C is waiting, Erlang-B is blocking).
                    # M/M/c/c is a common model for systems with no queue.
                    
                    # Re-evaluating based on "W" and "L".
                    # If M/M/1/1: L = P1 = rho/(1+rho). W = 1/mu (for served customers).
                    # If M/M/1: L = rho/(1-rho). W = 1/(mu-lam).
                    # Which one is "Auto Car Wash"?
                    # Usually, you drive up, if empty, enter. If full, you wait in line.
                    # So M/M/1 (Infinite Queue) is more realistic.
                    # If so, blk=0.
                    # I will implement Infinite Queue.
                    # Change logic:
                    # If server free, start service.
                    # Else, add to queue.
                    # Departure: remove from service, take from queue if any.
                    # Blocked: Never happens (unless max queue size defined, which isn't).
                    # So blk=0, p_loss=0.
                    
                    # Let's rewrite the loop for Infinite Queue.
                    pass

        # Resetting logic for Infinite Queue
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] # List of arrival times waiting for service
        service_end_times = [] # List of end times for currently serving cars
        # We also need to know when each car STARTED service to calculate wait time properly?
        # Or just store (arrival_time, start_time, end_time) for completed ones?
        # Better: Store (arrival_time, start_time) in a dict/list for active services.
        
        active_services = [] # List of dicts: {'start': t, 'end': t}
        waiting_queue = [] # List of arrival times
        
        arrivals_in_window = 0
        departures_in_window = 0
        blocked_in_window = 0
        total_time_in_system = 0.0
        area_N = 0.0
        last_event_time = 0.0
        current_N = 0 # Total in system (waiting + serving)
        busy_periods_area = 0.0
        occupied_periods_area = 0.0
        wait_count = 0 # Number of customers who waited (start > arrival)
        loss_count = 0
        
        # Initialize
        # Event loop
        while True:
            # Determine next event time
            candidates = []
            if next_arr <= H:
                candidates.append(next_arr)
            if active_services:
                min_end = min([a['end'] for a in active_services])
                if min_end <= H:
                    candidates.append(min_end)
            
            if not candidates:
                break
            
            next_t = min(candidates)
            dt = next_t - last_event_time
            
            # Integrate areas
            if last_event_time >= warmup:
                area_N += current_N * dt
                busy_periods_area += (min(current_N, c) / c) * dt if c > 0 else 0
                occupied_periods_area += (1 if current_N > 0 else 0) * dt
            
            last_event_time = next_t
            t = next_t
            
            # Process events at time t
            # Handle Departures first (to free up servers for new arrivals at same time?)
            # Standard convention: Dep before Arr if simultaneous? Or Arr before Dep?
            # Usually, if a car finishes at t and another arrives at t, the arriving car can take the spot.
            # So process Deps first.
            
            departed_indices = [i for i, a in enumerate(active_services) if abs(a['end'] - t) < 1e-9]
            for i in sorted(departed_indices, reverse=True):
                cust = active_services.pop(i)
                current_N -= 1
                if t >= warmup:
                    departures_in_window += 1
                    total_time_in_system += (cust['end'] - cust['arrival'])
                    if cust['start'] > cust['arrival']:
                        wait_count += 1
            
            # Handle Arrival
            if abs(next_arr - t) < 1e-9:
                if t >= warmup:
                    arrivals_in_window += 1
                # Add to waiting queue initially
                waiting_queue.append({'arrival': t})
                current_N += 1
                next_arr += rng.expovariate(lam)
                
                # Try to assign servers
                while len(active_services) < c and waiting_queue:
                    cust = waiting_queue.pop(0)
                    service_time = 6.0 / 60.0
                    start_t = t
                    end_t = t + service_time
                    active_services.append({
                        'arrival': cust['arrival'],
                        'start': start_t,
                        'end': end_t
                    })
            
            # Check for blocking? Infinite queue -> no blocking.
            # blocked_in_window remains 0.

        # End of simulation for seed s
        
        # Calculate stats for this seed
        # Note: Area integration stopped at last_event_time. 
        # If last_event_time < H, we missed the tail.
        # The loop breaks when no events <= H.
        # We should integrate until H.
        if last_event_time < H:
            dt_tail = H - last_event_time
            if last_event_time >= warmup:
                area_N += current_N * dt_tail
                busy_periods_area += (min(current_N, c) / c) * dt_tail if c > 0 else 0
                occupied_periods_area += (1 if current_N > 0 else 0) * dt_tail
            last_event_time = H

        # Finalize counts
        # Some customers might have arrived but not departed by H.
        # They are in system.
        # L estimate = area_N / win
        # W estimate = total_time_in_system / departures_in_window (if dep>0)
        # p_loss = blocked_in_window / arrivals_in_window (if arr>0)
        # p_wait = wait_count / departures_in_window (approx, among those who left)
        # Or wait_count / arrivals_in_window? Usually fraction of ALL customers who waited.
        # Let's use wait_count / arrivals_in_window for p_wait?
        # Prompt: "p_wait". Ambiguous. Usually probability an arriving customer waits.
        # Since we don't know future for those still in system, we approximate using departed ones or assume steady state.
        # Let's use wait_count / departures_in_window as proxy for conditional prob, or better:
        # Count how many ARRIVALS had to wait.
        # We tracked wait_count on DEPARTURE.
        # Customers still in system at H: if they are in waiting_queue, they waited. If in active_services, they didn't wait (started immediately).
        # So:
        # Total Arrivals = arrivals_in_window
        # Total Waiters = wait_count (from departed) + len(waiting_queue) (still waiting)
        # p_wait = Total Waiters / Total Arrivals
        
        total_waiters = wait_count + len(waiting_queue)
        
        est_L = area_N / win if win > 0 else 0
        est_W = total_time_in_system / departures_in_window if departures_in_window > 0 else 0
        est_busy_frac = busy_periods_area / win if win > 0 else 0
        est_p_loss = blocked_in_window / arrivals_in_window if arrivals_in_window > 0 else 0
        est_p_wait = total_waiters / arrivals_in_window if arrivals_in_window > 0 else 0
        est_busy_util = busy_periods_area / win if win > 0 else 0 # Same as busy_frac for c=1?
        # busy_util = E[min(N,c)]/c. busy_frac defined as E[min(N,1)]/1.
        # If c=1, they are same.
        # If c>1, busy_util is utilization.
        # busy_occupied = 1 - pi0 = P(N>0).
        est_busy_occupied = occupied_periods_area / win if win > 0 else 0
        
        per_seed_L.append(est_L)
        per_seed_W.append(est_W)
        per_seed_busy_frac.append(est_busy_frac)
        per_seed_p_loss.append(est_p_loss)
        per_seed_p_wait.append(est_p_wait)
        
        all_L.append(est_L)
        all_W.append(est_W)
        all_busy_frac.append(est_busy_frac)
        all_p_loss.append(est_p_loss)
        all_p_wait.append(est_p_wait)
        all_arr.append(arrivals_in_window)
        all_dep.append(departures_in_window)
        all_blk.append(blocked_in_window)
        all_busy_util.append(est_busy_util)
        all_busy_occupied.append(est_busy_occupied)
        seeds_used_list.append(s)

    avg_L = sum(all_L) / len(all_L) if all_L else 0
    avg_W = sum(all_W) / len(all_W) if all_W else 0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0
    avg_busy_occupied = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0
    
    dep_rate = avg_dep / win if win > 0 else 0
    lam_eff = dep_rate # In stable system, eff arrival rate = departure rate
    
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "runtime_units": "hours",
        "seed_list": seeds_used_list,
        "seeds_used": len(seeds_used_list),
        "time_unit": time_unit,
        "win": round(win, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(avg_busy_occupied, 6)
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
