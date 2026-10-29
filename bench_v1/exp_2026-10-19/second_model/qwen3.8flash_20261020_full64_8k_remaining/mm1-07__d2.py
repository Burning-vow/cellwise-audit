import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base, c_base = 8.0, 10.0, 1
    if a.pert == "lam_up": lam_base *= 1.2
    elif a.pert == "mu_up": mu_base *= 1.2
    elif a.pert == "c_up": c_base += 1
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0, 0, 0
    win = a.horizon
    warmup = 0.25 * win
    time_unit = "hour"
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0; N = 0; arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        wait_area = 0.0; busy_area = 0.0; loss_area = 0.0; wait_time_sum = 0.0
        last_event_t = 0.0; prev_N = 0; prev_busy = 0; prev_loss = 0; prev_wait = 0
        next_arr = rng.expovariate(lam_base)
        service_times = {}
        while t < win:
            dt = min(next_arr - t, float('inf'))
            if N > 0 and service_times:
                min_serv_end = min(service_times.values())
                dt = min(dt, min_serv_end - t)
            if dt <= 0 or t >= win: break
            area_dt = dt
            if t + area_dt > warmup:
                eff_dt = max(0.0, (t + area_dt) - warmup)
                if t < warmup:
                    eff_dt = area_dt - (warmup - t)
                else:
                    eff_dt = area_dt
                if eff_dt > 0:
                    wait_area += prev_wait * eff_dt
                    busy_area += prev_busy * eff_dt
                    loss_area += prev_loss * eff_dt
            t += area_dt
            if abs(t - next_arr) < 1e-9:
                arr_cnt += 1
                serv = rng.expovariate(mu_base)
                if N < c_base:
                    N += 1
                    service_times[arr_cnt] = t + serv
                    if N == 1:
                        prev_busy = 1
                else:
                    blk_cnt += 1
                    prev_loss = 1
                next_arr = t + rng.expovariate(lam_base)
            else:
                completed = [k for k,v in service_times.items() if v <= t + 1e-9]
                for k in completed:
                    del service_times[k]
                    dep_cnt += 1
                    N -= 1
                    if N == 0:
                        prev_busy = 0
            prev_N = N
            prev_wait = 1 if N > 0 and len([v for v in service_times.values() if v > t]) < N else 0
            # recompute prev_wait properly: customers waiting are those not yet served but arrived
            # Actually simpler: track queue length separately? Let's use: waiting = N - number currently in service
            # In M/M/1 with c=1, at most 1 in service. So waiting = max(0, N-1) when c=1.
            # For general c: waiting = max(0, N - c)
            prev_wait = max(0, N - c_base)
            prev_busy = 1 if N > 0 else 0
            prev_loss = 1 if blk_cnt > dep_cnt + arr_cnt - N else 0  # this is wrong, let me fix
            # prev_loss should be 1 only during the instant of a loss event, but we integrate over time
            # Better: track loss as an indicator that resets after each event
            # Actually for area integration, we need state between events. Loss happens at arrival instants only.
            # So prev_loss should be 0 except right after a loss event until next event. But since loss is instantaneous,
            # its contribution to time-average is zero unless we model it differently.
            # The problem asks for p_loss which is fraction of arrivals lost, not time-based.
            # Let me reconsider: p_wait is probability an arriving customer waits, p_loss is probability an arriving customer is blocked.
            # These are arrival-weighted, not time-weighted. So I should accumulate them at arrival times.
            pass
        # Redo with cleaner logic
        rng = random.Random(s)
        t = 0.0; N = 0; arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        wait_count_at_arr = 0; loss_count_at_arr = 0
        busy_time = 0.0; total_service_time = 0.0
        next_arr = rng.expovariate(lam_base)
        events = []
        # Simpler approach: discrete event simulation with proper bookkeeping
        # Reset and do it properly
        rng = random.Random(s)
        t = 0.0; N = 0; arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        wait_at_arr = 0; loss_at_arr = 0
        busy_dur = 0.0; last_busy_start = None
        next_arr = rng.expovariate(lam_base)
        serv_end = None
        while t < win:
            if next_arr < (serv_end if serv_end else float('inf')):
                t_new = next_arr
            else:
                t_new = serv_end
            if t_new >= win: break
            dt = t_new - t
            if last_busy_start is not None:
                busy_dur += dt
            t = t_new
            if t == next_arr:
                arr_cnt += 1
                serv = rng.expovariate(mu_base)
                if N < c_base:
                    N += 1
                    if N == 1:
                        last_busy_start = t
                        serv_end = t + serv
                    else:
                        # someone already in service, new one joins queue
                        pass
                    if N > c_base:
                        wait_at_arr += 1
                else:
                    blk_cnt += 1
                    loss_at_arr += 1
                next_arr = t + rng.expovariate(lam_base)
            else:
                dep_cnt += 1
                N -= 1
                if N == 0:
                    last_busy_start = None
                    serv_end = None
                else:
                    # start serving next customer
                    serv = rng.expovariate(mu_base)
                    serv_end = t + serv
                    if N == 1:
                        last_busy_start = t
        L_est = busy_dur / win if win > 0 else 0
        W_est = (busy_dur / dep_cnt) if dep_cnt > 0 else 0
        bf_est = busy_dur / win if win > 0 else 0
        pl_est = loss_at_arr / arr_cnt if arr_cnt > 0 else 0
        pw_est = wait_at_arr / arr_cnt if arr_cnt > 0 else 0
        per_seed_L.append(L_est); per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est); per_seed_p_loss.append(pl_est); per_seed_p_wait.append(pw_est)
        total_arr += arr_cnt; total_dep += dep_cnt; total_blk += blk_cnt
    avg_L = sum(per_seed_L)/len(per_seed_L) if per_seed_L else 0
    avg_W = sum(per_seed_W)/len(per_seed_W) if per_seed_W else 0
    avg_bf = sum(per_seed_busy_frac)/len(per_seed_busy_frac) if per_seed_busy_frac else 0
    avg_pl = sum(per_seed_p_loss)/len(per_seed_p_loss) if per_seed_p_loss else 0
    avg_pw = sum(per_seed_p_wait)/len(per_seed_p_wait) if per_seed_p_wait else 0
    dep_rate = total_dep / (win * seeds_used) * 60 if win > 0 else 0  # convert hour to minute? No, keep consistent
    # dep_rate in per hour: total_dep / (total_time_in_hours)
    total_time_hours = win * seeds_used
    dep_rate_per_hour = total_dep / total_time_hours if total_time_hours > 0 else 0
    lam_eff = dep_rate_per_hour
    result = {
        "L": round(avg_L, 6), "W": round(avg_W, 6), "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6), "runtime_units": "simulation", "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": time_unit, "win": win,
        "arr": round(total_arr/seeds_used, 6), "blk": round(total_blk/seeds_used, 6),
        "busy_util": round(avg_bf, 6), "dep": round(total_dep/seeds_used, 6),
        "dep_rate": round(dep_rate_per_hour, 6), "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6), "per_seed_L": [round(x,6) for x in per_seed_L],
        "per_seed_W": [round(x,6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x,6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x,6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x,6) for x in per_seed_p_wait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
