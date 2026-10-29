import random, json, math, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--horizon', type=float, default=1000.0)
    parser.add_argument('--seed-start', type=int, default=1)
    parser.add_argument('--pert', type=str, default='none')
    args = parser.parse_args()

    lam_base = 6.0 / 60.0  # per minute
    mu_base = 1.0 / 6.0    # per minute
    c = 1

    if args.pert == 'lam_up':
        lam = lam_base * 1.2
    elif args.pert == 'mu_up':
        mu = mu_base * 1.2
    elif args.pert == 'c_up':
        c = 2
        lam = lam_base
        mu = mu_base
    else:
        lam = lam_base
        mu = mu_base

    time_unit = "minute"
    horizon = args.horizon
    warmup_frac = 0.25
    win_start = horizon * warmup_frac
    win_len = horizon - win_start

    seeds_used = args.seeds
    seed_list = [args.seed_start + i for i in range(seeds_used)]

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_p_loss = []
    all_dep_rate = []

    for s_idx, seed in enumerate(seed_list):
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_times = {}
        arrival_times = {}
        busy_until = 0.0
        num_in_system = 0
        prev_t = 0.0
        area_L = 0.0
        total_wait_time = 0.0
        n_arrivals = 0
        n_departures = 0
        n_blocked = 0
        sum_service_completed = 0.0
        max_queue_size = 0

        while t < horizon:
            if not queue and t >= busy_until:
                if next_arr <= horizon:
                    t = next_arr
                    arr_time = t
                    svc = rng.expovariate(mu)
                    queue.append(arr_time)
                    service_times[arr_time] = svc
                    arrival_times[arr_time] = arr_time
                    n_arrivals += 1
                    if len(queue) > max_queue_size:
                        max_queue_size = len(queue)
                    num_in_system = len(queue)
                    area_L += (t - prev_t) * num_in_system
                    prev_t = t
                    busy_until = t + svc
                    next_arr = t + rng.expovariate(lam)
                else:
                    break
            else:
                if queue:
                    first_arr = queue[0]
                    svc = service_times[first_arr]
                    dep_time = busy_until
                    if dep_time <= horizon:
                        t = dep_time
                        if t >= win_start:
                            total_wait_time += (dep_time - arrival_times[first_arr])
                        queue.pop(0)
                        del service_times[first_arr]
                        del arrival_times[first_arr]
                        n_departures += 1
                        num_in_system = len(queue)
                        area_L += (t - prev_t) * num_in_system
                        prev_t = t
                        if queue:
                            next_svc = service_times[queue[0]]
                            busy_until = t + next_svc
                        else:
                            busy_until = 0.0
                    else:
                        break
                else:
                    if next_arr <= horizon:
                        t = next_arr
                        arr_time = t
                        svc = rng.expovariate(mu)
                        queue.append(arr_time)
                        service_times[arr_time] = svc
                        arrival_times[arr_time] = arr_time
                        n_arrivals += 1
                        if len(queue) > max_queue_size:
                            max_queue_size = len(queue)
                        num_in_system = len(queue)
                        area_L += (t - prev_t) * num_in_system
                        prev_t = t
                        busy_until = t + svc
                        next_arr = t + rng.expovariate(lam)
                    else:
                        break

        if prev_t < horizon:
            area_L += (horizon - prev_t) * num_in_system

        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = total_wait_time / n_departures if n_departures > 0 else 0.0
        busy_frac_est = min(1.0, L_est) if c == 1 else 0.0
        p_wait_est = 0.0
        if n_arrivals > 0:
            wait_count = 0
            # approximate p_wait by checking if any customer had to wait
            # but we didn't track that directly; use Little's law relation or simulate differently
            # For M/M/1, P(wait) = rho. Let's compute rho from effective lambda
            pass
        # Recompute p_wait properly: fraction of arrivals who waited
        # We need to track waiting status at arrival
        # Redo simulation with proper tracking? Too complex. Use theoretical approximation for now.
        # Actually, let's re-simulate with proper tracking in a cleaner way.

        # Clean re-simulation for this seed
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        svc_dict = {}
        arr_dict = {}
        busy_until = 0.0
        num_in_sys = 0
        prev_t = 0.0
        area_L = 0.0
        total_wt = 0.0
        n_arr = 0
        n_dep = 0
        n_blk = 0
        n_waited = 0

        while t < horizon:
            events = []
            if next_arr <= horizon:
                events.append(('arr', next_arr))
            if queue and busy_until <= horizon:
                events.append(('dep', busy_until))
            if not events:
                break
            ev_type, ev_time = min(events, key=lambda x: x[1])
            t = ev_time
            if t >= win_start:
                area_L += (t - prev_t) * num_in_sys
            prev_t = t

            if ev_type == 'arr':
                n_arr += 1
                svc = rng.expovariate(mu)
                if len(queue) < 10000:  # no blocking in infinite buffer
                    queue.append(t)
                    svc_dict[t] = svc
                    arr_dict[t] = t
                    if len(queue) > 1:
                        n_waited += 1
                    num_in_sys = len(queue)
                    if num_in_sys == 1:
                        busy_until = t + svc
                else:
                    n_blk += 1
                next_arr = t + rng.expovariate(lam)
            elif ev_type == 'dep':
                if queue:
                    cust_arr = queue.pop(0)
                    if cust_arr in svc_dict:
                        del svc_dict[cust_arr]
                    if cust_arr in arr_dict:
                        del arr_dict[cust_arr]
                    n_dep += 1
                    if t >= win_start:
                        total_wt += (t - cust_arr)
                    num_in_sys = len(queue)
                    if queue:
                        next_cust = queue[0]
                        busy_until = t + svc_dict[next_cust]
                    else:
                        busy_until = float('inf')

        if prev_t < horizon:
            area_L += (horizon - prev_t) * num_in_sys

        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = total_wt / n_dep if n_dep > 0 else 0.0
        busy_frac_est = min(1.0, L_est) if c == 1 else 0.0
        p_wait_est = n_waited / n_arr if n_arr > 0 else 0.0
        p_loss_est = n_blk / n_arr if n_arr > 0 else 0.0
        busy_util_est = min(L_est, c) / c if c > 0 else 0.0
        busy_occ_est = 1.0 - (1.0 - min(1.0, L_est)) if c == 1 else 0.0
        # busy_occupied = 1 - pi0. For M/M/1, pi0 = 1-rho, so 1-pi0=rho=L_est approx
        busy_occ_est = min(1.0, L_est) if c == 1 else 0.0
        lam_eff = n_dep / win_len if win_len > 0 else 0.0
        dep_rate_hr = lam_eff * 60.0

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(n_arr)
        all_blk.append(n_blk)
        all_dep.append(n_dep)
        all_busy_util.append(busy_util_est)
        all_busy_occupied.append(busy_occ_est)
        all_lam_eff.append(lam_eff)
        all_p_loss.append(p_loss_est)
        all_dep_rate.append(dep_rate_hr)

    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0.0
    avg_busy_occ = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0.0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0.0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0.0

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "p_wait": round(avg_p_wait, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
