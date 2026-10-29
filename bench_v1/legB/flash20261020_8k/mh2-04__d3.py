import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0 / 60.0
    mu = 1.0 / 6.0
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    # two-phase hyperexponential matching mean 1/mu and cv
    # cv^2 = 1 + p*(1-p)*(r1-r2)^2/(...) ; use balanced means
    c2 = cv * cv
    if c2 <= 1.0:
        p1 = 0.5
        r1 = r2 = mu
    else:
        p1 = 0.5 * (1.0 + math.sqrt((c2 - 1.0) / (c2 + 1.0)))
        r1 = 2.0 * p1 * mu
        r2 = 2.0 * (1.0 - p1) * mu

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy_area = 0.0
    tot_sys_area = 0.0
    tot_wait_area = 0.0
    tot_waiters_area = 0.0
    tot_n = 0.0
    tot_wait_n = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        # event list: we simulate arrival by arrival
        arr_times = []
        # generate arrivals lazily
        t_arr = rng.expovariate(lam)
        # state: queue of (arrival_time, service_time)
        queue = []
        cur_start = None
        cur_svc = None
        cur_arr = None
        # accumulators for this seed (window only)
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_busy = 0.0
        w_sys = 0.0
        w_wait = 0.0
        w_waiters = 0.0
        w_n = 0.0
        w_wait_n = 0.0
        last_t = 0.0
        # integrate from warm to H
        # we track state at time t; integrate area between events
        # We'll process events in time order.
        # To integrate only window, we integrate piecewise.
        # state variables: n (in system), busy
        # We'll integrate area of n and busy over [warm,H]
        # Use a helper to advance time to t_next, integrating.
        def integrate(t_from, t_to):
            nonlocal w_busy, w_sys, w_waiters
            if t_to <= t_from:
                return
            lo = max(t_from, warm)
            hi = min(t_to, H)
            if hi <= lo:
                return
            dt = hi - lo
            w_busy += dt * (1.0 if busy else 0.0)
            w_sys += dt * n
            w_waiters += dt * max(0, n - (1 if busy else 0))

        # We'll simulate with event times: next arrival t_arr, next departure next_dep
        # But service times drawn at arrival.
        # We need to handle queue.
        # Let's restructure: maintain queue of (arr_time, svc_time)
        # When server free and queue nonempty, start service.
        # We'll process events: arrival or departure.
        # At each event, integrate up to event time, then update state.
        # We'll also need to handle warm start: we simulate from 0, but only accumulate after warm.
        # For simplicity, we simulate full [0,H], but only accumulate in window.
        # We'll track n, busy, queue.
        # At arrival: n+=1; if not busy: start service immediately (busy=True, next_dep = t + svc)
        # else: queue.append((t, svc))
        # At departure: n-=1; busy=False; if queue: pop, start service (busy=True, next_dep = t + svc)
        # We need to draw service time at arrival.
        # We'll generate arrivals on the fly.
        # We'll also need to handle the case where t_arr > H: we can stop generating arrivals after H.
        # But we still need to process departures until H? Actually we only care up to H.
        # We'll simulate until t >= H and no more events before H.
        # We'll integrate up to H at the end.
        # Let's implement.

        # Initialize: t=0, n=0, busy=False, next_dep=inf, t_arr = exp(lam)
        # We'll loop while t < H or next_dep < H or t_arr < H
        # Actually we need to process events in order.
        # We'll use a while loop: while True:
        #   t_next = min(t_arr, next_dep)
        #   if t_next > H: break
        #   integrate(t, t_next)
        #   t = t_next
        #   if t_arr <= next_dep: # arrival
        #       # process arrival at t
        #       # draw service time
        #       svc = draw_service(rng)
        #       n += 1
        #       if not busy:
        #           busy = True
        #           next_dep = t + svc
        #       else:
        #           queue.append((t, svc))
        #       # schedule next arrival
        #       t_arr = t + rng.expovariate(lam)
        #   else: # departure
        #       n -= 1
        #       busy = False
        #       if queue:
        #           arr_t, svc = queue.pop(0)
        #           busy = True
        #           next_dep = t + svc
        #       else:
        #           next_dep = float('inf')
        #   # accumulate stats if t in window? We'll accumulate at end using areas.
        #   # For counts, we need to count arrivals/departures/blocks in window.
        #   # We'll count when event occurs and t >= warm and t <= H.
        #   if t >= warm and t <= H:
        #       if arrival: w_arr += 1
        #       else: w_dep += 1
        #   # blocking: if arrival and busy and queue length >= capacity? No capacity given, infinite queue. So no blocking.
        #   # p_loss = 0 always.
        #   # p_wait: fraction of arrivals that wait (i.e., busy at arrival). We'll count.
        #   # We'll track waiters: if arrival and busy: w_wait_n += 1
        #   # Also for W: sum of waiting times? We can compute W from L and lambda_eff? Or directly.
        #   # We'll compute W as average time in system for departures in window? Or use Little's law.
        #   # Better: compute W directly from waiting times of customers who depart in window? But we need per-seed W.
        #   # We can accumulate total time in system for customers who arrive in window? Or depart in window?
        #   # Standard: W = average time in system for customers who complete service in window.
        #   # We'll track for each customer: arrival time, service start time, departure time.
        #   # We'll accumulate sum of (departure - arrival) for departures in window.
        #   # Also sum of waiting time (start - arrival) for those.
        #   # We'll need to store arrival time with each customer.
        #   # We already have queue of (arr_time, svc). For current service, we need cur_arr.
        #   # Let's add cur_arr variable.
        #   # When starting service, set cur_arr = arr_time.
        #   # At departure, if t in window: w_dep += 1; w_sys_time += t - cur_arr; w_wait_time += (start - cur_arr)? We need start time.
        #   # We can store start time as well.
        #   # Let's restructure with cur_start.
        #   # This is getting long. Let's simplify: we'll compute W from L and lambda_eff using Little's law? But we need per-seed W.
        #   # We can compute W = L / lambda_eff, where lambda_eff = dep_rate. But that's derived.
        #   # The problem asks for per_seed_W. We can compute W directly by accumulating time in system for departures in window.
        #   # We'll do that.

        # Let's rewrite cleanly with variables:
        # t, n, busy, next_dep, t_arr, queue (list of (arr, svc)), cur_arr, cur_start
        # We'll also need to integrate areas.
        # We'll accumulate:
        # w_arr, w_dep, w_blk (0), w_busy_area, w_sys_area, w_waiters_area
        # w_sum_sys_time, w_sum_wait_time for departures in window
        # w_wait_count for arrivals in window that wait
        # w_arr_count for arrivals in window
        # We'll compute per-seed:
        # L = w_sys_area / win_len
        # W = w_sum_sys_time / w_dep (if w_dep>0 else 0)
        # busy_frac = w_busy_area / win_len
        # p_loss = w_blk / w_arr (if w_arr>0 else 0)
        # p_wait = w_wait_count / w_arr (if w_arr>0 else 0)
        # But note: W from departures in window may be biased. Alternatively, use L = lambda_eff * W, but we need W.
        # We'll use the direct method.

        # Let's implement.

        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        t_arr = rng.expovariate(lam)
        queue = []
        cur_arr = None
        cur_start = None
        w_arr = 0
        w_dep = 0
        w_blk = 0
        w_busy_area = 0.0
        w_sys_area = 0.0
        w_waiters_area = 0.0
        w_sum_sys_time = 0.0
        w_sum_wait_time = 0.0
        w_wait_count = 0
        w_arr_count = 0
        win_len = H - warm

        def draw_svc():
            if rng.random() < p1:
                return rng.expovariate(r1)
            else:
                return rng.expovariate(r2)

        while True:
            t_next = min(t_arr, next_dep)
            if t_next > H:
                break
            # integrate from t to t_next
            lo = max(t, warm)
            hi = min(t_next, H)
            if hi > lo:
                dt = hi - lo
                w_busy_area += dt * (1.0 if busy else 0.0)
                w_sys_area += dt * n
                w_waiters_area += dt * max(0, n - (1 if busy else 0))
            t = t_next
            if t_arr <= next_dep:
                # arrival
                svc = draw_svc()
                n += 1
                if t >= warm and t <= H:
                    w_arr += 1
                    w_arr_count += 1
                if not busy:
                    busy = True
                    cur_arr = t
                    cur_start = t
                    next_dep = t + svc
                else:
                    queue.append((t, svc))
                    if t >= warm and t <= H:
                        w_wait_count += 1
                t_arr = t + rng.expovariate(lam)
            else:
                # departure
                n -= 1
                if t >= warm and t <= H:
                    w_dep += 1
                    w_sum_sys_time += t - cur_arr
                    w_sum_wait_time += cur_start - cur_arr
                busy = False
                if queue:
                    arr_t, svc = queue.pop(0)
                    busy = True
                    cur_arr = arr_t
                    cur_start = t
                    next_dep = t + svc
                else:
                    next_dep = float('inf')
                    cur_arr = None
                    cur_start = None

        # after loop, integrate to H if needed
        if t < H:
            lo = max(t, warm)
            hi = H
            if hi > lo:
                dt = hi - lo
                w_busy_area += dt * (1.0 if busy else 0.0)
                w_sys_area += dt * n
                w_waiters_area += dt * max(0, n - (1 if busy else 0))

        # compute per-seed stats
        L_seed = w_sys_area / win_len if win_len > 0 else 0.0
        W_seed = w_sum_sys_time / w_dep if w_dep > 0 else 0.0
        bf_seed = w_busy_area / win_len if win_len > 0 else 0.0
        pl_seed = w_blk / w_arr if w_arr > 0 else 0.0
        pw_seed = w_wait_count / w_arr if w_arr > 0 else 0.0

        per_L.append(L_seed)
        per_W.append(W_seed)
        per_bf.append(bf_seed)
        per_pl.append(pl_seed)
        per_pw.append(pw_seed)

        tot_arr += w_arr
        tot_dep += w_dep
        tot_blk += w_blk
        tot_busy_area += w_busy_area
        tot_sys_area += w_sys_area
        tot_wait_area += w_sum_wait_time
        tot_waiters_area += w_waiters_area
        tot_n += w_arr_count
        tot_wait_n += w_wait_count
        win_total += win_len

    nseeds = len(seeds)
    L = sum(per_L) / nseeds if nseeds > 0 else 0.0
    W = sum(per_W) / nseeds if nseeds > 0 else 0.0
    busy_frac = sum(per_bf) / nseeds if nseeds > 0 else 0.0
    p_loss = sum(per_pl) / nseeds if nseeds > 0 else 0.0
    p_wait = sum(per_pw) / nseeds if nseeds > 0 else 0.0

    arr = tot_arr / nseeds if nseeds > 0 else 0.0
    dep = tot_dep / nseeds if nseeds > 0 else 0.0
    blk = tot_blk / nseeds if nseeds > 0 else 0.0
    win = win_total / nseeds if nseeds > 0 else 0.0
    dep_rate = (tot_dep / win_total) if win_total > 0 else 0.0
    lam_eff = dep_rate
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": nseeds,
        "time_unit": "minute",
        "win": win,
        "arr": arr,
        "blk": blk,
        "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "dep": dep,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
