import random, math, json, sys

def main():
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv), 2):
        if i + 1 < len(argv):
            args[argv[i].lstrip('-')] = argv[i+1]
    N = int(args.get('seeds', '5'))
    H = float(args.get('horizon', '100.0'))
    S = int(args.get('seed-start', '42'))
    pert = args.get('pert', 'none')
    lam = 8.0
    mu = 10.0
    c = 1
    if pert == 'lam_up':
        lam *= 1.2
    elif pert == 'mu_up':
        mu *= 1.2
    elif pert == 'c_up':
        c += 1
    time_unit = 'hour'
    horizon = H
    warmup = 0.25 * horizon
    win_len = horizon - warmup
    seed_list = [S + i for i in range(N)]
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_time_in_sys = 0.0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_n_count = 0
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_arr = rng.expovariate(lam)
        next_dep = None
        service_times = []
        queue = []
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_count = 0
        area_L = 0.0
        area_busy = 0.0
        sum_W = 0.0
        sum_wait = 0.0
        while t < horizon:
            events = []
            if next_arr is not None and next_arr <= horizon:
                events.append(('arr', next_arr))
            if next_dep is not None and next_dep <= horizon:
                events.append(('dep', next_dep))
            if not events:
                break
            ev_type, ev_t = min(events, key=lambda x: x[1])
            dt = ev_t - t
            if t >= warmup:
                area_L += n * dt
                if busy:
                    area_busy += dt
            t = ev_t
            if ev_type == 'arr':
                arr_count += 1
                st = rng.expovariate(mu)
                if n < c:
                    n += 1
                    busy = True
                    next_dep = t + st
                    service_times.append((t, st))
                else:
                    blk_count += 1
                next_arr = t + rng.expovariate(lam)
            elif ev_type == 'dep':
                dep_count += 1
                if service_times:
                    arrival_time, _ = service_times.pop(0)
                    w = t - arrival_time
                    sum_W += w
                    if t > warmup:
                        pass
                n -= 1
                if n > 0:
                    next_dep = t + rng.expovariate(mu)
                    busy = True
                else:
                    busy = False
                    next_dep = None
        if t >= warmup:
            final_dt = horizon - max(t, warmup)
            if final_dt > 0:
                area_L += n * final_dt
                if busy:
                    area_busy += final_dt
        L_est = area_L / win_len if win_len > 0 else 0.0
        W_est = sum_W / dep_count if dep_count > 0 else 0.0
        bf_est = area_busy / win_len if win_len > 0 else 0.0
        pl_est = blk_count / arr_count if arr_count > 0 else 0.0
        pw_est = wait_count / arr_count if arr_count > 0 else 0.0
        per_seed_L.append(L_est)
        per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est)
        per_seed_p_wait.append(pw_est)
        total_arr += arr_count
        total_dep += dep_count
        total_blk += blk_count
        total_time_in_sys += sum_W
        total_busy_time += area_busy
        total_wait_time += sum_W
        total_n_count += n
    avg_L = sum(per_seed_L) / N if N > 0 else 0.0
    avg_W = sum(per_seed_W) / N if N > 0 else 0.0
    avg_bf = sum(per_seed_busy_frac) / N if N > 0 else 0.0
    avg_pl = sum(per_seed_p_loss) / N if N > 0 else 0.0
    avg_pw = sum(per_seed_p_wait) / N if N > 0 else 0.0
    arr_avg = total_arr / N if N > 0 else 0.0
    dep_avg = total_dep / N if N > 0 else 0.0
    blk_avg = total_blk / N if N > 0 else 0.0
    dep_rate = dep_avg / win_len if win_len > 0 else 0.0
    lam_eff = dep_rate
    busy_util = avg_bf
    busy_occupied = avg_bf
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W * 60, 6),
        "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6),
        "runtime_units": time_unit,
        "seed_list": seed_list,
        "seeds_used": N,
        "time_unit": time_unit,
        "win": round(win_len, 6),
        "arr": round(arr_avg, 6),
        "blk": round(blk_avg, 6),
        "busy_util": round(busy_util, 6),
        "dep": round(dep_avg, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x * 60, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait],
        "busy_occupied": round(busy_occupied, 6)
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
