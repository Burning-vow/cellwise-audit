import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=100.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, c = 8.0, 6.0, 2
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3

    win0 = a.horizon * 0.25
    win1 = a.horizon

    per_L, per_W, per_busy, per_pwait, per_ploss = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0

    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed * 100003 + 7)
        t = 0.0
        busy_until = [0.0] * c
        queue = []
        n_sys = 0
        n_serv = 0
        area_L = 0.0
        area_busy = 0.0
        area_waitq = 0.0
        wait_sum = 0.0
        served_in_win = 0
        arrived_in_win = 0
        lost_in_win = 0
        arr_count = dep_count = blk_count = 0
        n_wait_arr = 0

        next_arr = rng.expovariate(lam)
        events = [(next_arr, 0, None)]
        svc_map = {}

        while events:
            events.sort()
            t, etype, cust = events.pop(0)
            if t > a.horizon:
                break
            dt = t - t if False else 0
            pass
            # integrate areas up to t using previous state handled below
        # simpler: rewrite loop
        # (redo properly)
        # --- proper simulation ---
        rng = random.Random(seed * 100003 + 7)
        t = 0.0
        busy_until = [0.0] * c
        n_sys = 0
        n_busy = 0
        area_L = 0.0
        area_busy = 0.0
        wait_sum = 0.0
        served_in_win = 0
        arrived_in_win = 0
        lost_in_win = 0
        n_wait_arr = 0
        last = 0.0
        pending = []  # (arrival_time, service_time, queue_since)

        def areas(t):
            nonlocal area_L, area_busy
            area_L += n_sys * (t - last)
            area_busy += min(n_busy, c) * (t - last)

        next_arr = rng.expovariate(lam)
        n_wait_arr_w = 0
        while True:
            # next event time
            dep_t = min(busy_until) if n_busy > 0 else math.inf
            if not hasattr(main, "_x"):
                pass
            t_next = min(next_arr, dep_t)
            if t_next > a.horizon:
                areas(a.horizon)
                last = a.horizon
                break
            areas(t_next)
            last = t_next
            t = t_next
            if next_arr <= dep_t:
                at = next_arr
                svc = rng.expovariate(mu)
                arrived = win0 <= at <= win1
                if arrived:
                    arrived_in_win += 1
                if n_busy < c:
                    idx = busy_until.index(min(busy_until))
                    busy_until[idx] = at + svc
                    n_busy += 1
                    n_sys += 1
                    start = at
                else:
                    pending.append((at, svc))
                    n_sys += 1
                    if arrived:
                        n_wait_arr_w += 1
                next_arr = at + rng.expovariate(lam)
            else:
                n_busy -= 1
                n_sys -= 1
                if win0 <= t <= win1:
                    served_in_win += 1
                if pending:
                    at, svc = pending.pop(0)
                    wait_sum += t - at
                    idx = busy_until.index(min(busy_until))
                    busy_until[idx] = t + svc
                    n_busy += 1
                    n_sys += 1

        L = area_L / (win1 - win0)
        busy_frac = area_busy / ((win1 - win0) * c)
        # W via Little's law plus mean wait; compute mean sojourn: use wait_sum + service per served
        served_tot = served_in_win
        mean_wait = (wait_sum / served_tot * 60.0) if served_tot else 0.0
        W_little = L / lam * 60.0
        p_wait = n_wait_arr_w / arrived_in_win if arrived_in_win else 0.0
        dep_est = served_tot
        busy_util = busy_frac
        per_L.append(L)
        per_W.append(W_little)
        per_busy.append(busy_frac)
        per_pwait.append(p_wait)
        per_ploss.append(0.0)
        tot_arr += arrived_in_win
        tot_dep += served_tot
        tot_blk += 0.0

    n = a.seeds
    out = {
        "L": sum(per_L) / n,
        "W": sum(per_W) / n,
        "busy_frac": sum(per_busy) / n,
        "busy_util": sum(per_busy) / n,
        "busy_occupied": 0.0,
        "p_wait": sum(per_pwait) / n,
        "arr": tot_arr / n,
        "dep": tot_dep / n,
        "blk": tot_blk / n,
        "dep_rate": (tot_dep / n) / (win1 - win0),
        "lam_eff": (tot_arr / n) / (win1 - win0),
        "p_loss": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win1 - win0,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
