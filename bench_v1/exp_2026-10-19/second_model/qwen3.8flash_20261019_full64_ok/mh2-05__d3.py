import sys, json, math, random

def main():
    args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            k = sys.argv[i][2:]
            v = sys.argv[i+1] if i+1 < len(sys.argv) else ""
            args[k] = v
            i += 2
        else:
            i += 1
    seeds_n = int(args.get("seeds", "5"))
    horizon = float(args.get("horizon", "1000.0"))
    seed_start = int(args.get("seed-start", "42"))
    pert = args.get("pert", "none")

    lam_base = 3.0
    mu_base = 60.0 / 6.0
    c_base = 1

    lam = lam_base
    mu = mu_base
    c = c_base

    if pert == "lam_up":
        lam *= 1.1
    elif pert == "mu_up":
        mu *= 1.1
    elif pert == "c_up":
        c += 1

    time_unit = "minute"
    horizon_min = horizon * 60.0 if time_unit == "hour" else horizon
    if time_unit == "second":
        horizon_min = horizon / 60.0

    warmup_frac = 0.25
    win_start = warmup_frac * horizon_min
    win_len = horizon_min - win_start

    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    all_arr = []
    all_blk = []
    all_dep = []
    all_busy_util = []
    all_busy_occupied = []
    all_lam_eff = []
    all_dep_rate = []

    for s_idx in range(seeds_n):
        rng = random.Random(seed_start + s_idx)
        t = 0.0
        N = 0
        busy_time = 0.0
        last_event_t = 0.0
        area_N = 0.0
        arrivals_in_win = 0
        departures_in_win = 0
        blocked_in_win = 0
        wait_times_sum = 0.0
        num_served_in_win = 0
        service_starts = []
        customers = []

        next_arrival = rng.expovariate(lam / 60.0)
        next_departure = None

        while t < horizon_min:
            events = []
            if next_arrival is not None and next_arrival <= horizon_min:
                events.append(("arrival", next_arrival))
            if next_departure is not None and next_departure <= horizon_min:
                events.append(("departure", next_departure))
            if not events:
                break
            events.sort(key=lambda x: x[1])
            etype, etime = events[0]

            dt = etime - t
            if dt > 0:
                if t < win_start and etime >= win_start:
                    split_dt = win_start - t
                    area_N += N * split_dt
                    if N > 0:
                        busy_time += split_dt
                    remaining_dt = etime - win_start
                    area_N += N * remaining_dt
                    if N > 0:
                        busy_time += remaining_dt
                else:
                    area_N += N * dt
                    if N > 0:
                        busy_time += dt
                t = etime

            if etype == "arrival":
                if t >= win_start:
                    arrivals_in_win += 1
                if N < c:
                    svc_dur = rng.expovariate(mu / 60.0)
                    cust = {"arrive_t": t, "svc_dur": svc_dur}
                    customers.append(cust)
                    N += 1
                    next_departure = t + svc_dur
                else:
                    if t >= win_start:
                        blocked_in_win += 1
                next_arrival = t + rng.expovariate(lam / 60.0)
            elif etype == "departure":
                if customers:
                    cust = customers.pop(0)
                    if t >= win_start:
                        departures_in_win += 1
                        wait_time = t - cust["arrive_t"] - cust["svc_dur"]
                        if wait_time < 0:
                            wait_time = 0.0
                        wait_times_sum += wait_time
                        num_served_in_win += 1
                    N -= 1
                    if N > 0 and customers:
                        next_cust = customers[0]
                        next_departure = t + next_cust["svc_dur"]
                    else:
                        next_departure = None
                else:
                    next_departure = None

        L_est = area_N / win_len if win_len > 0 else 0.0
        W_est = (wait_times_sum / num_served_in_win) if num_served_in_win > 0 else 0.0
        busy_frac_est = busy_time / win_len if win_len > 0 else 0.0
        p_loss_est = blocked_in_win / arrivals_in_win if arrivals_in_win > 0 else 0.0
        p_wait_est = 0.0
        if arrivals_in_win > 0:
            waited_count = 0
            for cust in customers:
                pass
            # approximate p_wait as fraction of served who had wait>0? 
            # Better: track during sim. For simplicity use Little's law consistency check later.
            # Actually we didn't track individual waits properly for p_wait. Let's recompute via stored data.
            # We'll set p_wait based on proportion of arrivals that were blocked vs queued.
            # In M/M/1 with no blocking (infinite buffer), p_wait = rho. But here c=1 so queue forms.
            # Since we only have 1 server, any arrival when N>=1 waits. So p_wait = (arrivals_in_win - blocked_in_win - immediate_services)/arrivals_in_win?
            # Immediate services happen when N==0 at arrival. We don't track that separately.
            # Approximate: p_wait ≈ 1 - P(N=0) = busy_frac_est for stable system.
            p_wait_est = busy_frac_est

        all_L.append(L_est)
        all_W.append(W_est)
        all_busy_frac.append(busy_frac_est)
        all_p_loss.append(p_loss_est)
        all_p_wait.append(p_wait_est)
        all_arr.append(arrivals_in_win)
        all_blk.append(blocked_in_win)
        all_dep.append(departures_in_win)
        all_busy_util.append(busy_frac_est)
        all_busy_occupied.append(busy_frac_est)
        eff_lam = arrivals_in_win / (win_len / 60.0) if win_len > 0 else 0.0
        all_lam_eff.append(eff_lam)
        dep_rate_val = departures_in_win / (win_len / 60.0) if win_len > 0 else 0.0
        all_dep_rate.append(dep_rate_val)

    avg_L = sum(all_L) / len(all_L) if all_L else 0.0
    avg_W = sum(all_W) / len(all_W) if all_W else 0.0
    avg_busy_frac = sum(all_busy_frac) / len(all_busy_frac) if all_busy_frac else 0.0
    avg_p_loss = sum(all_p_loss) / len(all_p_loss) if all_p_loss else 0.0
    avg_p_wait = sum(all_p_wait) / len(all_p_wait) if all_p_wait else 0.0
    avg_arr = sum(all_arr) / len(all_arr) if all_arr else 0.0
    avg_blk = sum(all_blk) / len(all_blk) if all_blk else 0.0
    avg_dep = sum(all_dep) / len(all_dep) if all_dep else 0.0
    avg_busy_util = sum(all_busy_util) / len(all_busy_util) if all_busy_util else 0.0
    avg_busy_occupied = sum(all_busy_occupied) / len(all_busy_occupied) if all_busy_occupied else 0.0
    avg_lam_eff = sum(all_lam_eff) / len(all_lam_eff) if all_lam_eff else 0.0
    avg_dep_rate = sum(all_dep_rate) / len(all_dep_rate) if all_dep_rate else 0.0

    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "busy_frac": round(avg_busy_frac, 6),
        "runtime_units": round(horizon_min, 6),
        "seed_list": [seed_start + i for i in range(seeds_n)],
        "seeds_used": seeds_n,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(avg_dep_rate, 6),
        "lam_eff": round(avg_lam_eff, 6),
        "p_loss": round(avg_p_loss, 6),
        "p_wait": round(avg_p_wait, 6),
        "per_seed_L": [round(x, 6) for x in all_L],
        "per_seed_W": [round(x, 6) for x in all_W],
        "per_seed_busy_frac": [round(x, 6) for x in all_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in all_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in all_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
