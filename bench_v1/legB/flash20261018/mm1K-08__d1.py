import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 12.0
    K = 6
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL = []; pW = []; pB = []; pLoss = []; pWait = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area = 0.0
        area_busy = 0.0
        area_occ = 0.0
        arr = 0; dep = 0; blk = 0
        wait_sum = 0.0; wait_cnt = 0
        # event list: (time, type, patient)
        # type 0 arrival, 1 departure
        events = []
        # schedule first arrival
        t_next_arr = rng.expovariate(lam)
        events.append((t_next_arr, 0, None))
        # patients: dict id -> (arrival, service)
        pid = 0
        patients = {}
        # we need to track queue order for departures; use list of (dep_time, pid)
        # but service drawn at arrival
        # We'll process events in time order
        # Use a simple loop
        # For departure events, we need to know which patient departs
        # We'll store departure events as (time, 1, pid)
        # and patients dict pid -> (arrival, service)
        # When arrival occurs, if n < K: n+=1, draw service, schedule departure
        # else blk++
        # When departure occurs: n-=1, dep++, if n>0 schedule next? No, departures are scheduled at arrival.
        # Actually we schedule departure at arrival time + service.
        # So departure events are pre-scheduled.
        # We need to handle multiple departures possibly at same time? Exponential so prob 0.
        # We'll use a heap? But simple list sort is fine for small.
        # Let's use heapq for efficiency.
        import heapq
        heap = []
        heapq.heappush(heap, (t_next_arr, 0, -1))
        # We need to track current time and integrate area before state change
        # We'll process events in order
        # For area integration: area += n * (t - last_t)
        last_t = 0.0
        # We need to track busy: busy = 1 if n>0 else 0
        # area_busy += busy * (t - last_t)
        # area_occ += (1 if n>0 else 0) * (t - last_t)  # same as busy
        # Actually busy_frac = 1 - pi0 = fraction of time n>0
        # busy_util = E[min(n,c)]/c
        # We'll compute area_min_n = sum min(n,c) * dt
        area_min = 0.0
        # We need to track n at each interval
        # We'll process events until t > H
        # But we need to integrate up to H
        # We'll stop when next event time > H, then integrate remaining
        # We'll also need to handle warmup: only accumulate stats after warm
        # But area integration for busy_frac etc should be over window [warm, H]
        # We'll integrate from warm to H
        # We'll track last_t for integration, but only add to area if last_t >= warm
        # Actually we need to integrate from max(last_t, warm) to min(t, H)
        # We'll do that.
        # We'll also need to count arrivals, departures, blocks in window
        # We'll count if event time >= warm and <= H
        # For arrivals: if arrival time in [warm, H], arr++
        # For departures: if departure time in [warm, H], dep++
        # For blocks: if arrival time in [warm, H] and blocked, blk++
        # For wait: if arrival time in [warm, H] and not blocked, wait_sum += wait_time, wait_cnt++
        # Wait time = start_service - arrival. But we don't track start_service explicitly.
        # We can track when service starts: when patient enters service (n goes from 0 to 1? No, n includes in service)
        # Actually n is number in system (waiting + in service). When a patient arrives and n < K, they enter system.
        # If n == 0 before arrival, they start service immediately. Otherwise they wait.
        # We need to track start_service time for each patient.
        # We can store in patients dict: pid -> (arrival, service, start_service)
        # When arrival: if n == 0, start_service = arrival; else start_service = None (will be set when previous departs)
        # But we need to know when service starts for waiting patients.
        # We can maintain a queue of waiting patients (FIFO). When a departure occurs, if queue not empty, pop next, set start_service = departure time, schedule departure at start_service + service.
        # But we already scheduled departure at arrival time + service? No, we should schedule departure when service starts.
        # The requirement says: service time must be drawn at arrival and attached to patient. It doesn't say departure must be scheduled at arrival.
        # So we can draw service at arrival, store it, and schedule departure when service starts.
        # That's fine.
        # So we need a queue of waiting patients (pid list).
        # When arrival: draw service, store. If n == 0: start_service = arrival, schedule departure at arrival + service. n=1.
        # else: n+=1, add to queue.
        # When departure: n-=1, dep++. If queue not empty: pop pid, start_service = departure time, schedule departure at start_service + service. n+=1? Wait, n already decreased. Actually n is number in system. When departure, one leaves, so n-=1. Then if queue not empty, one starts service, so n stays same? No, n is number in system (waiting + in service). When one departs, n decreases by 1. Then if queue not empty, one moves from waiting to service, so n remains same? Actually n is total in system. Departure reduces n by 1. Starting service doesn't change n. So n stays decreased. But we need to schedule departure for the new service. So n is correct.
        # Let's be careful: n = number in system. Arrival: if n < K: n+=1, if n==1 (was 0) start service immediately, schedule departure. else add to queue.
        # Departure: n-=1. If queue not empty: pop, start service, schedule departure. (n unchanged? No, n already decreased. The patient was in queue, now in service, so n is same? Actually n counts both waiting and in service. When one departs, n decreases by 1. When one starts service, they were already counted in n (as waiting), so n doesn't change. So n remains decreased. That's correct.)
        # So n after departure and starting next service is n-1 (if queue was nonempty) or n-1 (if empty). So n decreases by 1 each departure.
        # But wait: if queue was nonempty, the departing patient leaves, n decreases by 1. The next patient starts service, but they were already in n (as waiting). So n is still decreased by 1. So n = previous n - 1. That's correct.
        # So we don't need to adjust n when starting service.
        # So departure event: n -= 1; dep++; if queue: pop, start_service = t, schedule departure at t + service.
        # That's it.
        # We need to track queue as list of pids.
        # We need patients dict: pid -> (arrival, service, start_service)
        # We'll use pid counter.
        # Let's implement.
        # We'll use heapq for events: (time, type, pid) where type 0 arrival, 1 departure.
        # For arrival, pid = -1 (we'll assign new pid).
        # For departure, pid is the patient id.
        # We'll process events in order.
        # We'll also need to handle the case where multiple events at same time? Exponential so prob 0.
        # We'll use a while loop.
        # We'll integrate area before processing each event.
        # We'll stop when next event time > H, then integrate to H.
        # We'll also need to handle warmup: we only accumulate stats if event time >= warm.
        # But area integration: we integrate from max(last_t, warm) to min(t, H).
        # We'll do that.
        # Let's code.
        # We'll use a list for queue (FIFO).
        # We'll use a dict for patients.
        # We'll use a heap for events.
        # We'll use a variable n for number in system.
        # We'll use a variable last_t for integration.
        # We'll use variables for stats.
        # Let's start.
        # We need to schedule first arrival.
        # We already have t_next_arr.
        # We'll push (t_next_arr, 0, -1) to heap.
        # We'll also need to handle the case where H is very small.
        # We'll process until heap empty or next event time > H.
        # But we need to integrate up to H.
        # We'll do:
        # while heap and heap[0][0] <= H:
        #   t, typ, pid = heappop(heap)
        #   # integrate from last_t to t
        #   if t > last_t:
        #       dt = t - last_t
        #       # only accumulate if last_t >= warm? Actually we need to integrate from max(last_t, warm) to min(t, H)
        #       # but t <= H here.
        #       # We'll compute overlap with [warm, H]
        #       lo = max(last_t, warm)
        #       hi = min(t, H)
        #       if hi > lo:
        #           dt_win = hi - lo
        #           area += n * dt_win
        #           area_min += min(n, K) * dt_win
        #           if n > 0:
        #               area_busy += dt_win
        #       last_t = t
        #   # process event
        #   if typ == 0: # arrival
        #       # count if in window
        #       if t >= warm and t <= H:
        #           arr += 1
        #       if n < K:
        #           # accept
        #           pid_new = pid_counter
        #           pid_counter += 1
        #           service = rng.expovariate(mu)
        #           patients[pid_new] = [t, service, None]
        #           if n == 0:
        #               # start service immediately
        #               patients[pid_new][2] = t
        #               heappush(heap, (t + service, 1, pid_new))
        #           else:
        #               queue.append(pid_new)
        #           n += 1
        #       else:
        #           # blocked
        #           if t >= warm and t <= H:
        #               blk += 1
        #       # schedule next arrival
        #       t_next = t + rng.expovariate(lam)
        #       heappush(heap, (t_next, 0, -1))
        #   else: # departure
        #       # count if in window
        #       if t >= warm and t <= H:
        #           dep += 1
        #       n -= 1
        #       # if queue not empty, start next service
        #       if queue:
        #           pid_next = queue.pop(0)
        #           patients[pid_next][2] = t
        #           heappush(heap, (t + patients[pid_next][1], 1, pid_next))
        #       # else n remains decreased
        #   # end event
        # # after loop, integrate from last_t to H
        # if H > last_t:
        #   lo = max(last_t, warm)
        #   hi = H
        #   if hi > lo:
        #       dt_win = hi - lo
        #       area += n * dt_win
        #       area_min += min(n, K) * dt_win
        #       if n > 0:
        #           area_busy += dt_win
        #   last_t = H
        # # Now compute stats
        # win = H - warm
        # L = area / win if win > 0 else 0
        # busy_frac = area_busy / win if win > 0 else 0
        # busy_util = area_min / (K * win) if win > 0 else 0
        # p_loss = blk / arr if arr > 0 else 0
        # # W: average wait time for accepted patients in window
        # # We need to compute wait times for patients who arrived in window and were accepted.
        # # We have patients dict with arrival, service, start_service.
        # # We can iterate over patients and check if arrival in [warm, H] and start_service is not None.
        # # But we need to be careful: some patients may have arrived in window but not yet started service by H? They are still waiting. Their wait time is not complete. We should only include those who started service by H? Or include all accepted? The problem says W is average waiting time. Typically we include all patients who completed waiting (i.e., started service) within the window? Or all accepted patients? The standard is to include all patients who arrived in window and eventually started service (even if after H). But we only simulate up to H. So we might not have start_service for some. We can include only those with start_service <= H? Or include all with start_service not None? Since we simulate until H, any patient who started service after H is not simulated. So we only have start_service for those who started by H. So we can include those with start_service is not None and arrival in [warm, H]. That's fine.
        # # Alternatively, we can compute wait time as start_service - arrival for those with start_service not None and arrival in [warm, H].
        # # Let's do that.
        # wait_sum = 0.0
        # wait_cnt = 0
        # for pid, (arr_t, serv, start_t) in patients.items():
        #   if arr_t >= warm and arr_t <= H and start_t is not None:
        #       wait_sum += start_t - arr_t
        #       wait_cnt += 1
        # W = wait_sum / wait_cnt if wait_cnt > 0 else 0
        # p_wait = wait_cnt / arr if arr > 0 else 0  # but wait_cnt is number who started service, not number who waited. Actually p_wait is probability that an accepted patient waits > 0. We can compute as number of accepted patients with start_t > arr_t divided by number of accepted patients. But we need to be careful: some accepted patients may not have started service by H. We can compute p_wait as (number of accepted patients with start_t > arr_t) / (number of accepted patients with start_t not None? or all accepted?). The problem says p_wait is probability of waiting. Typically it's P(wait > 0) for accepted patients. We can compute as (wait_cnt - immediate_cnt) / wait_cnt? Actually immediate_cnt = number with start_t == arr_t. So p_wait = 1 - immediate_cnt/wait_cnt. But we need to include only those who started service. Let's do that.
        # # Let's compute immediate_cnt.
        # immediate_cnt = 0
        # for pid, (arr_t, serv, start_t) in patients.items():
        #   if arr_t >= warm and arr_t <= H and start_t is not None:
        #       if start_t == arr_t:
        #           immediate_cnt += 1
        # p_wait = 1 - immediate_cnt / wait_cnt if wait_cnt > 0 else 0
        # # But wait_cnt is number who started service. That's fine.
        # # Now we need to store per-seed values.
        # pL.append(L)
        # pW.append(W)
        # pB.append(busy_frac)
        # pLoss.append(p_loss)
        # pWait.append(p_wait)
        # # accumulate totals for overall averages
        # tot_arr += arr
        # tot_dep += dep
        # tot_blk += blk
        # # We also need to accumulate area, area_busy, area_min for overall? But overall L is average of per-seed L? Or we can compute overall L as average of per-seed L. The problem says per_seed_* are individual estimates. The overall L, W, etc. should be the average over seeds? Or computed from pooled data? Typically we
