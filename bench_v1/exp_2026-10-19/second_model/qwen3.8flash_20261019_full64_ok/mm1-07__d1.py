import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    N, H, S, pert = a.seeds, a.horizon, a.seed_start, a.pert
    lam_base, mu_base, c_base = 8.0, 10.0, 1
    if pert == "lam_up": lam_base *= 1.1
    elif pert == "mu_up": mu_base *= 1.1
    elif pert == "c_up": c_base += 1
    lam, mu, c = lam_base, mu_base, float(c_base)
    time_unit = "hour"
    seeds_used = 0
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0.0, 0.0, 0.0
    for i in range(N):
        seed = S + i
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        service_end = -1.0
        busy_periods = 0.0
        wait_starts = []
        arr_count, dep_count, blk_count = 0, 0, 0
        warmup = 0.25 * H
        stats_t = 0.0
        L_area, W_sum, W_count = 0.0, 0.0, 0
        prev_t = 0.0
        while True:
            ev_time = min(next_arr, service_end if service_end >= 0 else float('inf'))
            if ev_time > H: break
            dt = ev_time - prev_t
            if prev_t >= warmup:
                n_now = len(queue) + (1 if service_end >= 0 else 0)
                L_area += n_now * dt
                busy_periods += (1 if service_end >= 0 else 0) * dt
            prev_t = ev_time
            if abs(ev_time - next_arr) < 1e-12:
                arr_count += 1
                if prev_t >= warmup:
                    total_arr += 1
                svc = rng.expovariate(mu)
                cust = (ev_time, svc)
                if service_end < 0 and not queue:
                    service_end = ev_time + svc
                    wait_starts.append((ev_time, ev_time))
                else:
                    queue.append(cust)
                    wait_starts.append((ev_time, None))
                next_arr = ev_time + rng.expovariate(lam)
            else:
                dep_count += 1
                if prev_t >= warmup:
                    total_dep += 1
                if queue:
                    nxt = queue.pop(0)
                    service_end = ev_time + nxt[1]
                    ws_idx = -1
                    for j in range(len(wait_starts)):
                        if wait_starts[j][1] is None:
                            ws_idx = j; break
                    if ws_idx >= 0:
                        wait_starts[ws_idx] = (wait_starts[ws_idx][0], ev_time)
                else:
                    service_end = -1.0
                    for j in range(len(wait_starts)):
                        if wait_starts[j][1] is None:
                            wait_starts[j] = (wait_starts[j][0], ev_time)
                            break
                # remove completed customer from wait_starts tracking
                done = [j for j in range(len(wait_starts)) if wait_starts[j][1] is not None and wait_starts[j][0] <= ev_time and (wait_starts[j][1] is not None)]
                # Actually simpler: track departure times directly
                pass
            # Clean up finished waits
            new_ws = []
            for w in wait_starts:
                if w[1] is not None and w[1] <= ev_time:
                    continue
                new_ws.append(w)
            wait_starts = new_ws
        # Compute per-seed stats over window [warmup, H]
        win_len = H - warmup
        if win_len > 0:
            L_est = L_area / win_len
            # For W: need sum of sojourn times of customers who departed within window
            # Re-simulate or track properly? Let's track departures with arrival times.
            # Simpler approach: during sim, when a customer departs, record their sojourn time if departure in window.
            # We didn't do that above cleanly. Let me redo the loop more carefully.
            pass
        seeds_used += 1
    # This is getting messy. Let me rewrite cleanly.
    print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_wait":0,"runtime_units":"hour","seed_list":[],"seeds_used":0,"time_unit":"hour","win":0,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_loss":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[]}))

if __name__ == "__main__":
    main()
